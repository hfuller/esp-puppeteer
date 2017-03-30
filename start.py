from __future__ import print_function
from flask import Flask, jsonify, redirect, request, render_template
import sqlite3
import json

app = Flask(__name__)
app_name = "ESP Puppeteer"

@app.route('/')
def redir():
    return redirect("/devices")

@app.route('/devices')
def render_devices():
    return render_template('table.html', app_name=app_name, title="Devices")

@app.route('/<firmware>.ino.<platform>.bin')
def update_check(firmware, platform):
    print("firmware:", firmware, "platform:", platform)
    print("environ:", request.environ)
    
    if request.environ.get('HTTP_USER_AGENT') != 'ESP8266-http-Update':
        return "You're not an ESP!", 403

    mac = request.environ.get('HTTP_X_ESP8266_AP_MAC')
    ip = request.environ.get('HTTP_X_FORWARDED_FOR') #request.remote_addr
    version_obj = json.loads(request.environ.get('HTTP_X_ESP8266_VERSION'))
    print("device sent version json object:", version_obj)
    version = version_obj['version']
    name = version_obj['name']
    print("device", name, "is at version", version)

    cur = db.cursor()

    cur.execute('''SELECT id FROM firmwares WHERE name = ?''', [firmware])
    if cur.fetchone() == None:
        print("Adding firmware", firmware)
        cur.execute('''INSERT INTO firmwares(name) VALUES(?)''', [firmware])

    cur.execute('''SELECT id FROM platforms WHERE name = ?''', [platform])
    if cur.fetchone() == None:
        print("Adding platform", platform)
        cur.execute('''INSERT INTO platforms(name) VALUES(?)''', [platform])

    db.commit()

    cur.execute(
            '''
            UPDATE devices SET
                ip = ?,
                seen_timestamp = datetime('now'),
                firmware_id = (SELECT id FROM firmwares WHERE name = ?),
                platform_id = (SELECT id FROM platforms WHERE name = ?),
                version = ?,
                name = ?
            WHERE mac = ?
            ''',
            [ip, firmware, platform, version, name, mac]
    )
    print("update:", cur.rowcount)
    if cur.rowcount < 1:
        print("Adding device", mac)
        cur.execute(
                '''
                INSERT INTO devices(mac, ip, seen_timestamp, firmware_id, name)
                VALUES(?, ?, datetime('now'), (SELECT id FROM firmwares WHERE name = ?), ?)
                ''',
                [mac, ip, firmware, name]
        )
        #We intentionally did not set the version, because if it's the first time this device has showed up, then we want to allow the user to select a train first. Basically we are ensuring that the first time a device phones home, it will not download an update.

    db.commit()

    return "", 304

if __name__ == "__main__":
    print("Starting DB")
    db = sqlite3.connect('esp-puppeteer.sqlite3')

    #app.debug = True
    app.run(port=3777)

