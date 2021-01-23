import datetime
from RaspberryPie.config import config
from RaspberryPie.dataHandling import bGenSecretary

def time(): return ""

def weatherUrls(): return [config["WeatherUrls"][i] for i in config["WeatherUrls"]]

def getLatestAirData(): return bGenSecretary.fetchAir()

def getLatestPicture(): return bGenSecretary.fetchAir()

def getDataRangeAir(start: int, end: int): return bGenSecretary.fetchAir(datetime.datetime.utcfromtimestamp(end), datetime.datetime.utcfromtimestamp(start))

def getDataRangePictures(start: int, end: int): return bGenSecretary.fetchPicture(datetime.datetime.utcfromtimestamp(end), datetime.datetime.utcfromtimestamp(start))

def getSingleAirData(time: int): return bGenSecretary.fetchAir(datetime.datetime.utcfromtimestamp(time))

def getSinglePicture(time: int): return bGenSecretary.fetchPicture(datetime.datetime.utcfromtimestamp(time))