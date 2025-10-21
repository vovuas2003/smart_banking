# smart_banking

Черновики Вовы по реализации api для работы с БД (смотри примерный список API в functionality.txt, на данный момент реализована только небольшая часть)

## Новые файлы

db.py - черновик от коллег, класс для операций с БД

api.py - моё api для внедрения во фронтенд (для тестов в этом же файле вызываю конфигурацию класса из db.py, а также создаю и удаляю таблицы с помощью этого же класса, а не maven)

sql - директория для хранения sql файлов, вызываемых из api.py

## Как я запускал контейнер

Запустить docker desktop, далее в cmd

docker run --name db_proj -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=smart_banking -p 127.0.0.1:5432:5432 -d postgres:18

### Очистка докера

docker ps -a

docker stop db_proj

docker rm db_proj

docker volume ls

docker volume prune
