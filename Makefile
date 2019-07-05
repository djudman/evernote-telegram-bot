httpd:
	@if [ ! -d "./logs" ]; then mkdir logs; fi
	gunicorn \
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
	--network=evernotebot-net \
	-it \
	-p 127.0.0.1:8000:8000 \
	-v evernotebot-logs:/app/logs:rw \
	"djudman/evernote-telegram-bot:latest"
