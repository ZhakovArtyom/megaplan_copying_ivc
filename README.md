**Запуск приложения из корневой директории проекта**
1. Соберите Docker-образ:

`docker build -t megaplan-copying-invoices .`

2. Запустите Docker-контейнер:

_для linux:_
`docker run -d --name invoice-megaplan-container --restart=always -v $(pwd)/logs:/app/logs -p 8001:8000 megaplan-copying-invoices`

_для windows:_
`docker run -d --name invoice-megaplan-container --restart=always -v ${PWD}/logs:/app/logs -p 8001:8000 megaplan-copying-invoices`

**_Если нужно удалить контейнер для перезапуска кода:_**
`docker rm -f invoice-megaplan-container`