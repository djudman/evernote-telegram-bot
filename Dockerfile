FROM python:3.9.5-alpine

# http://bugs.python.org/issue19846
# > At the moment, setting "LANG=C" on a Linux system *fundamentally breaks Python 3*, and that's not OK.
ENV LANG C.UTF-8

RUN apk add git tzdata

# if this is called "PIP_VERSION", pip explodes with "ValueError: invalid truth value '<VERSION>'"
ENV PYTHON_PIP_VERSION 20.0.2
RUN set -ex; \
	wget -O get-pip.py 'https://bootstrap.pypa.io/get-pip.py'; \
	python get-pip.py --disable-pip-version-check --no-cache-dir "pip==$PYTHON_PIP_VERSION"; \
	pip --version; \
	\
	find /usr/local -depth \
		\( \
			\( -type d -a \( -name test -o -name tests \) \) \
			-o \
			\( -type f -a \( -name '*.pyc' -o -name '*.pyo' \) \) \
		\) -exec rm -rf '{}' +; \
	rm -f get-pip.py

WORKDIR /app/
COPY requirements.txt requirements.txt
RUN set -ex; \
	pip3 install -r requirements.txt; \
	cp /usr/share/zoneinfo/Europe/Moscow /etc/localtime; \
	mkdir /app/logs
COPY evernotebot /app/evernotebot
COPY util /app/util
COPY config.yaml /app/config.yaml

ENTRYPOINT [ \
	"gunicorn", \
	"--bind=0.0.0.0:8000", \
	"--workers=2", \
	"--preload", \
	"--access-logfile=/app/logs/gunicorn-access.log", \
	"--error-logfile=/app/logs/gunicorn-error.log", \
	"evernotebot.wsgi:app" \
]
