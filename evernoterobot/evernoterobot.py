import logging

from bot.dealer import EvernoteDealer
import settings


if __name__ == "__main__":
    logging.config.dictConfig(settings.LOG_SETTINGS)
    dealer = EvernoteDealer()
    dealer.run()
