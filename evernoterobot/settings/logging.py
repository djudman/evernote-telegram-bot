import logging
from logging.handlers import SMTPHandler
import smtplib


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
            logger = logging.getLogger('myfeed.file')
            logger.error(traceback.format_exc())
            # self.handleError(record)

    def getSubject(self, record):
        if record.exc_info:
            return "[%s] %s" % (record.levelname, str(record.exc_info[1]))
        return '[%s] %s' % (record.levelname, record.message)
