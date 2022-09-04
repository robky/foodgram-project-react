# Учебный проект Foodgram
### Описание
REST API для проекта Foodgram - «Продуктовый помощник». На этом сервисе пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.

### Demo: http://51.250.97.251/admin
```
login: user
password: 1234
```

### Технологии
Python 3.7
Django 3.2.15
Django Rest Framework 3.13.1

![example branch parameter](https://github.com/robky/foodgram-project-react/actions/workflows/foodgram.yml/badge.svg)

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/robky/foodgram-project-react.git
cd yamdb_final
```

Переименовать файл .env.example

```
mv ./infra/.env.example ./infra/.env
```

Заполнить файл .env актуальными данными согласно примера.

Запустить контейнер

```
docker-compose up -d --build
```

В скрипте автоматически выполнятся задачи миграции, подключения статики и наполнение базы демонстрациооными данными

Запустить в браузере

```
http://localhost/
```
