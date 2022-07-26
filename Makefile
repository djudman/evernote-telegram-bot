# This file just for some cases in local development

default:
	docker build --no-cache -t djudman/evernote-telegram-bot .
	docker push djudman/evernote-telegram-bot
test:
	python3 tests/run.py
run:
	./init.d/evernotebot start
