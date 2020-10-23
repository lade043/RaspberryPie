from flask import Flask, render_template, make_response
import json

app = Flask(__name__)
@app.route("/")
def index():
    pass
@app.route("/data/<start>/<end>/")
def functionName(start, end):
    data = {}
    db_entries = getEnvironment(int(start), int(end))
    data["labels"] = db_entries["temperature"][0]
    data["temp"] = db_entries["temperature"][1]
    data["humi"] = db_entries["humidity"][1]
    return json.dumps(data)