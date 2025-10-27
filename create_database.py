import sqlite3

# Connect to database (creates it if it doesn't exist)
conn = sqlite3.connect('nostalgia.db')

# Create a cursor object
cursor = conn.cursor()

# Create a table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS playlists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        year INTEGER NOT NULL,
        name TEXT NOT NULL,  -- e.g., "My 1995 Hits"
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )        
    ''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS playlist_tracks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        playlist_id INTEGER NOT NULL,
        spotify_id TEXT NOT NULL,
        title TEXT NOT NULL,
        artist TEXT NOT NULL,
        preview_url TEXT,
        album_art TEXT,
        spotify_url TEXT,
        position INTEGER,  -- Track order in playlist
        FOREIGN KEY (playlist_id) REFERENCES playlists(id)
    )        
    ''')

# Commit the changes
conn.commit()

# Close the connection
conn.close()

print("Table created successfully!")