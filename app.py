from flask import Flask, flash, redirect, render_template, request, session, g, jsonify 
import json
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

@app.route("/api/playlists")
def get_playlists():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    db = get_db()
    playlists = db.execute(
        """SELECT p.id, p.name, p.year, COUNT(pt.id) as track_count
           FROM playlists p
           LEFT JOIN playlist_tracks pt ON p.id = pt.playlist_id
           WHERE p.user_id = ?
           GROUP BY p.id
           ORDER BY p.created_at DESC""",
        (session["user_id"],)
    ).fetchall()
    db.close()

    return jsonify([dict(playlist) for playlist in playlists])

@app.route("/api/playlists/create", methods=["POST"])
def create_playlist():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.json
    playlist_name = data.get("name")
    track = data.get("track")

    if not playlist_name or not track:
        return jsonify({"error": "Missing data"}), 400
    
    db = get_db()

    # create playlist
    cursor = db.execute(
        "INSERT INTO playlists (user_id, name, year) VALUES (?, ?, ?)",
        (session["user_id"], playlist_name, track.get("release_date", "")[:4])
    )
    playlist_id = cursor.lastrowid

    # add track to playlist
    db.execute(
        """INSERT INTO playlist_tracks 
           (playlist_id, spotify_id, title, artist, preview_url, album_art, spotify_url, position)
           VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
        (playlist_id, track["spotify_id"], track["title"], track["artist"],
         track["preview_url"], track["album_art"], track["spotify_url"])
    )
    
    db.commit()
    db.close()

    return jsonify({"success": True, "playlist_id": playlist_id})

@app.route("/api/playlists/<int:playlist_id>", methods=["DELETE"])
def delete_playlist(playlist_id):
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    db = get_db()

    playlist = db.execute(
        "SELECT id FROM playlists WHERE id = ? AND user_id = ?",
        (playlist_id, session["user_id"])
    ).fetchone()

    if not playlist:
        return jsonify({"error": "Playlist not found"}), 404

    db.execute("DELETE FROM playlist_tracks WHERE playlist_id = ?", (playlist_id,))

    db.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))

    db.commit()
    db.close()

    return jsonify({"success": True, "message": "Playlist deleted"})

@app.route("/api/playlists/add-track", methods=["POST"])
def add_track_to_playlist():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.json
    playlist_id = data.get("playlist_id")
    track = data.get("track")

    if not playlist_id or not track:
        return jsonify({"error": "Missing data"}), 400
    
    db = get_db()

    # check if user has the playlist
    playlist = db.execute(
        "SELECT * FROM playlists WHERE id = ? AND user_id = ?",
        (playlist_id, session["user_id"])
    ).fetchone()

    if not playlist:
        db.close()
        return jsonify({"error": "Unauthorized"}), 403
    
    #check if song is already in the playlist
    existing = db.execute(
        "SELECT * FROM playlist_tracks WHERE playlist_id = ? AND spotify_id = ?",
        (playlist_id, track["spotify_id"])
    ).fetchone()

    if existing:
        db.close()
        return jsonify({"error": "Track already in playlist"}), 400
    
    #get max position in list
    max_pos = db.execute(
        "SELECT MAX(position) as max FROM playlist_tracks WHERE playlist_id = ?",
        (playlist_id,)
    ).fetchone()["max"]
    
    position = (max_pos or 0) + 1

    #Add a song
    db.execute(
        """INSERT INTO playlist_tracks 
           (playlist_id, spotify_id, title, artist, preview_url, album_art, spotify_url, position)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (playlist_id, track["spotify_id"], track["title"], track["artist"],
         track["preview_url"], track["album_art"], track["spotify_url"], position)
    )
    
    db.commit()
    db.close()

    return jsonify({"success": True})

@app.route("/saved")
def saved():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("saved.html")

@app.route("/playlist/<int:playlist_id>")
def view_playlist(playlist_id):
    if "user_id" not in session:
        return redirect("/login")
    
    db = get_db()
    
    # Get playlist info
    playlist = db.execute(
        "SELECT * FROM playlists WHERE id = ? AND user_id = ?",
        (playlist_id, session["user_id"])
    ).fetchone()
    
    if not playlist:
        db.close()
        return "Playlist not found", 404
    
    # Get tracks
    tracks = db.execute(
        """SELECT * FROM playlist_tracks 
           WHERE playlist_id = ? 
           ORDER BY position""",
        (playlist_id,)
    ).fetchall()
    
    db.close()
    
    return render_template("view_playlist.html", playlist=dict(playlist), tracks=[dict(t) for t in tracks])

@app.route("/api/playlists/remove-track", methods=["POST"])
def remove_track():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    track_id = request.json.get("track_id")
    
    db = get_db()
    
    # Verify ownership
    track = db.execute(
        """SELECT pt.* FROM playlist_tracks pt
           JOIN playlists p ON pt.playlist_id = p.id
           WHERE pt.id = ? AND p.user_id = ?""",
        (track_id, session["user_id"])
    ).fetchone()
    
    if not track:
        db.close()
        return jsonify({"error": "Unauthorized"}), 403
    
    db.execute("DELETE FROM playlist_tracks WHERE id = ?", (track_id,))
    db.commit()
    db.close()
    
    return jsonify({"success": True})


if __name__ == '__main__':
    app.run(debug=True)
