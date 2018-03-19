from flask import Flask, jsonify, request
from pysqlite2 import dbapi2 as sqlite
from datetime import datetime

DBconnection = sqlite.connect("appointments.db")
DB = DBconnection.cursor()

createSQL = "CREATE TABLE IF NOT EXISTS `appointments` (`appointment_time` INT NOT NULL UNIQUE);"
createDescSQL = "CREATE VIRTUAL TABLE IF NOT EXISTS `appointment_desc` USING FTS4"
viewSQL = "CREATE VIEW IF NOT EXISTS `appointments_all` AS SELECT `appointments`.rowid AS `appointment_id`, `appointment_time`, content AS `appointment_desc` FROM `appointments` JOIN `appointment_desc` ON `appointments`.rowid = `appointment_desc`.rowid;"
insertSQL1 = "INSERT INTO appointments (`appointment_time`) VALUES (?);"
insertSQL2 = "INSERT INTO appointment_desc (`rowid`, `content`) VALUES (last_insert_rowid(), ?);"
fetchAllSQL = "SELECT datetime( `appointment_time`, 'unixepoch' ) AS `appointment_time`, `appointment_desc` FROM appointments_all WHERE `appointment_time` > ? ORDER BY `appointment_time` ASC LIMIT 100;";
searchSQL = "SELECT datetime( `appointment_time`, 'unixepoch' ) AS `appointment_time`, `appointment_desc` FROM appointments_all WHERE `appointment_time` > ? AND `appointment_desc` MATCH ? ORDER BY `appointment_time` ASC LIMIT 100;"
DB.execute(createSQL)
DB.execute(createDescSQL)
DB.execute(viewSQL)

app = Flask(__name__)


@app.route("/")
def main():
    html = open("index.html").read(-1)
    return html


app.add_url_rule('/index', 'index', main)


@app.route("/new-appointment", methods=['POST', 'GET'])
def createAppointment():
    data = request.form
    try:
        if data['date'] == "":
            return main()
        if data['desc'] == "":
            return main()
        if data['time'] == "":
            return main()
    except:
        return main()

    timestamp = data['date'] + " " + data['time']

    try:
        unixTimestamp = totimestamp(datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S"))
    except ValueError:
        return main()

    DB.execute(insertSQL1, [str(unixTimestamp)])
    DB.execute(insertSQL2, [str(data['desc'])])
    DBconnection.commit()

    return main()


@app.route("/get-appointments-ajax", methods=['GET', 'POST'])
def getAppointments():
    data = request.values

    unixNow = str(totimestamp(datetime.now()))
    try:
        data['search']
    except:
        DB.execute(fetchAllSQL, [unixNow])
        results = DB.fetchall()
    else:
        DB.execute(searchSQL, [unixNow, data['search']])
        results = DB.fetchall()

    return jsonify(results)


def totimestamp(dt, epoch=datetime(1970, 1, 1)):
    td = dt - epoch
    return (td.microseconds + (td.seconds + td.days * 86400) * 10 ** 6) / 10 ** 6


if __name__ == "__main__":
    app.run()
