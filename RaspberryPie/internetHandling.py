import dropbox
import requests
import socket
import html2text
import imaplib
import email
import datetime


from RaspberryPie.logger import captScribe
from RaspberryPie.config import config

class MajGenApiCom:
    class Telegram:
        def __init__(self, id,  subject, sender, time, message):
            self.id = id
            self.subject = subject
            self.sender = sender
            self.time = time
            self.message = message
        def __str__(self):
                return "({}){}: {} at {}: {}".format(self.id, self.sender, self.subject, self.time, self.message)
        def delete(self):
            MajGenApiCom.delete_mail(id)
        
    def __init__(self, email, dropbox):
        # using functions so in future, the storing can "easily" made more secure (not always stored in memory hopefully)
        self.email = email
        self.dropbox = dropbox
        self.mail_config = config["Mail"]

    def upload_dropbox(self, filename, content):
        try:
            dbx = dropbox.Dropbox(self.dropbox)
            if type(content) != bytes:
                content = content.encode('utf-8')
            dbx.files_upload(content, filename, mode=dropbox.files.WriteMode.overwrite)
            captScribe.info("Uploaded file: {}".format(filename), "MajGenApiCom.upload_dropbox")
        except (dropbox.dropbox.ApiError, dropbox.dropbox.AuthError, dropbox.dropbox.BadInputError,
                dropbox.dropbox.HttpError, dropbox.dropbox.InternalServerError, dropbox.dropbox.PathRootError,
                dropbox.dropbox.RateLimitError, requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout,
                requests.exceptions.Timeout, requests.exceptions.ConnectionError) as dropbox_error:
                    captScribe.error("{} occured, while trying to upload {}.".format(str(dropbox_error), filename), "MajGenApiCom.upload_dropbox")

    def get_emails(self):
        mail_box = []
        imap = None

        if not "@" + self.mail_config["url"] in self.email["address"]:
            add_url = True
        else:
            add_url = False
        try:
            imap = imaplib.IMAP4_SSL(self.mail_config["smtpserver"])
            complete_mail_adress = lambda: self.email["address"] + "@" + self.mail_config["url"] if add_url else self.email["address"]
            imap.login(complete_mail_adress(), self.email["password"])
            imap.select("inbox")

            type, data = imap.search(None, 'ALL')
            ids = data[0]
            for id in reversed(ids.split()):
                text = ""
                typ, content = imap.fetch(id, '(RFC822)')

                for part in content:
                    if isinstance(part, tuple):
                        message = email.message_from_string(part[1].decode('utf-8'))
                        # credit for next 7 lines: https://stackoverflow.com/users/1105597/jury
                        for part in message.walk():
                            if part.get_content_maintype() == 'multipart':
                                continue
                            if part.get_content_maintype() == 'text':
                                # reading as HTML (not plain text)
                                _html = part.get_payload(decode = True)
                                text = html2text.html2text(_html)

                        telegram = self.Telegram(id, email.Header.decode_header(message["Subject"])[0][0],
                                              email.utils.parseaddr(message['From']),
                                              datetime.fromtimestamp(email.utils.mktime_tz(email.utils.parsedate_tz(message['Date']))), 
                                              text)
                        mail_box.append(telegram)
                        captScribe.info("Gotten email: {}".format(str(telegram)), "MajGenApiCom.get_emails")
        except (imaplib.IMAP4.error, socket.error) as imap_error:
            captScribe.error("Getting emails failed with: {}.".format(str(imap_error)), "MajGenApiCom.get_emails")

        finally:
            try:
                if imap:
                    imap.close()
                    imap.logout()
            except:
                captScribe.error("Logout of imap failed.", "MajGenApiCom.get_emails")

    def delete_mail(self, id):
        imap = None

        if not "@" + self.mail_config["url"] in self.email["address"]:
            add_url = True
        else:
            add_url = False
        try:
            imap = imaplib.IMAP4_SSL(self.mail_config["smtpserver"])
            complete_mail_adress = lambda: self.email["address"] + "@" + self.mail_config["url"] if add_url else self.email["address"]
            imap.login(complete_mail_adress(), self.email["password"])
            imap.select("inbox")

            imap.store(id, '+FLAGS', '\\DELETED')
            captScribe.info("Deleted email with id {}".format(id), "MajGenApiCom.delete_mail")

        except (imaplib.IMAP4.error, socket.error) as imap_error:
            captScribe.error("Getting emails failed with: {}.".format(str(imap_error)), "MajGenApiCom.delete_mail")

        finally:
            try:
                imap.expunge()
                imap.close()
                imap.logout()
            except:
                captScribe.error("Logout of imap failed.", "MajGenApiCom.delete_mail")

                
majGenApiCom = MajGenApiCom({"address": config["Secrets"]["emailaddress"], "password": config["Secrets"]["emailpassword"]}, config["Secrets"]["dropboxtoken"])