from flask import Flask, flash, redirect, render_template, request, session, g
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash
from flask_session import Session
import os
import sqlite3

from helpers import search_songs_with_year, search_songs, search_songs_by_year, get_random_songs_by_decade, get_db, close_db, login_required

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
DATABASE = "nostalgia.db"

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.teardown_appcontext(close_db)

@app.route("/")
@login_required
def index():
    tracks20s = get_random_songs_by_decade(2000, 2009)
    tracks10s = get_random_songs_by_decade(2010, 2019)

    return render_template("index.html", tracks20s=tracks20s, tracks10s=tracks10s)


@app.route("/register", methods=["GET", "POST"])
def register():
    """register a user account"""
    if request.method == "POST":
        username = request.form.get("username")

        password = request.form.get("password")
        confirm_password = request.form.get("confirmation")
        if not password or not confirm_password:
            return render_template("error.html")
        if password != confirm_password:
            return render_template("error.html")
        
        hash = generate_password_hash(password, method='scrypt', salt_length=16)

        """  SQL query to input user details into db """

        db=get_db()
        db.execute("INSERT INTO users (username, password_hash) VALUES(?, ?)", (username, hash))
        db.commit()   

        return redirect("/")
    
    else:
        return render_template("register.html")
    

@app.route("/login", methods=["GET", "POST"])
def login():

    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            return render_template("error.html")
        elif not request.form.get("password"):
            return render_template("error.html")
        
        db=get_db()
        users = db.execute("SELECT * FROM users WHERE username = ?", (request.form.get("username"),)).fetchall()    

        if len(users) != 1 or not check_password_hash(
            users[0]["password_hash"], request.form.get("password")
        ):
            return render_template("error.html")
        
        session["user_id"] = users[0]["id"]

        return redirect("/")
    
    else:
        return render_template("login.html")
    
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")



@app.route("/playlist")
@login_required
def playlist():
    year = request.form.get("year", type=int)
    if year:
        tracks = search_songs_by_year(year, 40)
        return render_template("playlist.html", year=year, tracks=tracks)
    return redirect("/")

@app.route("/search", methods=["GET", "POST"])
@login_required
def search():

    if request.method == "POST":
        song_query = request.form.get("song")
        year = request.form.get("year", type=int)
    
    else:
        song_query = request.args.get("song")
        year = request.args.get("year", type=int)

    tracks = []

    if song_query and year:
        tracks = search_songs_with_year(song_query, year)

    elif song_query:
        tracks = search_songs(song_query)

    elif year:
        tracks = search_songs_by_year(year, 40) 

    else:
        return redirect("/")
    
    return render_template("playlist.html", tracks=tracks, year=year, query=song_query)



if __name__ == '__main__':
    app.run(debug=True)
