httpd:
	@if [ ! -d "./logs" ]; then mkdir logs; fi
	gunicorn \
	-e TELEGRAM_API_TOKEN="" \
	-e EVERNOTE_BASIC_ACCESS_KEY="" \
	-e EVERNOTE_BASIC_ACCESS_SECRET="" \
	-e EVERNOTE_FULL_ACCESS_KEY="" \
	-e EVERNOTE_FULL_ACCESS_SECRET="" \
	-e EVERNOTEBOT_ADMINS="root:4813494d137e1631bba301d5acab6e7bb7aa74ce1185d456565ef51d737677b2" \
	--bind=127.0.0.1:8000 \
	--access-logfile ./logs/gunicorn-access.log \
	--error-logfile ./logs/gunicorn-error.log \
	evernotebot.wsgi:app
test:
	coverage run --include=evernotebot/* tests/run.py
	coverage report
build:
	docker build -t djudman/evernote-telegram-bot:latest .
	docker push djudman/evernote-telegram-bot:latest
start:
docker run \
-e MONGO_HOST="${MONGO_HOST}" \
-e TELEGRAM_API_TOKEN="${TELEGRAM_API_TOKEN}" \
-e EVERNOTE_BASIC_ACCESS_KEY="${EVERNOTE_BASIC_ACCESS_KEY}" \
-e EVERNOTE_BASIC_ACCESS_SECRET="${EVERNOTE_BASIC_ACCESS_SECRET}" \
-e EVERNOTE_FULL_ACCESS_KEY="${EVERNOTE_FULL_ACCESS_KEY}" \
-e EVERNOTE_FULL_ACCESS_SECRET="${EVERNOTE_FULL_ACCESS_SECRET}" \
--rm \
--name=evernotebot \
--network=nginx-net \
-it \
-v evernotebot-logs:/app/logs:rw \
"djudman/evernote-telegram-bot:latest"
