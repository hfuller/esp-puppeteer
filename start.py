from __future__ import print_function
from flask import Flask, jsonify, redirect, request
import sqlite3

app = Flask(__name__)

@app.route('/')
def redir():
    return redirect("/static/index.html")

@app.route('/<firmware>.ino.<platform>.bin')
def update_check(firmware, platform):
    print("firmware:", firmware, "platform:", platform)
    print(request.environ)
    
    if request.environ.get('HTTP_USER_AGENT') != 'ESP8266-http-Update':
        return "You're not an ESP!", 403

    mac = request.environ.get('HTTP_X_ESP8266_AP_MAC')
    ip = request.environ.get('HTTP_X_FORWARDED_FOR') #request.remote_addr

    cur = db.cursor()

    cur.execute('''SELECT id FROM firmwares WHERE name = ?''', [firmware])
    if cur.fetchone() == None:
        print("Adding firmware", firmware)
        cur.execute('''INSERT INTO firmwares(name) VALUES(?)''', [firmware])

    cur.execute(
            '''
            UPDATE devices SET ip = ?, seen_timestamp = datetime('now'), firmware_id = (SELECT id FROM firmwares WHERE name = ?)
            WHERE mac = ?
            ''',
            [ip, firmware, mac]
    )
    print("update:", cur.rowcount)
    if cur.rowcount < 1:
        print("Adding device", mac)
        cur.execute(
                '''
                INSERT INTO devices(mac, ip, seen_timestamp, firmware_id)
                VALUES(?, ?, datetime('now'), (SELECT id FROM firmwares WHERE name = ?))
                ''',
                [mac, ip, firmware]
        )

    db.commit()

    return "", 304

if __name__ == "__main__":
    print("Starting DB")
    db = sqlite3.connect('esp-puppeteer.sqlite3')

    #app.debug = True
    app.run(port=3777)

