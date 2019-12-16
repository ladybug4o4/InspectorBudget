import json
import os
import requests
from datetime import datetime
from tempfile import NamedTemporaryFile

from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from smb.SMBConnection import SMBConnection

from utils import load_config, year_month_prev

#
# class Synchro2:#(BoxLayout):
#     # txt_dwn = StringProperty('\u21CA Download from Samba')
#     # txt_snd = StringProperty('\u21C8 Send to Samba')
#
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         config = load_config()
#         self.url = config['api_url'] + 'entries/'
#         self.device_path = config['device_path']
#
#     def download(self, months=0):
#         t = 30
#         try:
#             if months == 0:
#                 r = requests.get(self.url, timeout=t)
#                 data = r.json()
#             elif months > 0:
#                 year_month_list = year_month_prev(
#                     datetime.today().year,
#                     datetime.today().month,
#                     months, [])
#                 data = []
#                 for ym in year_month_list:
#                     r = requests.get(self.url + '?year=%s&month=%s' % ym, timeout=t)
#                     data.extend(r.json())
#             else:
#                 print('k should be positive value or 0 (for all data to download')
#                 return 0
#
#             with open('data.json', 'w') as fp:
#                 json.dump(data, fp, indent=2)
#             return data
#         except Exception as e:
#             e = str(e)
#             print(e)
#             print(e[:e.index('(')])
#             # self.txt_dwn = str(e)
#
#
#     def send(self, records):
#         try:
#             ids = []
#             for rec in records:
#                 r = requests.post(self.url, rec)
#                 ids.append(r.json()['id'])
#             return ids
#         except Exception as e:
#             e = str(e)
#             print(e)
#             print(e[:e.index('(')])


class Synchro(BoxLayout):
    txt_dwn = StringProperty('\u21CA Download from Samba')
    txt_snd = StringProperty('\u21C8 Send to Samba')

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

    def download(self, k=0, names=None):
        self.setup()
        isok = self.connect()
        # k=0 -> download all, k>0 -> download k files.
        if self.is_connected():
            try:
                files = self.server.listPath(self.share_name, self.smb_path)
            except:
                self.txt_dwn = 'Bad password :('
                return False
            files = [f.filename for f in files]
            files = [f for f in files if (len(f) == 10 and f[2] == '_')]
            files.sort()
            if k>0:
                files = files[-k:]
            if isinstance(names, type(None)):
                names = files
            nrows = []

            dwn = []
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
                        dwn.append(smb_file_name)
            self.server.close()
            self.txt_dwn = 'Data \n%s\n successfully downloaded (items number: \n%s)' % (dwn, nrows)
        else:
            self.txt_dwn = 'Connection error :('


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
        if len(data_tmp_files) > 0:
            self.download(names=data_txt_files)
            for tmp_file in data_tmp_files:
                tmp_name, ext = tmp_file.split('.')
                target = os.path.join(self.device_path, tmp_name + '.json')
                source = os.path.join(self.device_path, tmp_file)
                n1, n2 = self.concatenate_json(target, source)
                self.txt_snd = 'File %s had %s records, now it has %s.' % (
                    tmp_name, n1, n2
                )
                with open(target, 'rb') as data:
                    try:
                        self.connect()
                        self.server.storeFile(self.share_name,
                                              os.path.join(self.smb_path, tmp_name+'.json'),
                                              data)
                        self.server.close()
                        os.remove(source)
                    except Exception as e:
                        self.txt_snd = 'Connection problem'
        else:
            self.txt_snd = 'Nothing to add.'

    def clear_all(self):
        path = load_config()['device_path']
        for f in os.listdir(path):
            os.remove(os.path.join(path, f))

    @staticmethod
    def is_connected():
        try:
            requests.get('http://' + load_config("router_ip"), timeout=1)
            return True
        except requests.ConnectionError as err:
            return False


if __name__=='__main__':
    print('Synchro')
    s=Synchro()
    print(s.is_connected())