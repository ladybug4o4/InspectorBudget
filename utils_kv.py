from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput


class MyTextInput(TextInput):
    def __init__(self, **kwargs):
        super(MyTextInput, self).__init__(**kwargs)
        self.padding_y = (self.height/2. - self.line_height, 0)
        self.halign = 'center'

    def reset(self):
        self.text = ''


class NumPadWidget(BoxLayout):pass


class FloatInput(TextInput):
    # https://stackoverflow.com/questions/36854811/kivy-textinput-on-focus-behavior-issue
    def __init__(self, **kwargs):
        super(FloatInput, self).__init__(**kwargs)
        self.padding_y = (self.height/2. - self.line_height, 0)
        self.halign = 'center'

    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y):

            prompt_content = BoxLayout(orientation='vertical')      # Main layout

            num_pad = NumPadWidget()
            prompt_content.add_widget(num_pad)

            def my_callback(instance):
                self.text = num_pad.ids.num_label.text
                self.popup.dismiss()

            # Now define the popup, with the content being the layout:
            self.popup = Popup()
            self.popup.title =''
            self.popup.separator_height = 0
            self.popup.content=prompt_content
            self.popup.size_hint=(0.85, 0.85)
            self.popup.autodismiss=False
            num_pad.ids.enter_btn.bind(on_press=my_callback)

            # Open the pop-up:
            self.popup.open()

    def reset(self):
        self.text = ''