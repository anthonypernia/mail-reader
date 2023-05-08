""" Main file to run the mail reader """
import mail_reader.utils.constants as c
from mail_reader.mail_reader import MailReader
from mail_reader.utils.settings import get_config

if __name__ == "__main__":
    config_mail_reader = get_config(c.MAIL_READER_TAG)
    mail_reader = MailReader(config_mail_reader)
    mail_reader.process()
    print("Done")
