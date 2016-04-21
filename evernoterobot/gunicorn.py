#!/usr/bin/env python

# Add this line to .bash_profile to enable bash completion
# complete -o default -C '<path>/web/gunicorn.py bash_complete' gunicorn.py

import sys
import os
import time
import signal
import gunicorn_config as config


def green(s):
    return "\033[92m%s\033[0m" % s


def red(s):
    return "\033[91m%s\033[0m" % s


def check_pidfile(pidfile):
    """ Check For the existence of a unix pid. """
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


def start():
    if not os.path.exists(config.pidfile):
        print('Starting... ', end="")
        os.system('gunicorn --config gunicorn_config.py %s' % config.app_name)
        time.sleep(1)
        if check_pidfile(config.pidfile):
            print(green('OK'))
        else:
            print(red('FAILED'))
    else:
        print("Gunicorn already running")


def stop():
    print("Stopping... ", end="")
    os.kill(get_pid(), signal.SIGTERM)
    os.unlink(config.pidfile)
    print(green('OK'))


def reload():
    print("Reloading... ", end="")
    os.kill(get_pid(), signal.SIGHUP)
    print(green('OK'))


def restart():
    stop()
    start()


def kill():
    print("Killing... ", end="")
    os.kill(get_pid(), signal.SIGINT)
    os.unlink(config.pidfile)
    print(green('OK'))


def status():
    if check_pidfile(config.pidfile):
        print(green('Started'))
    else:
        print(red('Stopped'))


def get_pid():
    try:
        with open(config.pidfile) as f:
            pid = int(f.read())
            return pid
    except FileNotFoundError:
        raise Exception('Gunicorn is not running')


def bash_complete(params):
    print("\n".join(params))


def print_help():
    print("Usage: %s start|stop|status|reload|restart|kill" % sys.argv[0])


handlers_map = {
    'start': start,
    'stop': stop,
    'reload': reload,
    'restart': restart,
    'kill': kill,
    'status': status,
}

if len(sys.argv) > 1:
    cmd = sys.argv[1].lower()
    if cmd == 'bash_complete':
        bash_complete(handlers_map.keys())
    else:
        handler = handlers_map.get(cmd)
        if handler:
            try:
                handler()
            except Exception as e:
                print(red(str(e)))
        else:
            print_help()
else:
    print_help()
