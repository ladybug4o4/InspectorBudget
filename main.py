import json
from datetime import datetime, date
import csv
import os
from kivy.core.window import Window
from kivy.uix.carousel import Carousel
from kivy.uix.popup import Popup

from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.textinput import TextInput
from kivy.uix.recycleview import RecycleView

from datepicker.datepicker import DatePicker
from kivy.app import App
from kivy.core.text import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.togglebutton import ToggleButton

from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'systemandmulti')

from utils import load_config, year_month_prev, year_month_next
from multiexpressionbutton import MultiExpressionButton
from synch import Synchro


class Date(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.dp = DatePicker()
        self.today_txt = self.dp.text
        self.tb = ToggleButton(text='Wczoraj')
        self.tb.bind(on_release=self.update)
        self.add_widget(self.dp)
        self.add_widget(self.tb)
        # ## TODO: tb: wczoraj jeśli kalendarz daje dziś i "dziś" jesli kalendarz daje cos innego

    def update(self, *args):
        self.dp.last_text = self.dp.text
        ## TODO zle sie zmienia
        if self.tb.state == 'down':
            self.dp.last_text = self.dp.text
            weekname = datetime.strftime(datetime.strptime(self.dp.yesterday, '%d.%m.%Y'), '%a')
            self.dp.text = weekname + ', ' + self.dp.yesterday
        else:
            self.dp.text = self.dp.last_text

    def reset(self):
        self.tb.state = 'normal'


class Category(Spinner):
    with open('categories.json', 'r') as f:
        categories = json.load(f)
    vals = {v['icon'] + '  ' + k for k, v in categories.items()}

    kv_vals = {}
    kv_vals["-"] = [v['icon'] + "  " + k for k,v in categories.items() if v['type'] == '-']
    kv_vals["+"] = [v['icon'] + "  " + k for k,v in categories.items() if v['type'] == '+']


class Save(Button):

    def on_release(self):
        print('zapisuje...')

        amount = self.parent.parent.ids.ammount.text
        if len(amount):
            category = self.parent.parent.ids.category.text
            note = self.parent.parent.ids.note.text
            day = self.parent.parent.ids.date.dp.text.split(', ')[-1]
            is_salary = 1 if self.parent.parent.ids.plus.state is 'down' else -1

            row = {
                "amount": float(amount)*is_salary,
                "date": day,
                "note": note.replace('\n', '').replace(',', ''),
                "category": category.split('  ')[-1]
            }

            data = Data(filename='%s_%s' % (day[-2:], day[3:5]))
            print(row)
            data.save(row)
            self.restart_setup()
        else:
            self.text = '"Ale co? :P"'

    def restart_setup(self):
        self.parent.parent.ids.date.reset()
        self.parent.parent.ids.ammount.text = ''
        self.parent.parent.ids.note.text = ''
        self.parent.parent.ids.plus.state = 'normal'
        self.parent.parent.ids.minus.state = 'down'
        self.parent.parent.ids.category.text = self.parent.parent.ids.category.values[0]


class Undo(MultiExpressionButton):

    def on_long_press(self):
        print('COFAM')
        day = self.parent.parent.ids.date.dp.text.split(',')[1][1:]
        data = Data(filename='%s_%s' % (day[-2:], day[3:5]))
        with open(data.tmp_path, 'r') as f:
            lines = json.load(f)
        if len(lines) > 1:
            with open(data.tmp_path, 'w') as f:
                json.dump(lines[:-1], f)
        else:
            os.remove(data.tmp_path)
        pop = Popup()
        pop.title = ''
        pop.separator_height = 0
        pop.size_hint = (.5, .35)
        pop.content = Button(text = 'coflem')
        pop.content.bind(on_press=pop.dismiss)
        pop.open()


class NewEntry(BoxLayout): pass


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
                # df0 = csv.reader(f)
                # df0 = [i for i in df0 if len(i) == 4]
        except FileNotFoundError:
            df0 = []

        try:
            with open(self.tmp_path, 'r') as f:
                df = json.load(f)
                # df = csv.reader(f)
                # df = [i for i in df if len(i) == 4]
        except FileNotFoundError:
            df = []
        df = df + df0
        self.df = self.sort(df)

    def save(self, row):
        try:
            with open(self.tmp_path, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = []
        data.append(row)
        with open(self.tmp_path, 'w') as f:
            json.dump(data, f, indent=2)

        # with open(self.tmp_path, 'a') as f:
        #     f.write(row)


    def sort(self, df):
        # data = [i for i in df if len(i) == 4]
        return sorted(df, key=lambda x: x['date'],  reverse=True)


class Table(BoxLayout):pass


class TableContent(RecycleView):
    def __init__(self, **kwargs):
        super(TableContent, self).__init__(**kwargs)
        self.year = datetime.today().year
        self.month = datetime.today().month
        self.create()

    def clean_data(self, row):
        date, category, note, amount = row['date'], row['category'], row['note'], row['amount']
        # amount, date, note, category = row.values()
        date = date.split('.')
        date = date[0] + '/' + date[1]
        icon = Category.categories[category]['icon']
        icon = '[size=40sp][color=#e9efb1]%s[/color][/size]' % icon

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
        all_data = sum([self.clean_data(r) for r in self.df], [])
        self.data =  [{'text': str(r)} for r in all_data]
        self.mnth_tot = self.month_total()


class Pswrd(BoxLayout):
    secret = StringProperty('')


class Log(Button):
    txt = StringProperty('Connection %s' % ':)' if Synchro.is_connected() else ':(')


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
