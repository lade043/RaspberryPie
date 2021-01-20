#general imports
import datetime
import sqlite3

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
    
    def recordPicture(self, picture):
        with open("{}/{}.jpg".format(self.image_path, str(datetime.datetime.now())), "w") as f:
            f.write(picture)
        
        self._record({"picture": {"picture": picture}})
    
    def recordAir(self, data):
        self._record({"air": {"temperature": data[0], "humidity": data[1]}})

bGenSecretary = BGenSecretary(config["File Locations"]["database_file"], config["File Locations"],["image_path"])