#!/usr/bin/env python3

import argparse
import logging.config
import sys
import os
from os.path import dirname, realpath, join
import signal
import time

sys.path.insert(0, realpath(dirname(__file__)))

import gunicorn_config
from daemons import EvernoteDealerDaemon, TelegramDownloaderDaemon
import settings


base_dir = realpath(dirname(__file__))
dealer_pidfile = join(base_dir, 'dealer.pid')
downloader_pidfile = join(base_dir, 'downloader.pid')
gunicorn_pidfile = gunicorn_config.pidfile


def green(s):
    return "\033[92m%s\033[0m" % s


def red(s):
    return "\033[91m%s\033[0m" % s


def check_process(pidfile):
    if os.path.exists(pidfile):
        with open(pidfile) as f:
            pid = int(f.read())
            try:
                os.kill(pid, 0)
            except OSError:
                os.unlink(pidfile)
                return False
            else:
                return True
    return False


def get_pid(pidfile):
    with open(pidfile) as f:
        pid = int(f.read())
        return pid


def start():
    os.makedirs(settings.LOGS_DIR, mode=0o700, exist_ok=True)
    os.makedirs(settings.DOWNLOADS_DIR, mode=0o700, exist_ok=True)
    logging.config.dictConfig(settings.LOG_SETTINGS)

    if not os.path.exists(gunicorn_pidfile):
        print('Starting gunicorn...', end="")
        os.system('gunicorn --config gunicorn_config.py %s' % gunicorn_config.app_name)
        time.sleep(1)
        if check_process(gunicorn_pidfile):
            print(green('OK'))
        else:
            print(red('FAILED'))
    else:
        print("Gunicorn already running")

    print('Starting downloader...')
    TelegramDownloaderDaemon(downloader_pidfile, settings.DOWNLOADS_DIR).start()
    print('Starting dealer...')
    EvernoteDealerDaemon(dealer_pidfile).start()


def stop():
    print('Stopping dealer...')
    EvernoteDealerDaemon(dealer_pidfile).stop()
    print('Stopping downloader...')
    TelegramDownloaderDaemon(downloader_pidfile).stop()

    print('Stopping gunicorn...', end="")
    os.kill(get_pid(gunicorn_pidfile), signal.SIGTERM)
    os.unlink(gunicorn_pidfile)
    print(green('OK'))


def status():
    for service_name, pidfile in [('Gunicorn', gunicorn_pidfile), ('Dealer', dealer_pidfile), ('Downloader', downloader_pidfile)]:
        print("{0} status: ".format(service_name), end="")
        if check_process(pidfile):
            print(green('Started'))
        else:
            print(red('Stopped'))


def restart():
    stop()
    start()


def reload():
    logging.config.dictConfig(settings.LOG_SETTINGS)
    print("Reloading gunicorn... ", end="")
    os.kill(get_pid(gunicorn_pidfile), signal.SIGHUP)
    print(green('OK'))


def process_failed_updates():
    # TODO:
    pass


if __name__ == "__main__":
    command_handlers = {
        'start': start,
        'restart': restart,
        'stop': stop,
        'reload': reload,
        'status': status,
        # 'fix-failed': process_failed_updates(),
    }

    parser = argparse.ArgumentParser()
    parser.add_argument('CMD', help="Available commands:\n{0}".format(
        "|".join([cmd for cmd in command_handlers.keys()])
    ))
    args = parser.parse_args()
    func = command_handlers.get(args.CMD)
    if not func:
        print("Unknown command '%s'" % args.CMD)
        sys.exit(1)
    func()
    print('Done.')
