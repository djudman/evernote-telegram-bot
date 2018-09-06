all:
	docker build -t djudman/evernote-telegram-bot:latest .
push:
	docker push djudman/evernote-telegram-bot
test:
	cd ./src && pipenv run python test.py
