FROM python:3.10.1-alpine

# http://bugs.python.org/issue19846
# > At the moment, setting "LANG=C" on a Linux system *fundamentally breaks Python 3*, and that's not OK.
ENV LANG C.UTF-8

RUN apk update \
	&& apk add --update --no-cache git tzdata gcc build-base

# if this is called "PIP_VERSION", pip explodes with "ValueError: invalid truth value '<VERSION>'"
ENV PYTHON_PIP_VERSION 22.2.2
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
	pip3 install --no-cache-dir -r requirements.txt; \
	cp /usr/share/zoneinfo/Europe/Moscow /etc/localtime; \
	mkdir /app/logs
COPY evernotebot /app/evernotebot

ENTRYPOINT [ \
	"uvicorn", \
	"--host=0.0.0.0", \
	"--port=8000", \
	"--workers=2", \
	"--loop=uvloop", \
	"--ws=none", \
	# TODO: lifespan support
	"--lifespan=off", \
	"--access-log", \
	"evernotebot.wsgi:app" \
]
