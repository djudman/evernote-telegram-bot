VERSION := $(shell cat ./VERSION)

all:
	docker build --force-rm -t djudman/evernote-telegram-bot:$(VERSION) .
	docker tag djudman/evernote-telegram-bot:$(VERSION) djudman/evernote-telegram-bot:latest
push:
	docker push djudman/evernote-telegram-bot
clear:
	docker rmi $$(docker images -qa -f dangling=true)
test:
	cd ./src && pipenv run python test.py
update:
	git pull origin master
	docker build --force-rm -t djudman/evernote-telegram-bot:$(VERSION) .
	docker-compose up -d
	docker logs evernotebot
