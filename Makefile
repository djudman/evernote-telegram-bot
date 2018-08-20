all:
	docker build -t djudman/evernote-telegram-bot:latest .
push:
	docker push djudman/evernote-telegram-bot
