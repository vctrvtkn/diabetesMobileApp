import json
import math
from datetime import datetime
from pathlib import Path

from kivy.metrics import dp, sp
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.utils import get_color_from_hex

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
                    callback()
                    return True
        return result


class BreadUnitApp(App):
    def build(self):
        self.title = 'Калькулятор ХЕ'
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

        self.manager = ScreenManager()
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
        layout = self.screen('home', 'Калькулятор\n хлебных единиц')

        home_screen = self.manager.get_screen('home')
        home_screen.on_swipe_left = lambda: self.show_step(1)
        home_screen.on_swipe_right = self.show_results
        
        self.button(layout, 'Рассчитать углеводы', lambda: self.show_step(1))
        self.button(layout, 'Посмотреть результаты', self.show_results)
        layout.add_widget(Widget())

    def show_step(self, number):
        config = {
            1: [('emptyTareWeight', 'Вес пустой тары, г *', True)],
            2: [
                ('productName', 'Название продукта', False),
                ('productWeightBeforeCooking', 'Вес продукта до приготовления, г *', True)
            ],
            3: [('carbohydratesPer100g', 'Углеводы на 100 г *', True)],
            4: [('finalWeight', 'Вес тары с готовым продуктом, г *', True)],
        }

        layout = self.screen('step', f'Шаг {number} из 4')
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
                            'Введите корректное неотрицательное число'
                            if key == 'emptyTareWeight'
                            else 'Введите целое число больше нуля'
                        )
                        return

                self.values[key] = int(value) if numeric else value

            if number == 4:
                required_previous = ('emptyTareWeight', 'productWeightBeforeCooking', 'carbohydratesPer100g')
                if not all(key in self.values for key in required_previous):
                    error.text = 'Сначала заполните шаги 1–3'
                    return
                if self.values['finalWeight'] <= self.values['emptyTareWeight']:
                    error.text = 'Итоговый вес должен быть больше веса тары'
                    return
                self.calculate()
            else:
                self.show_step(number + 1)

        current_screen.on_swipe_left = next_step
        current_screen.on_swipe_right = (
            lambda: self.show_home() if number == 1 else self.show_step(number - 1)
        )

        self.button(layout, 'Далее' if number < 4 else 'Рассчитать', next_step)
        self.button(
            layout,
            'Назад',
            lambda: self.show_home() if number == 1 else self.show_step(number - 1)
        )
        layout.add_widget(Widget())

    def save_history(self, message):
        timestamp = datetime.now().astimezone().strftime('%d.%m.%Y %H:%M')
        self.history.insert(0, {
            'timestamp': timestamp,
            'text': message
        })

        try:
            self.history_path.write_text(
                json.dumps(self.history, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
        except OSError:
            pass

    def calculate(self):
        v = self.values
        cooked_weight = v['finalWeight'] - v['emptyTareWeight']
        carbs = v['productWeightBeforeCooking'] * v['carbohydratesPer100g'] / 100

        self.exact_grams_per_xe = cooked_weight * 10 / carbs
        grams = math.ceil(self.exact_grams_per_xe)
        name = v.get('productName', '').strip() or 'Без названия'

        self.current_result = f'1 ХЕ готового продукта «{name}» равна {grams} г.'
        self.save_history(self.current_result)
        self.show_results()

    def show_results(self):
        layout = self.screen('results', 'Результаты')
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
                text='Сколько нужно хлебных единиц?',
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
                    answer.text = f'{n} ХЕ — это {math.ceil(self.exact_grams_per_xe * n)} г.'
                else:
                    answer.text = 'Введите целое число больше нуля'

            count.bind(text=recalc)
            recalc()
        else:
            layout.add_widget(Label(
                text='Текущий расчёт отсутствует',
                size_hint_y=None,
                height=dp(60),
                font_size=sp(20)
            ))

        # Небольшой отступ, чтобы отделить историю от текущего расчёта.
        layout.add_widget(Widget(size_hint_y=None, height=dp(22)))

        history_heading = Label(
            text='Предыдущие результаты:',
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
                text='История пока пуста',
                size_hint_y=None,
                height=dp(60),
                font_size=sp(18)
            ))
        else:
            for item in self.history:
                # Поддерживаем старые записи, сохранённые просто строками.
                if isinstance(item, dict):
                    timestamp = str(item.get('timestamp', '')).strip()
                    message = str(item.get('text', ''))
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
        self.button(layout, 'На главную', self.show_home)


if __name__ == '__main__':
    BreadUnitApp().run()
