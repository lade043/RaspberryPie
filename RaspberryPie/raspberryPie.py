# general imports
import os
import time
import numpy as np
import datetime

"""
All classes are ranked in their hierarchy, like this (ranks of the US Marines):
Capt << BGen << MajGen << LtGen << Gen
"""
# imports from project
from RaspberryPie.tasks import Task
from RaspberryPie.hardwareControl import majGenObserver, majGenGPIOController, ltGenDataCollector
from RaspberryPie.config import config
from RaspberryPie.logger import captScribe
from RaspberryPie.internetHandling import majGenApiCom, MajGenApiCom

ltGenInterpreter, genScheduler = None

tasks = [
    Task(majGenGPIOController.open, lambda msg: 1 if ("auf" == msg.subject.lower() or "open" == msg.subject.lower()) else 0),
    Task(majGenGPIOController.close, lambda msg: 1 if ("zu" == msg.subject.lower() or "close" == msg.subject.lower()) else 0)
]

class LtGenInterpreter:
    def __init__(self, tasks: list, communicator: MajGenApiCom):
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
    global ltGenInterpreter, genScheduler
    ltGenInterpreter = LtGenInterpreter(tasks, majGenApiCom)
    genScheduler = GenScheduler((majGenApiCom, ltGenDataCollector))


init()
