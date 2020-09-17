# general imports
import logging
import configparser
import os
import time
import numpy as np

# imports for emailprocessing
import imaplib
import email
import datetime
import dropbox
import requests
import socket
import html2text

# imports for hardware
import Adafruit_DHT
from picamera import PiCamera
import RPi.GPIO as GPIO

# imports from project
import RaspberryPie.tasks


config = configparser.RawConfigParser()
config.read("config.cfg") # edit this file for your specific configuration

"""
All classes are ranked in their hierarchy, like this (ranks of the US Marines):
Capt << BGen << MajGen << LtGen << Gen
"""

class CaptScribe:
    def __init__(self, log_info, log_error):
        self.logfile_info = log_info
        self.logfile_error = log_error
        self.loggers = [logging.getLogger("log_info"), logging.getLogger("log_error")]
        self.formatters = [logging.Formatter("%(asctime)s : %(level), %(message)s"), logging.Formatter("%(asctime)s : %(message)s: %(sinfo)")]
        self.handlers = [logging.FileHandler(self.logfile_info, mode='w'), logging.FileHandler(self.logfile_error, mode='w')]
        for i, handler in enumerate(self.handlers):
            handler.setFormatter(self.formatters[i])
        
        for i, logger in self.loggers:
            logger.addHandler(self.handlers[i])
        
        self.loggers[0].level = logging.INFO
        self.loggers[1].level = logging.ERROR
        
    def critical(self, msg, func=""):
        for logger in self.loggers:
            logger.critical(func.upper() + ": " + msg)

    def error(self, msg, func=""):
        for logger in self.loggers:
            logger.error(func.upper() + ": " + msg)
    
    def warning(self, msg, func=""):
        for logger in self.loggers:
            logger.warning(func.upper() + ": " + msg)
    
    def info(self, msg, func=""):
        for logger in self.loggers:
            logger.info(func.upper() + ": " + msg)
    
    def debug(self, msg, func=""):
        for logger in self.loggers:
            logger.debug(func.upper() + ": " + msg)

class MajGenObserver:
    class DictatingMachine: # just a file like object
        def __init__(self):
            self.captured = ""
        def write(self, text):
            self.captured = text
        def __str__(self):
                return str(self.captured)
    
    def get_picture(self):
        camera = PiCamera()
        majGensDictatingMachine = self.DictatingMachine()
        camera.start_preview()
        time.sleep(5) # letting camera adjust to environment (exposure and wb)
        camera.capture(majGensDictatingMachine)
        camera.stop_preview()
        return str(majGensDictatingMachine)
    
    def get_sensorData(self):
        sensor = Adafruit_DHT.DHT22
        pin = int(config["Hardware"]["dhtpin"])
        humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
        if humidity is None or temperature is None:
            captScribe.warning("Error while reading DHT22 sensor. The received values are: Humidity: {}, Temperature: {}".format(humidity, temperature), "MajGenObserver.get_sensorData")
            humidity, temperature = (-1, -274) # if you need any numbers, why don't take impossible ones, to show error
        return humidity, temperature

class MajGenApiTelecom:
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
            MajGenApiTelecom.delete_mail(id)
        
    def __init__(self, email_function, dropbox_function):
        # using functions so in future, the storing can "easily" made more secure (not always stored in memory hopefully)
        self.email_function = email_function
        self.dropbox_function = dropbox_function
        self.mail_config = config["Mail"]

    def upload_dropbox(self, filename, content):
        try:
            dbx = dropbox.Dropbox(self.dropbox_function())
            if type(content) != bytes:
                content = content.encode('utf-8')
            dbx.files_upload(content, filename, mode=dropbox.files.WriteMode.overwrite)
            captScribe.info("Uploaded file: {}".format(filename), "MajGenApiTelecom.upload_dropbox")
        except (dropbox.dropbox.ApiError, dropbox.dropbox.AuthError, dropbox.dropbox.BadInputError,
                dropbox.dropbox.HttpError, dropbox.dropbox.InternalServerError, dropbox.dropbox.PathRootError,
                dropbox.dropbox.RateLimitError, requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout,
                requests.exceptions.Timeout, requests.exceptions.ConnectionError) as dropbox_error:
                    captScribe.error("{} occured, while trying to upload {}.".format(str(dropbox_error), filename), "MajGenApiTelecom.upload_dropbox")

    def get_emails(self):
        mail_box = []
        if not "@" + self.mail_config["url"] in email_function()["address"]:
            add_url = True
        else:
            add_url = False
        try:
            imap = imaplib.IMAP4_SSL(self.mail_config["smtpserver"])
            complete_mail_adress = lambda: self.email_function()["address"] + "@" + self.mail_config["url"] if add_url else self.email_function()["address"]
            imap.login(complete_mail_adress(), self.email_function()["password"])
            imap.select("inbox")

            type, data = imap.search(None, 'ALL')
            ids = data[0]
            for id in reversed(ids.split()):
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
                        captScribe.info("Gotten email: {}".format(str(telegram)), "MajGenApiTelecom.get_emails")
        except (imaplib.IMAP4.error, socket.error) as imap_error:
            captScribe.error("Getting emails failed with: {}.".format(str(imap_error)), "MajGenApiTelecom.get_emails")

        finally:
            try:
                imap.close()
                imap.logout()
            except:
                captScribe.error("Logout of imap failed.", "MajGenApiTelecom.get_emails")

    def delete_mail(self, id):
        if not "@" + self.mail_config["url"] in email_function()["address"]:
            add_url = True
        else:
            add_url = False
        try:
            imap = imaplib.IMAP4_SSL(self.mail_config["smtpserver"])
            complete_mail_adress = lambda: self.email_function()["address"] + "@" + self.mail_config["url"] if add_url else self.email_function()["address"]
            imap.login(complete_mail_adress(), self.email_function()["password"])
            imap.select("inbox")

            imap.store(id, '+FLAGS', '\\DELETED')
            captScribe.info("Deleted email with id {}".format(id), "MajGenApiTelecom.delete_mail")

        except (imaplib.IMAP4.error, socket.error) as imap_error:
            captScribe.error("Getting emails failed with: {}.".format(str(imap_error)), "MajGenApiTelecom.delete_mail")

        finally:
            try:
                imap.expunge()
                imap.close()
                imap.logout()
            except:
                captScribe.error("Logout of imap failed.", "MajGenApiTelecom.delete_mail")

class MajGenGPIOController:
        def __init__(self, pin_open, pin_close, delta_switchOff):
            self.pinOpen = pin_open
            self.pinClose = pin_close
            self.deltaOff = delta_switchOff

            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pinOpen, GPIO.OUT)
            GPIO.setup(self.pinClose, GPIO.OUT)
            GPIO.output(self.pinOpen, GPIO.HIGH)
            GPIO.output(self.pinClose, GPIO.HIGH)
        
        def finalMission(self):
            self.kill()
            GPIO.cleanup()

        def close(self):
            self.kill()
            GPIO.output(self.pinClose, GPIO.LOW)
            GPIO.output(self.pinOpen, GPIO.HIGH)
            captScribe.info("GPIO set to closing", "MajGenGPIOControl.close")

        def open(self):
            self.kill()
            GPIO.output(self.pinClose, GPIO.HIGH)
            GPIO.output(self.pinOpen, GPIO.LOW)
            captScribe.info("GPIO set to opening", "MajGenGPIOControl.open")

        def kill(self):
            GPIO.output(self.pinClose, GPIO.HIGH)
            GPIO.output(self.pinOpen, GPIO.HIGH)
            time.sleep(.5) # waiting, so relay definetly has switched
            captScribe.info("GPIO switched off", "MajGenGPIOControl.kill")

        def delayedSwitchOff(self):
            time.sleep(self.deltaOff)
            self.kill()
            
class LtGenDataCollector:
    def __init__(self, functions: dict, library, schedule_timing=None):
        self.functions = functions
        if not schedule_timing:
            self.schedule_timing = {"air": config["Timing"]["environmentdelta"], "camera": config["Timing"]["picturedelta"]}
        else:
            self.schedule_timing = schedule_timing
        self.schedule = {"air": datetime.datetime.now(), "camera": datetime.datetime.now()}
        self.library = library
        
    def get_schedule(self):
        arr = []
        for event in self.schedule_timing:
            arr.append(self.schedule[event])
        return arr

    def _archive(self, place, data):
        pass

    def collect(self):
        time = datetime.datetime.now()
        for event in self.schedule:
            if time >= self.schedule[event]:
                data = self.functions[event]()
                self._archive(event, {time: data})

class LtGenInterpreter:
    def __init__(self, tasks: list, communicator: MajGenApiTelecom):
        self.tasks = tasks
        self.communicator = communicator
    
    def execute(self):
        messages = self.communicator.get_emails()
        for message in messages:
            for task in self.tasks:
                if task.test(message):
                    task.function()

class GenScheduler:
    def __init__(self, subordinates: list):
        self.subordinates = subordinates
        self.schedule = {}
        self.schedule_delta = {}
        for subordinate in self.subordinates:
            self.schedule[subordinate] = list(datetime.datetime.now())
            self.schedule_delta[subordinate] = list(subordinate.get_schedule())
        self.time = datetime.datetime.now

    def execute(self):
        while True:
            try:
                for subordinate in self.schedule:
                    if self.schedule[subordinate][np.argmin(self.schedule[subordinate])] <= self.time():
                        subordinate.execute()
                        self.schedule[subordinate][np.argmin(self.schedule[subordinate])] += self.schedule_delta[subordinate][np.argmin(self.schedule[subordinate])]
                
                time_list = lambda: [self.schedule[subordinate][np.argmin(self.schedule[subordinate])] for subordinate in self.schedule]
                sleep_duration = time_list()[np.argmin(time_list())]
                time.sleep(sleep_duration)
            except Exception as e:
                captScribe.critical("A not expected error occured: {}".format(str(e)), "GenScheduler.execute")

    def initiate_shutdown(self, reboot=True):
        majGenGPIOController.finalMission()
        reboot_str = lambda: " -r" if reboot else ""
        os.system("shutdown{} 0".format(reboot_str()))

def init():
    lib = {}
    captScribe = CaptScribe(config["File Locations"]["logfile_info"], config["File Locations"]["logfile_error"])
    majGenObserver = MajGenObserver()
    majGenApiTelecom = MajGenApiTelecom(lambda: {"address": config["Secrets"]["emailaddress"], "password": config["Secrets"]["emailpassword"]}, lambda: config["Secrets"]["dropboxtoken"])
    majGenGPIOController = MajGenGPIOController(config["Hardware"]["pinopen"], config["Hardware"]["pinclose"], config["Timing"]["gpioswitchoff"])
    ltGenDataCollector = LtGenDataCollector({"air": majGenObserver.get_sensorData(), "picture": majGenObserver.get_picture()}, lib)
    ltGenInterpreter = LtGenInterpreter(RaspberryPie.tasks.tasks, majGenApiTelecom)


init()
