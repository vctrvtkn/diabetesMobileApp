import json
import math
import locale
from datetime import datetime
from pathlib import Path

from kivy.metrics import dp, sp
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.utils import get_color_from_hex, platform
from translations import TRANSLATIONS
__version__ = '0.1.3'

def get_device_language():
    """Detect device language, defaulting to English."""
    if platform == 'android':
        try:
            from jnius import autoclass
            Locale = autoclass('java.util.Locale')
            language = str(Locale.getDefault().getLanguage())
        except Exception:
            language = 'en'
    else:
        try:
            language = locale.getlocale()[0] or 'en'
        except (ValueError, TypeError):
            language = 'en'
    return 'ru' if language.lower().startswith('ru') else 'en'

class SwipeScreen(Screen):
    """Горизонтальные свайпы вне полей ввода и прокручиваемых областей."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.on_swipe_left = None
        self.on_swipe_right = None
        self._swipe_start = None
        self._swipe_touch = None

    def _interactive_area(self, x, y):
        for widget in self.walk():
            if isinstance(widget, (TextInput, ScrollView)):
                if widget.collide_point(x, y):
                    return True
        return False

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and not self._interactive_area(*touch.pos):
            self._swipe_start = tuple(touch.pos)
            self._swipe_touch = touch
        else:
            self._swipe_start = None
            self._swipe_touch = None
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        start = self._swipe_start if touch is self._swipe_touch else None
        self._swipe_start = None
        self._swipe_touch = None
        result = super().on_touch_up(touch)
        if start is not None:
            dx = touch.x - start[0]
            dy = touch.y - start[1]
            if abs(dx) >= dp(85) and abs(dx) > abs(dy) * 1.5:
                callback = self.on_swipe_left if dx < 0 else self.on_swipe_right
                if callback:
                    manager = self.manager

                    if manager:
                        manager.transition = SlideTransition(
                            direction='left' if dx < 0 else 'right',
                            duration=0.25
                        )

                    callback()
                    return True
        return result


class BreadUnitApp(App):
    def build(self):
        # Use the saved language if selected; otherwise use device locale.
        self.settings_path = Path(self.user_data_dir) / 'settings.json'
        try:
            settings = json.loads(self.settings_path.read_text(encoding='utf-8'))
            saved_lang = settings.get('language') if isinstance(settings, dict) else None
        except (OSError, ValueError):
            saved_lang = None

        self.lang = saved_lang if saved_lang in ('ru', 'en') else get_device_language()
        self.tr = TRANSLATIONS[self.lang]
        self.title = self.tr['window_title']
        self.values = {}
        self.inputs = {}
        self.history_path = Path(self.user_data_dir) / 'history.json'
        self.history_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            self.history = json.loads(
                self.history_path.read_text(encoding='utf-8')
            )
            if not isinstance(self.history, list):
                self.history = []
        except (OSError, ValueError):
            self.history = []

        self.manager = ScreenManager(
            transition=SlideTransition(
                direction='left',
                duration=0.25
            )
        )
        self.show_home()
        return self.manager

    def screen(self, name, title):
        if self.manager.has_screen(name):
            self.manager.remove_widget(self.manager.get_screen(name))

        screen = SwipeScreen(name=name)

        # Цвет фона экрана
        with screen.canvas.before:
            Color(*get_color_from_hex('#1e1e1e'))  # RGBA
            background = Rectangle(pos=screen.pos, size=screen.size)

        # Фон подстраивается под размер экрана
        screen.bind(
            pos=lambda instance, value: setattr(background, 'pos', value),
            size=lambda instance, value: setattr(background, 'size', value)
        )

        layout = BoxLayout(
            orientation='vertical',
            padding=[dp(22), dp(20), dp(22), dp(20)],
            spacing=dp(14)
        )

        heading = Label(
            text=title,
            font_size=sp(27),
            size_hint_y=None,
            height=dp(76),
            halign='center',
            valign='middle'
        )

        layout.add_widget(heading)
        screen.add_widget(layout)
        self.manager.add_widget(screen)
        self.manager.current = name

        return layout

    def button(self, layout, caption, action):
        btn = Button(
            text=caption,
            size_hint_y=None,
            height=dp(78),
            font_size=sp(23)
        )
        btn.bind(on_release=lambda *_: action())
        layout.add_widget(btn)

    def show_home(self):
        layout = self.screen('home', self.tr['app_title'])

        home_screen = self.manager.get_screen('home')
        home_screen.on_swipe_left = lambda: self.show_step(1)
        home_screen.on_swipe_right = self.show_results

        logo = Image(
            source=str(Path(__file__).resolve().parent / 'icon.png'),
            size_hint_y=None,
            height=dp(230),
            fit_mode='contain'
        )
        layout.add_widget(logo)
        
        self.button(layout, self.tr['calculate_carbs'], lambda: self.show_step(1))
        self.button(layout, self.tr['view_results'], self.show_results)
        layout.add_widget(Widget())

        # Language switcher anchored to the bottom of the home screen.
        language_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(48),
            spacing=dp(10)
        )
        for language, caption in (('en', 'EN'), ('ru', 'RU')):
            active = language == self.lang
            btn = Button(
                text=caption,
                font_size=sp(18),
                bold=active,
                background_normal='',
                background_color=(0.34, 0.34, 0.34, 1) if active else (0.17, 0.17, 0.17, 1),
                color=(1, 1, 1, 1) if active else (0.72, 0.72, 0.72, 1)
            )
            btn.bind(on_release=lambda _, lang=language: self.set_language(lang))
            language_row.add_widget(btn)
        layout.add_widget(language_row)

    def set_language(self, language):
        if language not in TRANSLATIONS or language == self.lang:
            return

        self.lang = language
        self.tr = TRANSLATIONS[language]
        self.title = self.tr['window_title']
        try:
            self.settings_path.write_text(
                json.dumps({'language': language}, ensure_ascii=False),
                encoding='utf-8'
            )
        except OSError:
            pass

        if hasattr(self, 'exact_grams_per_xe'):
            self.current_result = self.format_result(
                self.values.get('productName', ''),
                math.ceil(self.exact_grams_per_xe)
            )

        self.show_home()

    def show_step(self, number):
        config = {
            1: [('emptyTareWeight', self.tr['tare'], True)],
            2: [
                ('productName', self.tr['product_name'], False),
                ('productWeightBeforeCooking', self.tr['raw_weight'], True)
            ],
            3: [('carbohydratesPer100g', self.tr['carbs_100'], True)],
            4: [('finalWeight', self.tr['final_weight'], True)],
        }

        layout = self.screen('step', self.tr['step'].format(number=number))
        current_screen = self.manager.get_screen('step')
        self.inputs = {}

        for key, label_text, numeric in config[number]:
            field_label = Label(
                text=label_text,
                size_hint_y=None,
                height=dp(52),
                font_size=sp(22),
                halign='left',
                valign='middle'
            )
            field_label.bind(size=lambda instance, size: setattr(instance, 'text_size', size))
            layout.add_widget(field_label)

            field = TextInput(
                text=str(self.values.get(key, '')),
                multiline=False,
                input_filter='int' if numeric else None,
                size_hint_y=None,
                height=dp(76),
                font_size=sp(24),
                padding=[dp(12), dp(10), dp(12), dp(10)]
            )
            self.inputs[key] = field
            layout.add_widget(field)

        error = Label(
            text='',
            color=(1, 0.35, 0.35, 1),
            size_hint_y=None,
            height=dp(60),
            font_size=sp(18)
        )
        layout.add_widget(error)

        def next_step():
            for key, _, numeric in config[number]:
                value = self.inputs[key].text.strip()

                if numeric and (not value or int(value) <= 0):
                    if key == 'emptyTareWeight' and value == '0':
                        pass
                    else:
                        error.text = (
                            self.tr['invalid_tare']
                            if key == 'emptyTareWeight'
                            else self.tr['invalid_positive']
                        )
                        return

                self.values[key] = int(value) if numeric else value

            if number == 4:
                required_previous = ('emptyTareWeight', 'productWeightBeforeCooking', 'carbohydratesPer100g')
                if not all(key in self.values for key in required_previous):
                    error.text = self.tr['missing_steps']
                    return
                if self.values['finalWeight'] <= self.values['emptyTareWeight']:
                    error.text = self.tr['invalid_final']
                    return
                self.calculate()
            else:
                self.show_step(number + 1)

        current_screen.on_swipe_left = next_step
        current_screen.on_swipe_right = (
            lambda: self.show_home() if number == 1 else self.show_step(number - 1)
        )

        self.button(layout, self.tr['next'] if number < 4 else self.tr['calculate'], next_step)
        self.button(
            layout,
            self.tr['back'],
            lambda: self.show_home() if number == 1 else self.show_step(number - 1)
        )
        layout.add_widget(Widget())

    def save_history(self, data):
        timestamp = datetime.now().astimezone().strftime('%d.%m.%Y %H:%M')
        self.history.insert(0, {'timestamp': timestamp, **data})
        try:
            self.history_path.write_text(
                json.dumps(self.history, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
        except OSError:
            pass

    def format_result(self, name, grams):
        name = str(name).strip() or self.tr['unnamed']
        return self.tr['result_one'].format(name=name, grams=grams)

    def calculate(self):
        v = self.values
        cooked_weight = v['finalWeight'] - v['emptyTareWeight']
        carbs = v['productWeightBeforeCooking'] * v['carbohydratesPer100g'] / 100
        self.exact_grams_per_xe = cooked_weight * 10 / carbs
        grams = math.ceil(self.exact_grams_per_xe)
        name = v.get('productName', '').strip()
        self.current_result = self.format_result(name, grams)
        self.save_history({'name': name, 'grams_per_xe': grams})
        self.show_results()

    def show_results(self):
        layout = self.screen('results', self.tr['results'])
        results_screen = self.manager.get_screen('results')
        results_screen.on_swipe_left = self.show_home
        results_screen.on_swipe_right = lambda: self.show_step(4)

        if hasattr(self, 'current_result'):
            result_label = Label(
                text=self.current_result,
                size_hint_y=None,
                height=dp(82),
                font_size=sp(21),
                halign='left',
                valign='middle'
            )
            result_label.bind(size=lambda instance, size: setattr(instance, 'text_size', size))
            layout.add_widget(result_label)

            question = Label(
                text=self.tr['question'],
                size_hint_y=None,
                height=dp(52),
                font_size=sp(21),
                halign='left',
                valign='middle'
            )
            question.bind(size=lambda instance, size: setattr(instance, 'text_size', size))
            layout.add_widget(question)

            count = TextInput(
                text='1',
                input_filter='int',
                multiline=False,
                size_hint_y=None,
                height=dp(76),
                font_size=sp(24),
                padding=[dp(12), dp(10), dp(12), dp(10)]
            )
            layout.add_widget(count)

            answer = Label(
                text='',
                size_hint_y=None,
                height=dp(68),
                font_size=sp(23),
                halign='left',
                valign='middle'
            )
            answer.bind(size=lambda instance, size: setattr(instance, 'text_size', size))
            layout.add_widget(answer)

            def recalc(*_):
                if count.text and int(count.text) > 0:
                    n = int(count.text)
                    answer.text = self.tr['result_count'].format(count=n, grams=math.ceil(self.exact_grams_per_xe * n))
                else:
                    answer.text = self.tr['invalid_positive']

            count.bind(text=recalc)
            recalc()
        else:
            layout.add_widget(Label(
                text=self.tr['no_current'],
                size_hint_y=None,
                height=dp(60),
                font_size=sp(20)
            ))

        # Небольшой отступ, чтобы отделить историю от текущего расчёта.
        layout.add_widget(Widget(size_hint_y=None, height=dp(22)))

        history_heading = Label(
            text=self.tr['previous'],
            size_hint_y=None,
            height=dp(48),
            font_size=sp(22),
            halign='left',
            valign='middle'
        )
        history_heading.bind(
            size=lambda instance, size: setattr(instance, 'text_size', size)
        )
        layout.add_widget(history_heading)

        scroll = ScrollView()
        content = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(10)
        )
        content.bind(minimum_height=content.setter('height'))

        if not self.history:
            content.add_widget(Label(
                text=self.tr['empty_history'],
                size_hint_y=None,
                height=dp(60),
                font_size=sp(18)
            ))
        else:
            for item in self.history:
                # Поддерживаем старые записи, сохранённые просто строками.
                if isinstance(item, dict):
                    timestamp = str(item.get('timestamp', '')).strip()
                    if 'grams_per_xe' in item:
                        message = self.format_result(item.get('name', ''), item['grams_per_xe'])
                    else:
                        message = str(item.get('text', ''))  # Legacy entry
                    text = f'{timestamp}\n{message}' if timestamp else message
                else:
                    text = str(item)

                history_label = Label(
                    text=text,
                    size_hint_y=None,
                    height=dp(94),
                    font_size=sp(18),
                    halign='left',
                    valign='middle'
                )
                history_label.bind(
                    width=lambda instance, width: setattr(
                        instance, 'text_size', (max(width - 8, 1), None)
                    )
                )
                content.add_widget(history_label)

        scroll.add_widget(content)
        layout.add_widget(scroll)
        self.button(layout, self.tr['home'], self.show_home)


if __name__ == '__main__':
    BreadUnitApp().run()
