Telegram bot for Evernote
=========================
[![Build status](https://travis-ci.org/djudman/evernote-telegram-bot.svg?branch=master)](https://travis-ci.org/djudman/evernote-telegram-bot?branch=master)
[![Coverage Status](https://coveralls.io/repos/github/djudman/evernote-telegram-bot/badge.svg?branch=master)](https://coveralls.io/github/djudman/evernote-telegram-bot?branch=master)
[![Maintainability](https://api.codeclimate.com/v1/badges/1d23d48c1a7370b7b12f/maintainability)](https://codeclimate.com/github/djudman/evernote-telegram-bot/maintainability)

This bot can save everything that you send to Evernote account.

You can use this bot in Telegram: https://t.me/evernoterobot  
Or you can use your own telegram bot and your own server, then see [Installation](#Installation)

# Installation
If you have some reasons do not use my bot deployed on my server, you can use
your own installation.  

* Create your own bot with the
[BotFather](https://telegram.me/BotFather)
(see https://core.telegram.org/bots#3-how-do-i-create-a-bot)  
* Install a Docker to your server (see https://docs.docker.com/install/)
* Get and set up SSL certificate (see https://letsencrypt.org)
* Set up nginx or another proxy server to work with your SSL certificate.
* Clone source code to your server
    ```
    git clone https://github.com/djudman/evernote-telegram-bot.git
    ```
* Build your own docker image
    ```
    docker build -t evernote-telegram-bot
    ```
* Define [environment variables](#Environment-variables) (for example, in `.bashrc`)
* Run a container
    ```
    docker run \
        -e EVERNOTEBOT_DEBUG="${EVERNOTEBOT_DEBUG}" \
        -e MONGO_HOST="${MONGO_HOST}" \
        -e EVERNOTEBOT_HOSTNAME="${EVERNOTEBOT_HOSTNAME}" \
        -e TELEGRAM_API_TOKEN="${TELEGRAM_API_TOKEN}" \
        -e TELEGRAM_BOT_NAME="${TELEGRAM_BOT_NAME}" \
        -e EVERNOTE_BASIC_ACCESS_KEY="${EVERNOTE_BASIC_ACCESS_KEY}" \
        -e EVERNOTE_BASIC_ACCESS_SECRET="${EVERNOTE_BASIC_ACCESS_SECRET}" \
        -e EVERNOTE_FULL_ACCESS_KEY="${EVERNOTE_FULL_ACCESS_KEY}" \
        -e EVERNOTE_FULL_ACCESS_SECRET="${EVERNOTE_FULL_ACCESS_SECRET}" \
        --rm \
        --name=evernotebot \
        -it \
        -v ./logs:/app/logs:rw \
        evernote-telegram-bot
    ```

# Environment variables
| Variable name                | Default value | Description |
|------------------------------|---------------|-------------|
| DEBUG                        | 0             | Enable debug mode (additional logging enabled) |
| MONGO_HOST                   | 127.0.0.1     | Hostname for mongodb host|
| EVERNOTEBOT_HOSTNAME         | evernotebot.djudman.info | DNS name of your host
| TELEGRAM_API_TOKEN           | -             | Access token for telegram API. You can obtain this by BotFather |
| TELEGRAM_BOT_NAME            | evernoterobot | Name of telegram bot. You used this in BotFather |
| EVERNOTE_BASIC_ACCESS_KEY    | -             | appKey for your Evernote app (with readonly permissions) |
| EVERNOTE_BASIC_ACCESS_SECRET | -             | secret for your Evernote app (with readonly permissions) |
| EVERNOTE_FULL_ACCESS_KEY     | -             | appKey for your Evernote app (with read/write permissions) |
| EVERNOTE_FULL_ACCESS_SECRET  | -             | secret for your Evernote app (with read/write permissions) |
