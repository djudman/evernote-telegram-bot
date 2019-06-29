httpd:
	gunicorn --error-logfile ./gunicorn-errors.log evernotebot.wsgi:app
test:
	@PWD=$(pwd)
	@cd ./tests && PYTHONPATH="$(PWD)" python3 -m unittest -v
test-cov:
	coverage run --include=evernotebot/* tests/run.py
	# @echo "\n* Code coverage *\n"
	# coverage report
	# coverage html
build:
	docker build .
