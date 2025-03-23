import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import os

# Asegurarse de que el directorio instance existe
os.makedirs('instance', exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect('instance/music_server.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.execute('''
    CREATE TABLE IF NOT EXISTS playlists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.execute('''
    CREATE TABLE IF NOT EXISTS playlist_songs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        playlist_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        FOREIGN KEY (playlist_id) REFERENCES playlists (id)
    )
    ''')
    
    conn.commit()
    conn.close()

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash
    
    @staticmethod
    def get_by_id(user_id):
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        
        if user is None:
            return None
        
        return User(
            id=user['id'],
            username=user['username'],
            password_hash=user['password_hash']
        )
    
    @staticmethod
    def get_by_username(username):
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user is None:
            return None
        
        return User(
            id=user['id'],
            username=user['username'],
            password_hash=user['password_hash']
        )
    
    @staticmethod
    def create(username, password):
        conn = get_db_connection()
        
        # Verificar si el usuario ya existe
        existing_user = conn.execute(
            'SELECT id FROM users WHERE username = ?', 
            (username,)
        ).fetchone()
        
        if existing_user:
            conn.close()
            return False
        
        password_hash = generate_password_hash(password)
        
        cursor = conn.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username, password_hash)
        )
        
        user_id = cursor.lastrowid
        
        # Crear una playlist predeterminada para el usuario
        conn.execute(
            'INSERT INTO playlists (user_id, title) VALUES (?, ?)',
            (user_id, 'Mi Playlist')
        )
        
        conn.commit()
        conn.close()
        return True
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_playlists(self):
        conn = get_db_connection()
        playlists = conn.execute(
            'SELECT * FROM playlists WHERE user_id = ? ORDER BY created_at DESC',
            (self.id,)
        ).fetchall()
        conn.close()
        return playlists
    
    def create_playlist(self, title):
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO playlists (user_id, title) VALUES (?, ?)',
            (self.id, title)
        )
        conn.commit()
        conn.close()
        return True

# Función para añadir una canción a una playlist
def add_song_to_playlist(playlist_id, filename):
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO playlist_songs (playlist_id, filename) VALUES (?, ?)',
        (playlist_id, filename)
    )
    conn.commit()
    conn.close()
    return True

# Función para obtener las canciones de una playlist
def get_playlist_songs(playlist_id):
    conn = get_db_connection()
    songs = conn.execute(
        'SELECT * FROM playlist_songs WHERE playlist_id = ?',
        (playlist_id,)
    ).fetchall()
    conn.close()
    return songs