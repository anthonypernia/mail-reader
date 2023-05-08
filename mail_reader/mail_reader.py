""" MailReader class to read emails from a mail server """
import email
import imaplib
import logging
import os
from email.header import decode_header
from email.message import Message

import mail_reader.utils.constants as c

logging.basicConfig(level=logging.INFO)


class MailReader:
    """MailReader class to read emails from a mail server"""

    def __init__(self, config: dict):
        """MailReader class to read emails from a mail server

        Args:
            config (dict): dictionary with the following keys:
                user (str): user of the mail server
                password (str): password of the mail server
                mail (str): mail of the mail server
                host (str): host of the mail server
                port (int): port of the mail server
                ssl (bool): ssl of the mail server
                path_attachments (str): path to save the attachments

        Raises:
            Exception: if any of the parameters is not provided
        """
        self.user = config.get(c.USER, None)
        self.password = config.get(c.PASSWORD, None)
        self.mail = config.get(c.MAIL, c.DEFAULT_MAIL)
        self.host = config.get(c.HOST, c.DEFAULT_HOST)
        self.port = config.get(c.PORT, c.DEFAULT_PORT)
        self.ssl = config.get(c.SSL, None)
        self.path_attachments = config.get(
            c.PATH_ATTACHMENTS, c.DEFAULT_PATH_ATTACHMENTS
        )
        if not self.user and not self.password:
            raise Exception(  # pylint: disable= broad-exception-raised
                "User and password are required"
            )

    def clean_text(self, text: str) -> str:
        """Clean text to use it as a folder name
        Args:
            text (str): text to clean
        Returns:
            str: cleaned text
        """
        return "".join(c if c.isalnum() else "_" for c in text)

    def obtain_header(self, msg: Message) -> tuple:
        """Obtain the header of the email

        Args:
            msg (Message): email message

        Returns:
            tuple: subject and from of the email
        """
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(str(encoding))
        mail_from, encoding = decode_header(msg.get("From"))[0]
        if isinstance(mail_from, bytes):
            mail_from = mail_from.decode(encoding)
        logging.info(f"Subject: {subject}")
        logging.info(f"From: {mail_from}")
        return subject, mail_from

    def download_attachment(self, part: Message, subject: str) -> None:
        """Download attachments from the email
        Args:
            part (Message): part of the email
            subject (str): subject of the email to be used as a folder name
        """
        filename = part.get_filename()
        if filename:
            folder_name = self.clean_text(subject)
            if not os.path.isdir(folder_name):
                if not os.path.isdir(self.path_attachments):
                    os.mkdir(self.path_attachments)
                path = f"{self.path_attachments}/{folder_name}"
                if not os.path.isdir(path):
                    os.mkdir(path)
                filepath = os.path.join(path, filename)
                open(filepath, "wb").write(part.get_payload(decode=True))

    def conn_and_auth(self) -> imaplib.IMAP4_SSL:
        """Connect and authenticate to the mail server

        Returns:
            imaplib.IMAP4_SSL: imap connection
        """
        imap = imaplib.IMAP4_SSL(self.host, self.port)
        imap.login(self.user, self.password)
        return imap

    def multipart_process(self, part: Message, subject: str) -> None:
        """Process the multipart of the email
        Args:
            part (Message): part of the email
            subject (str): subject of the email to be used as a folder name
        """
        content_type = part.get_content_type()
        content_disposition = str(part.get("Content-Disposition"))
        try:
            body = part.get_payload(decode=True).decode()
        except Exception:  # pylint: disable= broad-exception-caught
            pass
        if content_type == "text/plain" and "attachment" not in content_disposition:
            logging.info(body)
        elif "attachment" in content_disposition:
            self.download_attachment(part, subject)

    def body_process(self, msg: Message) -> None:
        """Process the body of the email
        Args:
            msg (Message): email message
        """
        content_type = msg.get_content_type()
        body = msg.get_payload(decode=True).decode()
        if content_type == "text/plain":
            logging.info(body)

    def search_messages(
        self, imap: imaplib.IMAP4_SSL, search_criteria: str = "ALL"
    ) -> list:
        """Search messages in the inbox by criteria
        Example:
            search_messages(imap, '(SENTSINCE 06-May-2023)') to search messages since 06-May-2023
            search_messages(imap, '(FROM "anthonyperniah@gmail.com")' to search messages from
            search_messages(imap, '(SUBJECT "Hello")' to search messages with subject Hello
            search_messages(imap, '(BODY "Hello")' to search messages with body Hello
            search_messages(imap, '(ANSWERED)' to search messages that have been answered
        Args:
            imap (imaplib.IMAP4_SSL): imap connection
            search_criteria (str, optional): search criteria. Defaults to "ALL".
        Returns:
            list: list of messages according to the search criteria
        """
        status, messages = imap.search(None, search_criteria)
        if status != "OK":
            logging.warning("No messages found!")
            return []
        messages = messages[0].split(b" ")
        return messages

    def process(self) -> None:
        """Process the emails in the inbox"""
        imap = self.conn_and_auth()
        imap.select("INBOX")
        messages = self.search_messages(imap)
        for i in messages:
            _, msg = imap.fetch(i, "(RFC822)")
            for response in msg:
                if isinstance(response, tuple):
                    msg = email.message_from_bytes(
                        response[1]  # pylint: disable=unsubscriptable-object
                    )
                    subject, _ = self.obtain_header(msg)
                    if msg.is_multipart():
                        for part in msg.walk():
                            self.multipart_process(part, subject)
                    else:
                        self.body_process(msg)
                    print("=" * 100)
        imap.close()
