httpd:
	@if [ ! -d "./logs" ]; then mkdir logs; fi
	gunicorn \
	--bind=127.0.0.1:8000 \
	--access-logfile ./logs/gunicorn-access.log \
	--error-logfile ./logs/gunicorn-error.log \
	evernotebot.wsgi:app
test:
	@PWD=$(pwd)
	@cd ./tests && PYTHONPATH="$(PWD)" python3 -m unittest -v
test-cov:
	coverage run --include=evernotebot/* tests/run.py
	coverage report
build:
	@if [ ! -d "./logs" ]; then mkdir logs; fi
	docker-compose build
	# docker push
# install:
