#general imports
from RaspberryPie.logger import CaptScribe
import time
import datetime

# imports for hardware
import Adafruit_DHT
from picamera import PiCamera
import RPi.GPIO as GPIO

# imports from project
import RaspberryPie.config as config
import RaspberryPie.dataHandling as dataHandling 

captScribe = None

def _set_captScribe(_captScribe):
    global captScribe
    captScribe = _captScribe
    dataHandling._set_captScribe(_captScribe)


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
                return self.captured
    
    def __init__(self, schedule_timing):
        self.schedule_timing = schedule_timing
    
    def get_schedule(self):
        return self.schedule_timing
        
class MajGenAirChecker(MajGenObserver):
    def __init__(self, schedule_timing=None):
        if not schedule_timing:
            schedule_timing = config.config["Timing"]["environmentdelta"]
        super().__init__(schedule_timing)

    def execute():
        sensor = Adafruit_DHT.DHT22
        pin = int(config.config["Hardware"]["dhtpin"])
        humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
        if humidity is None or temperature is None:
            captScribe.warning("Error while reading DHT22 sensor. The received values are: Humidity: {}, Temperature: {}".format(str(humidity), str(temperature)), "MajGenObserver.get_sensorData")
            humidity, temperature = (-1, -274) # if you need any numbers, why don't take impossible ones, to show error
        return humidity, temperature

class MajGenVisualObserver(MajGenObserver):
    def __init__(self, schedule_timing=None):
        if not schedule_timing:
            schedule_timing = config.config["Timing"]["picturedelta"]
        super().__init__(schedule_timing)

    def execute():
        camera = PiCamera()
        majGensDictatingMachine = super.DictatingMachine()
        camera.start_preview()
        time.sleep(5) # letting camera adjust to environment (exposure and wb)
        camera.capture(majGensDictatingMachine, format="jpeg")
        camera.stop_preview()
        return str(majGensDictatingMachine)

class MajGenAirRecoder(MajGenAirChecker):
    def __init__(self, dataCollector, schedule_timing=None):
        self.dataCollector = dataCollector
        super().__init__(schedule_timing=schedule_timing)
    
    def execute(self):
        data = super.execute()
        self.dataCollector.recordeAir({"air": (str(datetime.datetime.now()), data)})

class MajGenVisualRecoder(MajGenVisualObserver):
    def __init__(self, dataCollector, schedule_timing=None):
        self.dataCollector = dataCollector
        super().__init__(schedule_timing=schedule_timing)
    
    def execute(self):
        data = super.execute()
        self.dataCollector.recordePicture({"picture": (str(datetime.datetime.now()), data)})



majGenGPIOController = MajGenGPIOController(config.config["Hardware"]["pinopen"], config.config["Hardware"]["pinclose"], config.config["Timing"]["gpioswitchoff"])
majGenVisualObserver = MajGenVisualObserver()
majGenAirChecker = MajGenAirChecker()
majGenAirRecoder = MajGenAirRecoder(dataHandling.bGenSecretary)
majGenVisualRecoder = MajGenVisualRecoder(dataHandling.bGenSecretary)
