import sqlite3
import os
from datetime import datetime
import pytz

# Database file location
DB_FILE = 'cloud_storage.db'

# Indian timezone
IST = pytz.timezone('Asia/Kolkata')

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Files table with metadata
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL UNIQUE,
            filepath TEXT NOT NULL,
            source_type TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            file_type TEXT,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            thumbnail_path TEXT,
            optimized_path TEXT,
            duration INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Watch history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watch_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            last_position REAL DEFAULT 0,
            duration REAL DEFAULT 0,
            watch_percentage REAL DEFAULT 0,
            last_watched TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE
        )
    ''')
    
    # User preferences table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pref_key TEXT NOT NULL UNIQUE,
            pref_value TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

def add_file(filename, filepath, source_type, file_size, file_type=None):
    """Add a file to the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current IST time
    ist_time = datetime.now(IST)
    
    try:
        cursor.execute('''
            INSERT INTO files (filename, filepath, source_type, file_size, file_type, upload_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (filename, filepath, source_type, file_size, file_type, ist_time))
        
        conn.commit()
        file_id = cursor.lastrowid
        conn.close()
        return file_id
    except sqlite3.IntegrityError:
        # File already exists, update it
        cursor.execute('''
            UPDATE files 
            SET filepath = ?, source_type = ?, file_size = ?, file_type = ?, upload_date = ?
            WHERE filename = ?
        ''', (filepath, source_type, file_size, file_type, ist_time, filename))
        
        conn.commit()
        cursor.execute('SELECT id FROM files WHERE filename = ?', (filename,))
        file_id = cursor.fetchone()[0]
        conn.close()
        return file_id

def update_file_metadata(file_id, thumbnail_path=None, optimized_path=None, duration=None):
    """Update file metadata"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    updates = []
    params = []
    
    if thumbnail_path:
        updates.append('thumbnail_path = ?')
        params.append(thumbnail_path)
    if optimized_path:
        updates.append('optimized_path = ?')
        params.append(optimized_path)
    if duration:
        updates.append('duration = ?')
        params.append(duration)
    
    if updates:
        params.append(file_id)
        query = f"UPDATE files SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
    
    conn.close()

def get_all_files(sort_by='date', order='desc'):
    """Get all files with sorting"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Map sort options
    sort_columns = {
        'name': 'filename',
        'date': 'upload_date',
        'type': 'file_type',
        'size': 'file_size'
    }
    
    sort_col = sort_columns.get(sort_by, 'upload_date')
    sort_order = 'DESC' if order == 'desc' else 'ASC'
    
    query = f'''
        SELECT f.*, wh.last_position, wh.watch_percentage, wh.last_watched
        FROM files f
        LEFT JOIN watch_history wh ON f.id = wh.file_id
        ORDER BY f.{sort_col} {sort_order}
    '''
    
    cursor.execute(query)
    files = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in files]

def delete_file(file_id):
    """Delete a file from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM files WHERE id = ?', (file_id,))
    conn.commit()
    conn.close()

def update_watch_history(file_id, position, duration):
    """Update or create watch history for a file"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    watch_percentage = (position / duration * 100) if duration > 0 else 0
    ist_time = datetime.now(IST)
    
    # Check if history exists
    cursor.execute('SELECT id FROM watch_history WHERE file_id = ?', (file_id,))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute('''
            UPDATE watch_history 
            SET last_position = ?, duration = ?, watch_percentage = ?, last_watched = ?
            WHERE file_id = ?
        ''', (position, duration, watch_percentage, ist_time, file_id))
    else:
        cursor.execute('''
            INSERT INTO watch_history (file_id, last_position, duration, watch_percentage, last_watched)
            VALUES (?, ?, ?, ?, ?)
        ''', (file_id, position, duration, watch_percentage, ist_time))
    
    conn.commit()
    conn.close()

def get_watch_history(file_id):
    """Get watch history for a file"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT last_position, duration, watch_percentage
        FROM watch_history
        WHERE file_id = ?
    ''', (file_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    return dict(result) if result else None

def get_all_watch_history():
    """Get all watch history sorted by last watched"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT f.*, wh.last_position, wh.duration, wh.watch_percentage, wh.last_watched
        FROM watch_history wh
        JOIN files f ON wh.file_id = f.id
        ORDER BY wh.last_watched DESC
        LIMIT 50
    ''')
    
    history = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in history]

def set_user_preference(key, value):
    """Set user preference"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO user_preferences (pref_key, pref_value) VALUES (?, ?)', (key, value))
    except sqlite3.IntegrityError:
        cursor.execute('UPDATE user_preferences SET pref_value = ? WHERE pref_key = ?', (value, key))
    
    conn.commit()
    conn.close()

def get_user_preference(key, default=None):
    """Get user preference"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT pref_value FROM user_preferences WHERE pref_key = ?', (key,))
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else default

def get_file_by_name(filename):
    """Get file by filename"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM files WHERE filename = ?', (filename,))
    result = cursor.fetchone()
    conn.close()
    
    return dict(result) if result else None

def get_file_by_id(file_id):
    """Get file by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM files WHERE id = ?', (file_id,))
    result = cursor.fetchone()
    conn.close()
    
    return dict(result) if result else None

# Initialize database on import
if not os.path.exists(DB_FILE):
    init_db()
