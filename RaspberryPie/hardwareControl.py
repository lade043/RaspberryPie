#general imports
import time
import datetime

# imports for hardware
import Adafruit_DHT
from picamera import PiCamera
import RPi.GPIO as GPIO

# imports from project
from RaspberryPie.config import config
from RaspberryPie.logger import captScribe

lib = {}

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
            captScribe.warning("Error while reading DHT22 sensor. The received values are: Humidity: {}, Temperature: {}".format(str(humidity), str(temperature)), "MajGenObserver.get_sensorData")
            humidity, temperature = (-1, -274) # if you need any numbers, why don't take impossible ones, to show error
        return humidity, temperature

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

    def collect(self, function_names: list):
        time = datetime.datetime.now()
        for function in function_names:
            data = self.functions[function]()
            self._archive(function, {time: data})


majGenObserver = MajGenObserver()
majGenGPIOController = MajGenGPIOController(config["Hardware"]["pinopen"], config["Hardware"]["pinclose"], config["Timing"]["gpioswitchoff"])
ltGenDataCollector = LtGenDataCollector({"air": majGenObserver.get_sensorData, "picture": majGenObserver.get_picture}, lib)