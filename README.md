# Финансовая аналитика по транзакциям 🧾📊

Проект представляет собой модуль финансового анализа на основе Excel-данных с транзакциями. Основные задачи — генерация аналитических JSON-ответов для веб-интерфейсов «Главная» и «События», анализ категорий, кешбэка, инвесткопилки и курсов валют/акций.

---

## 🚀 Возможности

- **Главная страница** (`generate_main_page_data`)
  - Приветствие по времени суток
  - Анализ расходов по картам
  - Топ-5 транзакций
  - Курсы валют и цены акций

- **Страница событий** (`generate_events_page_data`)
  - Расходы, доходы и переводы по категориям за период
  - Гибкий выбор периода (`W`, `M`, `Y`, `ALL`)
  - Интеграция с внешними API для курса валют и акций

- **Сервисы:**
  - Выгода от кешбэка по категориям
  - Подсчёт «инвесткопилки»
  - Поиск транзакций по ключевым словам, номерам телефонов и переводам частным лицам

- **Отчёты:**
  - Расходы по категориям за 3 месяца
  - Средние траты по дням недели и по типу дня

---

## 🗂️ Структура проекта

```
project-root/
├── data/
│   ├── operations.xlsx             # Финансовые транзакции
│   └── user_settings.json          # Настройки пользователя
│
├── src/
│   ├── __init__.py                 # Пакетный инициализатор
│   ├── main.py                     # Главный демонстрационный скрипт
│   ├── views.py                    # Главная и События
│   ├── options.py                  # API и загрузка данных
│   ├── services.py                 # Кешбэк, инвесткопилка, поиск
│   ├── reports.py                  # Отчёты по тратам
│   ├── utils.py                    # Парсинг даты, приветствие
│   └── decorators.py               # Сохранение результатов
│
├── tests/
│   ├── test_views.py               # Тесты views.py
│   ├── test_utils.py               # Тесты utils.py
│   ├── test_options.py             # Тесты options.py
│   ├── test_services.py            # Тесты services.py
│   ├── test_reports.py             # Тесты reports.py
│   └── conftest.py                 # Общие фикстуры (sample_transactions и др.)
│
├── .env                            # Переменные окружения (ключ API, пути к данным)
├── .env_template                   # Шаблон для .env
├── .flake8                         # Настройки линтера
├── .gitignore                      # Игнорируемые файлы
├── .coverage                       # Покрытие после pytest --cov
├── LICENSE                         # MIT License
├── README.md                       # Документация и инструкция по запуску
├── pytest.ini                      # Конфигурация pytest
└── pyproject.toml                  # Настройки зависимостей (poetry, black и т.д.)
```

---

## ⚙️ Установка

1. Клонируй проект:
   ```bash
   git clone <repo_url>
   cd <project_folder>
   ```

2. Установи зависимости:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # или .venv\Scriptsctivate в Windows
   poetry install
   ```

3. Настрой `.env`:
   ```env
   DATA_FILE=data/operations.xlsx
   SETTINGS_FILE=data/user_settings.json
   FINNHUB_API_KEY=your_api_key_here
   ```

✅ Требования: Python 3.10+

---

## 🦚 Формат входных данных

- **operations.xlsx** — Excel-файл с колонками:
  - `date`, `amount`, `category`, `description`, `card`, `type`, `to` и т.п.
- **user_settings.json** — настройки отображения, предпочтения по категориям, карты и др.

---

## 🔮 Примеры JSON-ответов

### Пример `generate_main_page_data`
```json
{
  "greeting": "Доброе утро",
  "cards_spending": {
    "Tinkoff Black": 12000,
    "Sberbank": 5300
  },
  "top_transactions": [
    {"date": "2025-05-01", "amount": -5000, "description": "Продукты"},
    {"date": "2025-05-02", "amount": -4500, "description": "Кафе"}
  ],
  "currencies": {"USD": 91.5, "EUR": 98.1},
  "stocks": {"AAPL": 187.2, "TSLA": 172.4}
}
```

---

## 🧯 Тестирование

Запуск тестов:
```bash
pytest
```
С отчётом покрытия:
```bash
pytest --cov=src
```

---

## 🛠️ TODO / Возможные улучшения

- Добавить веб-интерфейс (FastAPI, Flask)
- CI/CD-пайплайн (GitHub Actions)
- Расширить модуль поиска (по магазинам, гео, суммам)
- Подключение к банковским API

---

## 👨‍💻 Авторы

- 👤 [black-sun-spb]
- 📬 Контакты: [taisiya199264@gmail.com]

---

## 🪪 Лицензия

Этот проект лицензируется под [MIT License](LICENSE).

---

## 📈 Бейджи

![Tests](https://img.shields.io/badge/tests-passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-90%25-blue)
![License](https://img.shields.io/badge/license-MIT-green)
