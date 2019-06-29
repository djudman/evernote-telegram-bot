httpd:
	gunicorn --error-logfile ./gunicorn-errors.log evernotebot.wsgi:app
test:
	@PWD=$(pwd)
	@cd ./tests && PYTHONPATH="$(PWD)" python3 -m unittest -v
build:
	docker build .
