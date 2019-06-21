VERSION := $(shell cat ./VERSION)

httpd:
	gunicorn --error-logfile ./gunicorn-errors.log evernotebot.wsgi:app
