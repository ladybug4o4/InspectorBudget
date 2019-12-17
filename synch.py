import json
import os
import requests
from datetime import datetime
from tempfile import NamedTemporaryFile

from smb.SMBConnection import SMBConnection
from utils import load_config, year_month_prev


class SynchroAPI():

    def __init__(self, **kwargs):
        super(SynchroAPI).__init__(**kwargs)
        config = load_config()
        self.url = config['api_url'] + 'entries/'
        self.device_path = config['device_path']

    def download(self, months=0):
        t = 30
        if months == 0:
            ##TODO: save as separate files
            r = requests.get(self.url, timeout=t)
            data = r.json()['results']
            with open('data/data.json', 'w') as fp:
                json.dump(data, fp, indent=1)
        elif months > 0:
            year_month_list = year_month_prev(
                datetime.today().year,
                datetime.today().month,
                months, [])
            files = {}
            for ym in year_month_list:
                r = requests.get(self.url + '?year=%s&month=%s' % ym, timeout=t)
                r = r.json()['results']
                file_name = '%s_%.2d.json' % (str(ym[0])[-2:], ym[1])
                files[file_name] = len(r)
                with open('data/' + file_name, 'w') as fp:
                    json.dump(r, fp, indent=1)
            return str(list(files.keys())), str(list(files.values()))
        else:
            print('months should be positive value or 0 (for all data to download')
            return 0


    def send(self):
        data_files = os.listdir(self.device_path)
        data_tmp_files = [f for f in data_files if f[-3:] == 'tmp']
        ids = []
        for file in data_tmp_files:
            pth = 'data/' + file
            with open(pth, 'r') as fp:
                records = json.load(fp)
            for rec in records:
                r = requests.post(self.url, rec)
                ids.append(r.json()['id'])
            os.remove(pth)
        txt_snd = 'Nowe wpisy nr: %s' % str(ids)
        return txt_snd


class SynchroRouter():

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup()

    def setup(self):
        config = load_config()
        self.smb_path = config["smb_path"]
        self.device_path = os.path.join(os.getcwd(), config["device_path"])
        self.device_temp_data = os.path.join(os.getcwd(), config["device_path"])
        self.client = config["client"]
        self.ip = config["router_ip"]
        self.username = config["username"]
        self.is_conn = False
        self.password = config["password"]
        self.share_name = config["share_name"]

    def connect(self):
        self.server = SMBConnection(self.username,
                                    self.password, self.client, '',
                                    use_ntlm_v2=True,
                                    is_direct_tcp=True)
        isok = self.server.connect(self.ip, 139)

    def target_path(self, fname):
        return os.path.join(self.device_path, fname)

    def download(self, months=0, names=None):
        self.setup()
        # months=0 -> download all, months>0 -> download months files.
        self.connect()
        files = self.server.listPath(self.share_name, self.smb_path)
        files = [f.filename for f in files]
        files = [f for f in files if (len(f) == 10 and f[2] == '_')]
        files.sort()
        if months>0:
            files = files[-months:]
        if isinstance(names, type(None)):
            names = files
        nrows = []

        dwn_names = []
        for smb_file_name in files:
            if smb_file_name in names:
                with NamedTemporaryFile() as tmp:
                    fname = os.path.join(self.smb_path, smb_file_name)
                    _, filesize = self.server.retrieveFile(self.share_name, fname, tmp)
                    tmp.file.seek(0)
                    smb_file_content = tmp.file.read().decode()
                    with open(self.target_path(smb_file_name), 'w') as f:
                        f.write(smb_file_content)
                        n = sum([ 1 for i in smb_file_content if i == "{"])
                        nrows.append(n)
                    dwn_names.append(smb_file_name)
        self.server.close()
        return dwn_names, nrows


    def concatenate_csv(self, target, source):
        if os.path.exists(target):
            n1 = os.popen('wc -l %s' % target).read().split(' ')[0]
        else:
            n1 = 0
        os.system('cat %s >> %s' % (source, target))
        n2 = os.popen('wc -l %s' % target).read().split(' ')[0]

        with open(target, 'r') as tmp:
            data = tmp.readlines()
        return data, n1, n2

    def concatenate_json(self, target, source):
        if os.path.exists(target):
            with open(target, 'r') as f:
                target_data = json.load(f)
                n1 = len(target_data)
        else:
            target_data = []
            n1 = 0

        with open(source, 'r') as f:
            source_data = json.load(f)

        all_data = target_data + source_data
        with open(target, 'w') as f:
            json.dump(all_data, f, indent=2)
        return n1, len(all_data)

    def send(self):
        self.setup()
        data_files = os.listdir(self.device_path)
        data_tmp_files = [f for f in data_files if f[-3:] == 'tmp']
        data_txt_files = [f.split('.')[0]+'.json' for f in data_tmp_files]

        self.download(names=data_txt_files)
        file_names = []
        N1 = []
        N2 = []
        for tmp_file in data_tmp_files:
            tmp_name, ext = tmp_file.split('.')
            target = os.path.join(self.device_path, tmp_name + '.json')
            source = os.path.join(self.device_path, tmp_file)
            n1, n2 = self.concatenate_json(target, source)
            file_names.append(tmp_file)
            N1.append(n1)
            N2.append(n2)
            txt_snd = 'Plik %s miał %s wpisów, obecnie ma %s.' % (tmp_name, n1, n2)
            with open(target, 'rb') as data:
                    self.connect()
                    self.server.storeFile(self.share_name,
                                          os.path.join(self.smb_path, tmp_name+'.json'),
                                          data)
                    self.server.close()
                    os.remove(source)
        txt_snd = 'Plik(i) %s miał(y) %s wpisów,\nobecnie ma(ją) %s.' % (str(file_names), str(N1), str(N2))
        return txt_snd


if __name__=='__main__':
    print('Synchro')
    # s=Synchro()
    # print(s.is_connected())