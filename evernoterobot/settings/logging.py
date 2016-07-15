from os.path import join

import logging
from logging.handlers import SMTPHandler
import smtplib

from .base import LOGS_DIR, PROJECT_NAME, SMTP


class SslSMTPHandler(SMTPHandler):
    def emit(self, record):
        """
        Emit a record.

        Format the record and send it to the specified addressees.
        """
        try:
            try:
                from email.utils import formatdate
            except ImportError:
                formatdate = self.date_time
            port = self.mailport
            if not port:
                port = smtplib.SMTP_PORT
            smtp = smtplib.SMTP_SSL(self.mailhost, port, timeout=1)
            msg = self.format(record)
            subject = '[%s] %s' % (record.levelname, record.message)
            msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\nDate: %s\r\n\r\n%s" % (
                            self.fromaddr,
                            ",".join(self.toaddrs),
                            self.getSubject(record),
                            formatdate(), msg)
            if self.username:
                # smtp.ehlo() # for tls add this line
                # smtp.starttls() # for tls add this line
                # smtp.ehlo() # for tls add this line
                smtp.login(self.username, self.password)
            smtp.sendmail(self.fromaddr, self.toaddrs, msg)
            smtp.quit()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            import traceback
            logger = logging.getLogger()
            logger.error(traceback.format_exc())
            # self.handleError(record)

    def getSubject(self, record):
        if record.exc_info:
            return "[%s] %s" % (record.levelname, str(record.exc_info[1]))
        return '[%s] %s' % (record.levelname, record.message)


LOG_SETTINGS = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'default': {
            'format': '%(asctime)s - PID:%(process)d - %(levelname)s - %(message)s (%(pathname)s:%(lineno)d)',
        },
    },

    'handlers': {
        'stdout': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
        'accessfile': {
            'class': 'logging.FileHandler',
            'filename': join(LOGS_DIR, 'access.log')
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': join(LOGS_DIR, '%s.log' % PROJECT_NAME),
            'formatter': 'default',
        },
        'dealer_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': join(LOGS_DIR, 'dealer.log'),
            'formatter': 'default',
        },
        'downloader_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': join(LOGS_DIR, 'downloader.log'),
            'formatter': 'default',
        },
        'email': {
            'level': 'ERROR',
            'class': 'settings.logging.SslSMTPHandler',
            'mailhost': (SMTP['host'], SMTP['port']),
            'fromaddr': SMTP['email'],
            'toaddrs': [SMTP['email']],
            'subject': '',
            'credentials': (SMTP['user'], SMTP['password']),
            'secure': (),
        },
    },

    'loggers': {
        'aiohttp.access': {
            'level': 'INFO',
            'handlers': ['accessfile'],
            'propagate': False,
        },
        'aiohttp.server': {
            'level': 'INFO',
            'handlers': ['file', 'email'],
            'propagate': False,
        },
        'gunicorn.access': {
            'level': 'INFO',
            'handlers': ['accessfile'],
            'propagate': False,
        },
        'gunicorn.error': {
            'level': 'INFO',
            'handlers': ['file', 'email'],
            'propagate': False,
        },
        'dealer': {
            'level': 'DEBUG',
            'handlers': ['dealer_file', 'email'],
            'propagate': True,
        },
        'downloader': {
            'level': 'DEBUG',
            'handlers': ['downloader_file', 'stdout'],
            'propagate': True,
        },
        '': {
            'level': 'DEBUG',
            'handlers': ['file'],
            'propagate': True,
        },
    },
}
