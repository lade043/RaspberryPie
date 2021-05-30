from flask import Flask, render_template, make_response
import json
import signal

import RaspberryPie.flaskAddons as fa

app = Flask(__name__)
@app.route("/")
def index():
    latestAirData = fa.getLatestAirData()
    latestPicture = fa.getLatestPicture()
    return render_template("index.html", 
                           WeatherTime = latestAirData["time_string"],
                           temp = latestAirData["temperature"],
                           humi = latestAirData["humidity"],
                           weather_urls=fa.weatherUrls(),
                           PictureTime = latestPicture["time_string"],
                           picture = latestPicture["picture"])


@app.route("/data/<start>/<end>/")
def airData(start, end):
    data = fa.getDataRangeAir(int(start), int(end))
    return json.dumps(data)

@app.route("/picture/<time>/")
def picture(time):
    if time == "latest":
        return json.dumps(fa.getLatestPicture())
    else:
        return json.dumps(fa.getLatestPicture(int(time)))

@app.route("/initiate/picture/")
def inititatePicture():
    pass

@app.route("/inititate/air/")
def ininitiateAir():
    pass

@app.route("/initiate/gpio/<state>/")
def ininitisteGPIO(state):
    try:
        state = int(state)
    except:
        state = state

    if state == "open" or state == 0:
        return "Opened", 200
    elif state == "close" or state == 1:
        return "Closed", 200
    return "state not found", 404
    

@app.route("/initiate/shutdown/")
def initiateShutdown():
    pass

@app.route("/lastChange/")
def lastChange():
    return str(fa.lastChange())