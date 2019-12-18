import json
from datetime import datetime, date
import os
import requests
from kivy.uix.accordion import Accordion, AccordionItem

from kivy.uix.carousel import Carousel
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.properties import StringProperty, ObjectProperty
from kivy.app import App
from kivy.core.text import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'systemandmulti')

from utils import load_config, year_month_prev, year_month_next, datename
from multiexpressionbutton import MultiExpressionButton
from synch import SynchroRouter, SynchroAPI

from datepicker.datepicker import DatePicker, DATEFORMAT



class Date(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.dp = DatePicker()
        self.today_txt = self.dp.text
        self.tb = ToggleButton(text='Wczoraj', font_size=20)
        self.tb.bind(on_release=self.update)
        self.add_widget(self.dp)
        self.add_widget(self.tb)
        # ## TODO: tb: wczoraj jeśli kalendarz daje dziś i "dziś" jesli kalendarz daje cos innego

    def update(self, *args):
        self.dp.last_text = self.dp.text
        ## TODO zle sie zmienia
        if self.tb.state == 'down':
            self.dp.last_text = self.dp.text
            weekname = datetime.strftime(datetime.strptime(self.dp.yesterday, DATEFORMAT), '%a')
            self.dp.text = weekname + ', ' + self.dp.yesterday
        else:
            self.dp.text = self.dp.last_text

    def reset(self):
        self.tb.state = 'normal'


class Category(Spinner):
    def __init__(self, **kwargs):
        super(Category, self).__init__(**kwargs)
        if not os.path.exists('my_categories.json'):
            os.system('cp categories.json my_categories.json')
        self.refresh()


    def refresh(self):
        with open('my_categories.json', 'r') as f:
            names = json.load(f)
        vals = {v['icon'] + '  ' + k for k, v in names.items()}

        kv_vals = {}
        kv_vals["-"] = [v['icon'] + "  " + k for k, v in names.items() if v['type'] == '-']
        kv_vals["+"] = [v['icon'] + "  " + k for k, v in names.items() if v['type'] == '+']
        self.kv_vals = kv_vals
        self.names = names

    def remove(self, name):
        with open('my_categories.json', 'r') as f:
            names = json.load(f)
        _ = names.pop(name)
        with open('my_categories.json', 'w') as f:
            json.dump(names, f, indent=1)


    def unification(self):
        if type(category) == str:
            icon = Category().names[category]['icon']
        else:
            icon = [ v['icon'] for k,v in Category().names.items() if v['id'] == category]
        icon = '[size=40sp][color=#e9efb1]%s[/color][/size]' % icon[0]


class AccordionItemRow(BoxLayout):
    def __init__(self, kv_val, type, **kwargs):
        super(AccordionItemRow,self).__init__(**kwargs)
        self.orientation = 'horizontal'
        self.kv_name = kv_val.split('  ')[-1]
        self.type = type
        self.add_widget(Label(text=kv_val))
        self.b = Button(text='\u2612', size_hint_x=.15)
        self.b.bind(on_press=self.delete)
        self.add_widget(self.b)

    def delete(self, *args, **kwargs):
        C = Category()
        not_removable = self.parent.parent.parent.parent.parent.parent.parent.parent.parent.parent.children[-1].children[-1].children[0].children[0].children[0].df_categories
        if not self.kv_name in not_removable:
            C.remove(self.kv_name)
            self.parent.parent.parent.parent.parent.reset(self.type, **kwargs)
        else:
            self.b.text = ''


class AccordionContent(AccordionItem, Category):

    def __init__(self, type='-', **kwargs):
        super(AccordionContent, self).__init__(**kwargs)
        self.build(type)

    def reset(self, type):
        self.refresh() # category
        self.remove_widget(self.col)
        self.build(type)

    def build(self, type):
        self.title = type
        self.col = BoxLayout(orientation='vertical')
        for v in self.kv_vals[type]:
            self.col.add_widget(AccordionItemRow(v, type))
        self.add_widget(self.col)


class AccordionEdit(AccordionItem):
    def __init__(self, **kwargs):
        super(AccordionEdit, self).__init__(**kwargs)
        self.title = '\u270D Edytuj kategorie'
        row_new_category = BoxLayout(orientation='vertical')
        row_new_category.add_widget(TextInput(hint_text='Nowa kategoria'))
        row_new_category.add_widget(Icons(size_hint_y=5))
        b2 = BoxLayout(orientation='horizontal')
        b2.add_widget(ToggleButton(id='category_type', group='type', text='-'))
        b2.add_widget(ToggleButton(id='category_type', group='type', text='+'))
        row_new_category.add_widget(b2)
        row_new_category.add_widget(Button(text='Dodaj', on_release=self.save))
        row_new_category.add_widget(Button(text='Wyślij/pobierz do API'))
        row_new_category.add_widget(Label(text=''))
        self.add_widget(row_new_category)

    def get_items(self):
        return self.children[0].children[0].children[0].children[0].children

    def save(self, *args):
        add_items = self.get_items()

        # -1 Logi
        # 0 Pobierz z API
        # 1 Wyślij do API
        # 2 Dodaj
        # 3 BoxLayout -> togglebuttons
        # 4 Icons
        # 5 Nowa kategoria

        # + add_items[2].children[0].state
        # - add_items[2].children[1].state
        tb = add_items[3].children
        type = '-' if tb[1].state == 'down' else '+'
        icon = [i.text for i in add_items[4].children if i.state == 'down']
        category_name = add_items[5].text

        if len(category_name) and len(type) and len(icon):
            icon = icon[0]
            with open('my_categories.json', 'r') as f:
                categories = json.load(f)
            categories[category_name] = {
                'icon': icon,
                'type': type,
                'id': -1
            }
            with open('my_categories.json', 'w') as f:
                json.dump(categories, f)
                add_items[0].text = 'Kategoria "%s  %s" dodana jako "%s".' % (
                    icon, category_name, type)

            plus, minus = self.parent.children[1:]
            plus.reset('+')
            minus.reset('-')
            for t in tb:
                t.state = 'normal'
            add_items[5].text = ''
            for i in add_items[4].children:
                i.state = 'normal'


class Icons(GridLayout):
    def __init__(self, **kwargs):
        super(Icons, self).__init__(**kwargs)
        self.cols = 7
        icons = ['\u271A','\u273F','\u2708','\u2709','\u2638','\u2622','\u2614','\u2615',
                 '\u2604','\u2603','\u2601','\u2600','\u2618','\u2616','\u262D','\u262E','\u2620','\u260E',
                 '\u2663', '\u263B', '\u265A', '\u265B','\u265C','\u265D','\u265E','\u265F','\u25D5','\u25EC',
                 '\u25F1', '\u221E','\u2706', '\u2707', '\u2652', '\u2665', '\u2696', '\u26A1']
        for i in icons:
            self.add_widget(ToggleButton(text=i, group='icons', markup=True))


class CategoryOptions(Popup, Category):
    def __init__(self, **kwargs):
        super(CategoryOptions, self).__init__(**kwargs)
        print(self.kv_vals)

        acc = Accordion()
        acc.orientation = 'vertical'
        incomes = AccordionContent(type='+')
        expenses = AccordionContent(type='-')
        add = AccordionEdit()
        acc.add_widget(expenses)
        acc.add_widget(incomes)
        acc.add_widget(add)
        self.add_widget(acc)

    # def


class Save(MultiExpressionButton):

    def on_release(self):
        print('zapisuje...')

        amount = self.parent.parent.ids.amount.text
        if len(amount):

            category = self.parent.parent.ids.category.text
            note = self.parent.parent.ids.note.text
            day = self.parent.parent.ids.date.dp.text.split(', ')[-1]
            is_salary = 1 if self.parent.parent.ids.plus.state is 'down' else -1

            row = {
                "amount": float(amount)*is_salary,
                "date": day,
                "note": note.replace('\n', '').replace(',', ''),
                "category": Category().names[category.split('  ')[-1]]['id']
            }

            data = Data(filename=datename(day))
            print(row)
            data.save(row)
            self.restart_setup()

    def restart_setup(self):
        self.parent.parent.ids.date.reset()
        self.parent.parent.ids.amount.text = ''
        self.parent.parent.ids.note.text = ''
        self.parent.parent.ids.plus.state = 'normal'
        self.parent.parent.ids.minus.state = 'down'
        self.parent.parent.ids.category.text = self.parent.parent.ids.category.values[0]

    def on_long_press(self):
        pop = CategoryOptions()
        pop.open()


class Undo(MultiExpressionButton):

    def on_long_press(self):
        files = os.listdir(os.path.join(os.getcwd(), load_config()["device_path"]))
        if any([ x.endswith('tmp') for x in files]):
            print('COFAM')
            day = self.parent.parent.ids.date.dp.text.split(',')[1][1:]
            data = Data(filename=datename(day))
            with open(data.tmp_path, 'r') as f:
                lines = json.load(f)
            if len(lines) > 1:
                with open(data.tmp_path, 'w') as f:
                    json.dump(lines[:-1], f)
            else:
                os.remove(data.tmp_path)
            pop = Popup()
            pop.title = 'Komunikat'
            pop.separator_height = 0
            pop.size_hint = (.5, .4)
            pop.content = Button(text = 'Operacja cofnięta')
            pop.content.bind(on_press=pop.dismiss)
            pop.open()
        else:
            pop = Popup()
            pop.title = 'Komunikat'
            pop.separator_height = 0
            pop.size_hint = (.6, .2)
            pop.content = Button(text='Brak nowych wpisów')
            pop.content.bind(on_press=pop.dismiss)
            pop.open()


class NewEntry(BoxLayout):pass


class Item(Label): pass


class Sumup(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = '\u03A3 = %.2f' % TableContent().month_total()

    def update(self):
        self.text = '\u03A3 = %.2f' % self.parent.parent.children[0].mnth_tot


class Month(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.month_i = datetime.today().month
        self.year = datetime.today().year
        self.text = self.month_name(self.month_i)
        self.prev = prev = Button(text='<', on_release=self.prev_month, size_hint_x=.1)
        self.title = title = Label(
            text=self.txt(),
            markup=True,
            valign='middle',
            size_hint_x=.2
        )
        self.next = next = Button(text='>', on_release=self.next_month, size_hint_x=.1)
        self.add_widget(prev)
        self.add_widget(title)
        self.add_widget(next)

    def txt(self):
        return '%02d/%d' % (self.month_i, self.year)

    def prev_month(self, args):
        self.year, self.month_i = year_month_prev(self.year, self.month_i, 2, [])[-1]
        self.update()

    def next_month(self, args):
        self.year, self.month_i = year_month_next(self.year, self.month_i, 2, [])[-1]
        self.update()

    def month_name(self, m):
        return date(1900, m, 1).strftime('%B')

    def update(self):
        self.title.text = self.txt()
        self.parent.parent.parent.ids.table.month = self.month_i
        self.parent.parent.parent.ids.table.year = self.year
        self.parent.parent.parent.ids.table.create()
        self.parent.parent.parent.ids.sum.update()


class Data:
    def __init__(self, filename):
        config = load_config()
        self.txt_path = os.path.join(os.getcwd(),
                                     config["device_path"],
                                     filename+'.json')
        self.tmp_path = os.path.join(os.getcwd(), config["device_path"], filename+'.tmp')
        self.df = []

    def read(self):
        try:
            with open(self.txt_path, 'r') as f:
                df0 = json.load(f)
            df0 = sorted(df0, key=lambda x: x['date'], reverse=True)
        except FileNotFoundError:
            df0 = []

        try:
            with open(self.tmp_path, 'r') as f:
                df = json.load(f)
                df.reverse()
        except FileNotFoundError:
            df = []
        self.df = df + df0
        self.category_unification()

    def save(self, row):
        try:
            with open(self.tmp_path, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = []
        data.append(row)
        with open(self.tmp_path, 'w') as f:
            json.dump(data, f, indent=2)

    def category_unification(self):
        C = Category().names
        for row in self.df:
            if type(row['category']) == int:
                try:
                    tmp = { v['id']: k for k,v in C.items()}
                    name =  tmp[row['category']]
                    row['category'] = name
                except:
                    pass



class Table(BoxLayout):pass


class TableContent(RecycleView):
    def __init__(self, **kwargs):
        super(TableContent, self).__init__(**kwargs)
        self.year = datetime.today().year
        self.month = datetime.today().month
        self.create()

    def clean_data(self, row):
        date, category, note, amount = row['date'], row['category'], row['note'], row['amount']
        date = date.split('-')
        date = date[0] + '/' + date[1]
        if type(category) == str:
            icon = Category().names[category]['icon']
        else:
            icon = [ v['icon'] for k,v in Category().names.items() if v['id'] == category]
        icon = '[size=40sp][color=#e9efb1]%s[/color][/size]' % icon[0] if len(icon) else ''

        i, n = 0, 10
        if not isinstance(note, str):
            note2 = ''
        else:
            note2 = '\n'.join([note[i*n:((i+1)*n)] for i in range((len(note)//n)+1)])
            note2 = '[size=16sp]%s[/size]' % note2
        amount = '[color=#e9efb1]%s[/color]' % amount if float(amount) > 0 else amount
        return [date, icon, note2, amount]

    def month_total(self):
        return sum([float(x['amount']) for x in self.df])

    def create(self):
        data = Data(filename='%d_%.2d' % (self.year%2000, self.month))
        data.read()
        self.df = data.df
        self.df_categories = set([i['category'] for i in data.df])
        all_data = sum([self.clean_data(r) for r in self.df], [])
        self.data =  [{'text': str(r)} for r in all_data]
        self.mnth_tot = self.month_total()


class Synchro(BoxLayout):
    txt_dwn = StringProperty('\u21CA Ściągnij pół roku')
    txt_snd = StringProperty('\u21C8 Wyślij nowe wpisy')

    @staticmethod
    def is_connected():
        try:
            requests.get('http://' + load_config("router_ip"), timeout=1)
            return True
        except requests.ConnectionError as err:
            return False

    def clear_all(self):
        path = load_config()['device_path']
        for f in os.listdir(path):
            os.remove(os.path.join(path, f))

    def download(self, months):
        try:
            if not os.path.exists('my_config.json'):
                self.txt_dwn = 'Ustaw ustawienia'
            else:
                type = load_config('type')
                if type == 'router':
                    s = SynchroRouter()
                    names, nrows = s.download(months)
                    self.txt_dwn = 'Dane %s\nszczęśliwie ściągnięte (liczba wpisów: \n%s)' % \
                               (names, nrows)
                elif type == 'api':
                    s = SynchroAPI()
                    names, nrows = s.download(months)
                    self.txt_dwn = 'Dane %s\nszczęśliwie ściągnięte (liczba wpisów: \n%s)' % \
                               (names, nrows)
                else:
                    self.txt_dwn = 'Ustaw ustawienia.'
        except Exception as e:
            e = str(e)
            print(e)
            self.txt_dwn = 'Problem z połączeniem. Sprawdź ustawienia.'

    def send(self):
        data_files = os.listdir(load_config('device_path'))
        data_tmp_files = [f for f in data_files if f[-3:] == 'tmp']
        if len(data_tmp_files) > 0:
            try:
                if not os.path.exists('my_config.json'):
                    self.txt_dwn = 'Ustaw ustawienia'
                else:
                    type = load_config('type')
                    if type == 'router':
                        s = SynchroRouter()
                        self.txt_snd = s.send()
                    elif type == 'api':
                        s = SynchroAPI()
                        self.txt_snd = s.send()
                    else:
                        self.txt_snd = 'Ustaw ustawienia.'
            except Exception as e:
                e = str(e)
                print(e)
                self.txt_snd = 'Problem z połączeniem.'
        else:
            self.txt_snd = 'Nic nowego.'


class LoginPopup(Popup):
    def __init__(self, caller, **kwargs):
        self.caller = caller
        super(LoginPopup, self).__init__(**kwargs)

    def save(self, type):
        self.caller.type = type
        user = self.ids.user.text
        pswd = self.ids.pswd.text
        path = self.ids.path.text
        ip = self.ids.ip.text
        ip_name = self.ids.ip_name.text
        router_ip = self.ids.router_ip.text
        with open('config.json', 'r') as f:
            config = json.load(f)
        config['router_ip'] = router_ip
        config['smb_path'] = path
        config['username'] = user
        config['password'] = pswd
        config['share_name'] = user
        config['client'] = user
        config['type'] = type
        config['api_url'] = 'http://' + ip + '/' + ip_name + '/'
        with open('my_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        self.dismiss()


class Status(Button):
    txt = StringProperty('Połączenie %s' % ':)' if Synchro.is_connected() else ':(')

    def on_press(self, **kwargs):
        pop = LoginPopup(caller=self)
        pop.open()


class MainWidget(Carousel):

    def update_tab(self):
        if self.children[0].children[0].__class__ == Table().__class__:
            Tab = self.children[0].children[0].__class__
            self.children[0].children[0].clear_widgets()
            self.children[0].children[0].add_widget(Tab())


class InspectorBudgetApp(App):
    col = ObjectProperty({
        'szary': (74/128, 78/128, 77/128, 1),
        'niebieski': (14/256, 154/256, 167/256, 1),
        'morski': (61/256., 164/256., 171/256., 1),
        'zolty': (246/255., 205/255., 97/255., 1),
        'losos': (254/255., 138/255., 113/255., 1),
        'item': (61/255., 164/255., 171/255., .35),
    })

    def build(self):
        data_path = os.path.join(os.getcwd(), load_config()['device_path'])
        if not os.path.exists(data_path):
            os.mkdir(data_path)

        return MainWidget()

if __name__ == '__main__':
    InspectorBudgetApp().run()
