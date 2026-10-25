import json
import math
from pathlib import Path

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput


class BreadUnitApp(App):
    def build(self):
        self.title = 'Калькулятор ХЕ'
        self.values = {}
        self.inputs = {}
        self.history_path = Path(self.user_data_dir) / 'history.json'
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.history = json.loads(self.history_path.read_text(encoding='utf-8'))
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
        screen = Screen(name=name)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=12)
        layout.add_widget(Label(text=title, font_size='23sp', size_hint_y=None, height=65))
        screen.add_widget(layout)
        self.manager.add_widget(screen)
        self.manager.current = name
        return layout

    def button(self, layout, caption, action):
        btn = Button(text=caption, size_hint_y=None, height=55)
        btn.bind(on_release=lambda *_: action())
        layout.add_widget(btn)

    def show_home(self):
        layout = self.screen('home', 'Калькулятор хлебных единиц')
        self.button(layout, 'Рассчитать углеводы', lambda: self.show_step(1))
        self.button(layout, 'Посмотреть результаты', self.show_results)
        layout.add_widget(Label())

    def show_step(self, number):
        config = {
            1: [('emptyTareWeight', 'Вес пустой тары, г *', True)],
            2: [('productName', 'Название продукта', False),
                ('productWeightBeforeCooking', 'Вес продукта до приготовления, г *', True)],
            3: [('carbohydratesPer100g', 'Углеводы на 100 г *', True)],
            4: [('finalWeight', 'Вес тары с готовым продуктом, г *', True)],
        }
        layout = self.screen('step', f'Шаг {number} из 4')
        self.inputs = {}
        for key, label, numeric in config[number]:
            layout.add_widget(Label(text=label, size_hint_y=None, height=40))
            field = TextInput(text=str(self.values.get(key, '')), multiline=False,
                              input_filter='int' if numeric else None,
                              size_hint_y=None, height=55, font_size='20sp')
            self.inputs[key] = field
            layout.add_widget(field)
        error = Label(text='', color=(1, 0.35, 0.35, 1), size_hint_y=None, height=60)
        layout.add_widget(error)

        def next_step():
            for key, _, numeric in config[number]:
                value = self.inputs[key].text.strip()
                if numeric and (not value or int(value) <= 0):
                    if key == 'emptyTareWeight' and value == '0':
                        pass
                    else:
                        error.text = 'Введите корректное неотрицательное число' if key == 'emptyTareWeight' else 'Введите целое число больше нуля'
                        return
                self.values[key] = int(value) if numeric else value
            if number == 4:
                if self.values['finalWeight'] <= self.values['emptyTareWeight']:
                    error.text = 'Итоговый вес должен быть больше веса тары'
                    return
                self.calculate()
            else:
                self.show_step(number + 1)

        self.button(layout, 'Далее' if number < 4 else 'Рассчитать', next_step)
        self.button(layout, 'Назад', lambda: self.show_home() if number == 1 else self.show_step(number - 1))
        layout.add_widget(Label())

    def calculate(self):
        v = self.values
        cooked = v['finalWeight'] - v['emptyTareWeight']
        carbs = v['productWeightBeforeCooking'] * v['carbohydratesPer100g'] / 100
        self.exact_grams_per_xe = cooked * 10 / carbs
        grams = math.ceil(self.exact_grams_per_xe)
        name = v.get('productName', '').strip() or 'Без названия'
        self.current_result = f'1 ХЕ готового продукта «{name}» равна {grams} г.'
        self.history.insert(0, self.current_result)
        try:
            self.history_path.write_text(json.dumps(self.history, ensure_ascii=False, indent=2), encoding='utf-8')
        except OSError:
            pass
        self.show_results()

    def show_results(self):
        layout = self.screen('results', 'Результаты')
        if hasattr(self, 'current_result'):
            layout.add_widget(Label(text=self.current_result, size_hint_y=None, height=75))
            layout.add_widget(Label(text='Сколько нужно хлебных единиц?', size_hint_y=None, height=40))
            count = TextInput(text='1', input_filter='int', multiline=False, size_hint_y=None, height=55)
            layout.add_widget(count)
            answer = Label(text='', size_hint_y=None, height=60)
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
            layout.add_widget(Label(text='Текущий расчёт отсутствует', size_hint_y=None, height=50))
        layout.add_widget(Label(text='Предыдущие результаты:', size_hint_y=None, height=45))
        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=8)
        content.bind(minimum_height=content.setter('height'))
        for item in self.history:
            content.add_widget(Label(text=item, size_hint_y=None, height=65))
        scroll.add_widget(content)
        layout.add_widget(scroll)
        self.button(layout, 'На главную', self.show_home)


if __name__ == '__main__':
    BreadUnitApp().run()
