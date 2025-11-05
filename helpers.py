import requests
import base64
import os
import sqlite3
from flask import g, redirect, render_template, session
from functools import wraps

DATABASE = "nostalgia.db"

def get_db():
    """Open a new database connection if one doesn't exist for the current request"""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  # allows accessing columns by name
    return g.db


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function



def close_db(exception=None):
    """Close the database connection at the end of a request"""
    db = g.pop("db", None)
    if db is not None:
        db.close()



def get_spotify_token():
    """Get access token"""
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

    auth_string = f"{client_id}:{client_secret}"
    auth_base64 = base64.b64encode(auth_string.encode()).decode()

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={"grant_type": "client_credentials"}
     ) 

    return response.json()["access_token"]

def search_songs_by_year(year, limit=40):
    """Search Spotify for songs from a specific year"""
    token = get_spotify_token()

    response = requests.get(
        "https://api.spotify.com/v1/search",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "q": f"year:{year}",
            "type": "track",
            "limit": limit,
            "market": "US" 
        }
    )

    tracks = []

    for track in response.json()["tracks"]["items"]:

        print("Popularity:", track["popularity"])

        tracks.append({
            "spotify_id": track["id"],
            "title": track["name"],
            "artist": track["artists"][0]["name"],
            "album": track["album"]["name"],
            "preview_url": track["preview_url"],
            "album_art": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
            "spotify_url": track["external_urls"]["spotify"],
            "release_date": track["album"]["release_date"],
            "popularity_score": track["popularity"]
        })
    
    tracks = [t for t in tracks if t["popularity_score"] > 1]
    tracks.sort(key=lambda x: x["popularity_score"], reverse=True)

    return tracks

def search_songs(query, limit=20):
    """Search Spotify for any song by name or artist"""
    token = get_spotify_token()
    
    response = requests.get(
        "https://api.spotify.com/v1/search",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "q": query,
            "type": "track",
            "limit": limit
        }
    )
    
    tracks = []
    for track in response.json()["tracks"]["items"]:
        tracks.append({
            "spotify_id": track["id"],
            "title": track["name"],
            "artist": track["artists"][0]["name"],
            "album": track["album"]["name"],
            "preview_url": track["preview_url"],
            "album_art": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
            "spotify_url": track["external_urls"]["spotify"],
            "release_date": track["album"]["release_date"],
            "popularity_score": track["popularity"]
        })
    
    tracks.sort(key=lambda x: x["popularity_score"], reverse=True)
    return tracks


def search_songs_with_year(query, year, limit=20):
    """Search for songs with both name/artist AND year filter"""
    token = get_spotify_token()
    
    # Combine query with year filter
    search_query = f"{query} year:{year}"
    
    response = requests.get(
        "https://api.spotify.com/v1/search",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "q": search_query,
            "type": "track",
            "limit": limit
        }
    )
    
    tracks = []
    for track in response.json()["tracks"]["items"]:
        tracks.append({
            "spotify_id": track["id"],
            "title": track["name"],
            "artist": track["artists"][0]["name"],
            "album": track["album"]["name"],
            "preview_url": track["preview_url"],
            "album_art": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
            "spotify_url": track["external_urls"]["spotify"],
            "release_date": track["album"]["release_date"],
            "popularity_score": track["popularity"]
        })
    
    tracks.sort(key=lambda x: x["popularity_score"], reverse=True)
    return tracks


def random_songs(query, year, limit=20):
    """Search for songs with both name/artist AND year filter"""
    token = get_spotify_token()
    
    # Combine query with year filter
    search_query = f"{query} year:{year}"
    
    response = requests.get(
        "https://api.spotify.com/v1/search",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "q": search_query,
            "type": "track",
            "limit": limit
        }
    )
    
    tracks = []
    for track in response.json()["tracks"]["items"]:
        tracks.append({
            "spotify_id": track["id"],
            "title": track["name"],
            "artist": track["artists"][0]["name"],
            "album": track["album"]["name"],
            "preview_url": track["preview_url"],
            "album_art": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
            "spotify_url": track["external_urls"]["spotify"],
            "release_date": track["album"]["release_date"],
            "popularity_score": track["popularity"]
        })
    
    tracks.sort(key=lambda x: x["popularity_score"], reverse=True)
    return tracks

def get_random_songs_by_decade(start_year, end_year, limit=50):
    """get random songs by range"""
    token = get_spotify_token()
    search_query = f"year:{start_year}-{end_year}"

    response = requests.get(
        "https://api.spotify.com/v1/search",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "q": search_query,
            "type": "track",
            "limit": limit           
        }
    )

    tracks = []
    for track in response.json()["tracks"]["items"]:
        tracks.append({
            "spotify_id": track["id"],
            "title": track["name"],
            "artist": track["artists"][0]["name"],
            "album": track["album"]["name"],
            "preview_url": track["preview_url"],
            "album_art": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
            "spotify_url": track["external_urls"]["spotify"],
            "release_date": track["album"]["release_date"],
            "popularity_score": track["popularity"]
        })

    tracks.sort(key=lambda x: x["popularity_score"], reverse=True)
    return tracks
