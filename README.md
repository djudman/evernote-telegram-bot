Telegram bot for Evernote
=========================
[![Coverage Status](https://coveralls.io/repos/github/djudman/evernote-telegram-bot/badge.svg?branch=master)](https://coveralls.io/github/djudman/evernote-telegram-bot?branch=master)
[![Maintainability](https://api.codeclimate.com/v1/badges/1d23d48c1a7370b7b12f/maintainability)](https://codeclimate.com/github/djudman/evernote-telegram-bot/maintainability)

This bot can save to your Evernote everything that you send.

You can use this bot in Telegram: https://t.me/evernoterobot  
*Or* you can use **your own** telegram bot and your own server, then see [Installation](#Installation)

# Installation
If you have some reasons do not use my bot deployed on my server, you can use
your own installation.  

* Create your bot with the
[BotFather](https://telegram.me/BotFather)
(see https://core.telegram.org/bots#3-how-do-i-create-a-bot)
* Create Evernote application and obtain a pair of keys (access key and access secret) 
    * Go to https://dev.evernote.com/doc/ and press the green button *"GET AN API KEY"*
* Install a Docker to your server (see https://docs.docker.com/install/)
* Get and set up SSL certificate (see https://letsencrypt.org)
* Set up [nginx](https://nginx.org)/[caddy](https://caddyserver.com)/another proxy server to work with your SSL certificate.
* Check you have *[curl](https://curl.haxx.se/download.html)* on your server (usually it's installed by default)
* Execute this command: `sudo curl https://raw.githubusercontent.com/djudman/evernote-telegram-bot/master/evernotebot-install.sh --output evernotebot-install.sh && sh evernotebot-install.sh`
    * `sudo` is needed because there is copying a file to `/etc/init.d` directory
    * you will need to enter some data as:
        * telegram api token
        * evernote access key
        * evernote access secret
        * etc., see [Environment variables](#Environment-variables)
* Execute `/etc/init.d/evernotebot start` to start bot

## How to build docker image manually

* Clone source code to your server
    ```
    git clone https://github.com/djudman/evernote-telegram-bot.git
    ```
* Build image
    ```
    docker build -t evernote-telegram-bot .
    ```
* Define [environment variables](#Environment-variables) (for example, in `.bashrc`)
* Create a docker volume to store data
    `docker volume create evernotebot-data`
* Run a container
    ```
    docker run \
        -e EVERNOTEBOT_DEBUG="$EVERNOTEBOT_DEBUG" \
        -e EVERNOTEBOT_HOSTNAME="$EVERNOTEBOT_HOSTNAME" \
        -e EVERNOTEBOT_EXPOSE_PORT="$EVERNOTEBOT_EXPOSE_PORT" \
        -e TELEGRAM_API_TOKEN="$TELEGRAM_API_TOKEN" \
        -e TELEGRAM_BOT_NAME="$TELEGRAM_BOT_NAME" \
        -e EVERNOTE_READONLY_KEY="$EVERNOTE_READONLY_KEY" \
        -e EVERNOTE_READONLY_SECRET="$EVERNOTE_READONLY_SECRET" \
        -e EVERNOTE_READWRITE_KEY="$EVERNOTE_READWRITE_KEY" \
        -e EVERNOTE_READWRITE_SECRET="$EVERNOTE_READWRITE_SECRET" \
        -d \
        -p 127.0.0.1:8000:8000 \
        --restart=always \
        --name=evernotebot \
        -it \
        -v ./logs:/app/logs:rw \
        --mount source="evernotebot-data",target="/evernotebot-data" \
        evernote-telegram-bot
    ```

# Environment variables
| Variable name             | Default value         | Description                                                                                                  |
|---------------------------|-----------------------|--------------------------------------------------------------------------------------------------------------|
| EVERNOTEBOT_DIR           | $HOME/evernotebot     | Install dir for tha bot. Some files there. For example, `logs/` dir and `.env` file                          |
| EVERNOTEBOT_DEBUG         | 0                     | Enable debug mode (additional logging, use evernote sandbox)                                                 |
| EVERNOTEBOT_HOSTNAME      | evernotebot.djud.site | DNS name of your host. This name will use in such URLs as oauth callback url and webhook url                 |
| EVERNOTEBOT_EXPOSE_PORT   | 8000                  | Port that the docker container with bot listen on your machine. The bot inside container uses 127.0.0.1:8000 |
| TELEGRAM_BOT_NAME         | evernoterobot         | Name of telegram bot. You used this in BotFather                                                             |
| TELEGRAM_API_TOKEN        | -                     | Access token for telegram API. You can obtain this by BotFather                                              |
| EVERNOTE_READONLY_KEY     | -                     | appKey for your Evernote app (readonly permissions)                                                          |
| EVERNOTE_READONLY_SECRET  | -                     | secret for your Evernote app (readonly permissions)                                                          |
| EVERNOTE_READWRITE_KEY    | -                     | appKey for your Evernote app (read/write permissions), required for `one_note` bot mode                      |
| EVERNOTE_READWRITE_SECRET | -                     | secret for your Evernote app (read/write permissions), required for `one_note` bot mode                      |
