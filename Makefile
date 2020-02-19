httpd:
	@if [ ! -d "./logs" ]; then mkdir logs; fi
	gunicorn \
		-e EVERNOTEBOT_DEBUG="true" \
		-e TELEGRAM_API_TOKEN="" \
		-e EVERNOTE_BASIC_ACCESS_KEY="" \
		-e EVERNOTE_BASIC_ACCESS_SECRET="" \
		-e EVERNOTE_FULL_ACCESS_KEY="" \
		-e EVERNOTE_FULL_ACCESS_SECRET="" \
		--bind=127.0.0.1:8000 \
		--access-logfile ./logs/gunicorn-access.log \
		--error-logfile ./logs/gunicorn-error.log \
		evernotebot.wsgi:app
test:
	python3 tests/run.py
build:
	docker build --no-cache -t djudman/evernote-telegram-bot .
	docker push djudman/evernote-telegram-bot
start:
	docker run \
		-e EVERNOTEBOT_DEBUG="${EVERNOTEBOT_DEBUG}" \
		-e MONGO_HOST="${MONGO_HOST}" \
		-e EVERNOTEBOT_HOSTNAME="${EVERNOTEBOT_HOSTNAME}" \
		-e TELEGRAM_API_TOKEN="${TELEGRAM_API_TOKEN}" \
		-e TELEGRAM_BOT_NAME="${TELEGRAM_BOT_NAME}" \
		-e EVERNOTE_BASIC_ACCESS_KEY="${EVERNOTE_BASIC_ACCESS_KEY}" \
		-e EVERNOTE_BASIC_ACCESS_SECRET="${EVERNOTE_BASIC_ACCESS_SECRET}" \
		-e EVERNOTE_FULL_ACCESS_KEY="${EVERNOTE_FULL_ACCESS_KEY}" \
		-e EVERNOTE_FULL_ACCESS_SECRET="${EVERNOTE_FULL_ACCESS_SECRET}" \
		--rm \
		--name=evernotebot \
		-it \
		-v ./logs:/app/logs:rw \
		"djudman/evernote-telegram-bot:latest"
