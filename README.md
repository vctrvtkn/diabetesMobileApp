# Bread Unit Calculator / Калькулятор хлебных единиц

A simple mobile calculator for estimating bread units (BU / ХЕ) in cooked food.
Простое мобильное приложение для расчёта хлебных единиц (ХЕ) в готовом продукте.

**Note:** This tool provides calculations based on user-entered nutritional information. It is not a substitute for individualized medical advice.
**Внимание:** Этот инструмент выполняет расчеты на основе введенной пользователем информации о пищевой ценности. Он не заменяет индивидуальную медицинскую консультацию.

***Why is it needed?***
The idea is to accurately calculate the XE during the cooking process:
1. Weigh the empty cookware (pot, ladle, etc.) -> Enter the value
2. Reset the scale to zero, add the raw product -> Enter the value
3. Cook, scale the cooked product with the cookware -> Enter the value

If you don't want to consider cookware weight, enter 0 in step 1, but then you'll need to enter the cooked product's value without the cookware weight in step 4. // Later, I'll add an option to account for 0 and a warning in step 4.

***Зачем оно надо?***
Идея в том, чтобы считать точно ХЕ в процессе готовки:
1. Взвесили пустую тару (кастрюля, ковш и пр.) -> Ввели значение
2. Обнулили значение на весах, положили сырой продукт -> Ввели значение
3. Приготовили, поставили на весы (готовый продукт вместе с тарой) -> Ввели значение

Если вы не хотите учитывать вес тары, то ставьте значение 0 в шаге 1, но тогда в шаге 4 надо вводить значение готового продукта без тары. // Позже добавлю учет значения 0 и предупреждение в шаге 4.



## Features / Возможности

- Calculates the weight of cooked food corresponding to one bread unit (1 ХЕ = 10 g carbohydrates).
- Calculates the portion weight for a selected number of bread units.
- Takes into account empty container weight, raw product weight, carbohydrates per 100 g, and final cooked weight with the container.
- Saves a local history of calculations.
- Supports Russian and English interface languages based on the device locale (English fallback).
- Supports swipe navigation between screens.

- Рассчитывает вес готового продукта, соответствующий одной хлебной единице (1 ХЕ = 10 г углеводов).
- Рассчитывает вес порции для выбранного количества хлебных единиц.
- Учитывает вес пустой емкости, вес сырого продукта, содержание углеводов на 100 г и конечный вес готового продукта с емкостью.
- Сохраняет локальную историю расчетов.
- Поддерживает русский и английский языки интерфейса в зависимости от локали устройства (запасной английский).
- Поддерживает навигацию между экранами с помощью жестов.

## Technology / Технологии

- Python 3
- Kivy
- Buildozer / python-for-android for Android APK builds

## Run locally / Запуск на компьютере

Install Kivy in a compatible Python environment, then run:
Установите Kivy в совместимой среде Python, затем выполните:

```bash
python main.py
```

Keep `main.py`, `translations.py`, and `icon.png` in the project directory.
Файлы `main.py`, `translations.py` и `icon.png` должны находиться в директории проекта.

## Build for Android / Сборка для Android

Buildozer runs in a Linux environment. With a configured `buildozer.spec`, run:
Buildozer работает в среде Linux. После настройки файла `buildozer.spec` выполните следующую команду:
```bash
buildozer android debug
```

## Calculation / Формула

Carbohydrates in the raw product:
Углеводы в сыром продукте:
`carbs = raw_weight_g * carbs_per_100g / 100`

Cooked product weight:
Вес готового продукта с тарой:
`cooked_weight_g = final_weight_with_container_g - empty_container_weight_g`

Grams of cooked food per 1 bread unit:
Количество граммов готовой пищи на 1 хлебную единицу:
`grams_per_BU = cooked_weight_g * 10 / carbs`

Displayed gram values are rounded up to whole grams.
Отображаемые значения в граммах округлены до целых граммов.

## License / Лицензия

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
Проект распространяется по лицензии MIT. Полный текст — в файле [LICENSE](LICENSE).
