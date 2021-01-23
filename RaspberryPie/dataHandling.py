#general imports
import datetime
import sqlite3
import base64

# imports from Project
from RaspberryPie.logger import captScribe
from RaspberryPie.config import config


class BGenSecretary:
    def __init__(self, database_path, image_path):
        self.database = database_path
        self.image_path = image_path
    
    
    def _record(self, data: dict):
        connection = None
        try:
            connection = sqlite3.connect(self.database)
            cursor = connection.cursor()
            for typ in data:
                time = datetime.datetime.now()
                data[typ]["time_string"] = str(time)
                data[typ]["unix_time"] = int(time.timestamp())
                command = "INSERT INTO {} ({}) VALUES ({})".format(typ, str([i for i in data[typ]])[1:-1], str([data[typ][i] for i in data[typ]])[1:-1])
                cursor.execute(command)
                captScribe.info("Inserted data into table '{}' of database".format(typ), "BGenSecretary._record")
            connection.commit()
        except sqlite3.Error as e:
            captScribe.error(str(e), "BGenSecretary._record")
        finally:
            if connection is sqlite3.Connection:
                connection.close()
    
    def recordPicture(self, picture: bytes):
        with open("{}/{}.jpg".format(self.image_path, str(datetime.datetime.now())), "w") as f:
            f.write(picture)
        
        self._record({"picture": {"picture": base64.encodebytes(picture).decode('ascii').replace("\n", "")}})
    
    def recordAir(self, data):
        self._record({"air": {"temperature": data[0], "humidity": data[1]}})
    
    def _fetchSingle(self, table, time: datetime.datetime):
        unix_time = int(time.timestamp())
        command = "SELECT * FROM {} ORDER BY ABS(unix_time - {}) ASC LIMIT 1".format(table, unix_time)
        connection, entry = None
        try:
            connection = sqlite3.connect(self.database)
            cursor = connection.cursor()
            cursor.execute(command)
            entry = cursor.fetchone()
            captScribe.info("Fetched entry for {} from {}".format(str(unix_time), table), "BGenSecretary._fetchSingle")
        except sqlite3.Error as e:
            captScribe.error(str(e), "BGenSecretary._fetchSingle")
        finally:
            if connection is sqlite3.Connection:
                connection.close()
        return tuple(entry) if entry is sqlite3.Row else None
    
    def _fetchMultiple(self, table, end:datetime.datetime, start: datetime.datetime):
        unix_time_end = int(end.timestamp())
        unix_time_start = int(start.timestamp())
        command = "SELECT * FROM {} WHERE unix_time BETWEEN {} AND {}".format(unix_time_start, unix_time_end)
        connection, entries = None
        try:
            connection = sqlite3.connect(self.database)
            cursor = connection.cursor()
            cursor.execute(command)
            entries = cursor.fetchall()
            captScribe.info("Fetched entries for {} from {}".format(str((unix_time_start, unix_time_end)), table), "BGenSecretary._fetchSingle")
        except sqlite3.Error as e:
            captScribe.error(str(e), "BGenSecretary._fetchSingle")
        finally:
            if connection is sqlite3.Connection:
                connection.close()
        return [tuple(entry) for entry in entries] if entries is not None else None
    
    def fetchAir(self, time=datetime.datetime.now(), start_time=None): # time is either one point or the end point if start is given
        if not start_time:
            entry = self._fetchSingle("air", time)
            return {"unix_time": entry[0], "time_string": entry[1], "temperature": entry[2], "humidity": entry[3]}
        else:
            entries = self._fetchMultiple("air", time, start_time)
            return {"unix_time": [entry[0] for entry in entries], "time_string": [entry[1] for entry in entries], "temperature": [entry[2] for entry in entries], "humidity": [entry[3] for entry in entries]}
        
    def fetchPicture(self, time=datetime.datetime.now(), start_time=None):
        if not start_time:
            entry = self._fetchSingle("picture", time)
            return {"unix_time": entry[0], "time_string": entry[1], "picture": entry[2]}
        else:
            entries = self._fetchMultiple("picture", time, start_time)
            return {"unix_time": [entry[0] for entry in entries], "time_string": [entry[1] for entry in entries], "picture": [entry[2] for entry in entries]}


bGenSecretary = BGenSecretary(config["File Locations"]["database_file"], config["File Locations"],["image_path"])