VERSION := $(shell cat ./VERSION)

httpd:
	@gunicorn --error-logfile ./logs/errors.log evernotebot.wsgi:app
