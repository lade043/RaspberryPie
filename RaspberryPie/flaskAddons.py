import datetime
import RaspberryPie.config as config
import RaspberryPie.dataHandling as dataHandling

def time(): return ""

def weatherUrls(): return [config.config["WeatherUrls"][i] for i in config.config["WeatherUrls"]]

def getLatestAirData(): return dataHandling.bGenSecretary.fetchAir()

def getLatestPicture(): return dataHandling.bGenSecretary.fetchAir()

def getDataRangeAir(start: int, end: int): return dataHandling.bGenSecretary.fetchAir(datetime.datetime.utcfromtimestamp(end), datetime.datetime.utcfromtimestamp(start))

def getDataRangePictures(start: int, end: int): return dataHandling.bGenSecretary.fetchPicture(datetime.datetime.utcfromtimestamp(end), datetime.datetime.utcfromtimestamp(start))

def getSingleAirData(time: int): return dataHandling.bGenSecretary.fetchAir(datetime.datetime.utcfromtimestamp(time))

def getSinglePicture(time: int): return dataHandling.bGenSecretary.fetchPicture(datetime.datetime.utcfromtimestamp(time))

def lastChange(): 
    with open(config.config["FileLocations"]["lastChangeFile"], 'r') as f: 
        return int(f.read())