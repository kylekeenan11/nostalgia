from flask import Flask

import sqlite3
con = sqlite3.connect("nostalgia.db")

cur = con.cursor()  

app = Flask(__name__) 

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"