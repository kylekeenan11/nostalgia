from flask import Flask, flash, redirect, render_template, request, session
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash
from flask_session import Session
import os

from helpers import search_songs_with_year, search_songs, search_songs_by_year, get_random_songs_by_decade

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/")
def index():
    tracks80s = get_random_songs_by_decade(1980, 1989, 20)
    tracks90s = get_random_songs_by_decade(1990, 1999, 4)

    return render_template("index.html", tracks80s=tracks80s, tracks90s=tracks90s)


@app.route("/playlist")
def playlist():
    year = request.form.get("year", type=int)
    if year:
        tracks = search_songs_by_year(year, 40)
        return render_template("playlist.html", year=year, tracks=tracks)
    return redirect("/")

@app.route("/search", methods=["GET", "POST"])
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
