import argparse
import sys
from os.path import realpath, dirname, join

sys.path.insert(1, realpath(dirname(__file__)))

from daemons.dealer import EvernoteDealer


def dealer_pidfile():
    return join(realpath(dirname(__file__)), 'dealer.pid')


def start_dealer():
    dealer = EvernoteDealer(dealer_pidfile())
    dealer.start()


def stop_dealer():
    dealer = EvernoteDealer(dealer_pidfile())
    dealer.stop()


handlers_map = {
    'start': start_dealer,
    'stop': stop_dealer,
}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        handler = handlers_map.get(cmd)
        if handler:
            try:
                handler()
            except Exception as e:
                print(str(e))
        else:
            print('Help must be here')
