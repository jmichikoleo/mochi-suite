import tkinter as tk
from tkinter import ttk
import sqlite3
import os
from datetime import datetime, date, timedelta
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --------------------- Theme definitions ---------------------
THEMES = {
    "Pastel Pink": {
        "BG": "#fff1f3",
        "SIDEBAR": "#ffe6ea",
        "CARD": "#ffffff",
        "BTN": "#ffd7dd",
        "BTN_HOVER": "#ffb6c2",
        "TEXT": "#2b2b2b",
        "TEXT_LIGHT": "#888888",
        "ACCENT": "#ffdfe6"
    },
    "Cream": {
        "BG": "#fff9f0",
        "SIDEBAR": "#fff1e0",
        "CARD": "#ffffff",
        "BTN": "#f7e6c9",
        "BTN_HOVER": "#edd3b7",
        "TEXT": "#3b2f27",
        "TEXT_LIGHT": "#888888",
        "ACCENT": "#f3e1c9"
    },
    "Sakura": {
        "BG": "#fff6f8",
        "SIDEBAR": "#ffdce6",
        "CARD": "#ffffff",
        "BTN": "#ffb7cf",
        "BTN_HOVER": "#ff9fc0",
        "TEXT": "#4b2a33",
        "TEXT_LIGHT": "#888888",
        "ACCENT": "#ffd0dd"
    },
    "BluePastel": {
    "BG": "#d9f3fb",
    "SIDEBAR": "#c2ebf8",
    "CARD": "#ffffff",
    "BTN": "#c8f0ff",
    "BTN_HOVER": "#bde8f7",
    "TEXT": "#1e2a38",
    "TEXT_LIGHT": "#a0a0a0",
    "ACCENT": "#c0e5f5"
    },

    "Lavender": {
        "BG": "#f7f4ff",
        "SIDEBAR": "#efe7ff",
        "CARD": "#ffffff",
        "BTN": "#e7dbff",
        "BTN_HOVER": "#d5c2ff",
        "TEXT": "#332e47",
        "TEXT_LIGHT": "#888888",
        "ACCENT": "#e6dbff"
    }
}

current_theme_name = "Pastel Pink"

# --------------------- Helpers ---------------------
def theme():
    return THEMES[current_theme_name]

def apply_theme():
    t = theme()
    
    # Core elements
    root.configure(bg=t["BG"])
    header.configure(bg=t["BG"])
    title_label.configure(bg=t["BG"], fg=t["TEXT"])
    theme_btn.configure(bg=t["BTN"], fg=t["TEXT"], activebackground=t["BTN_HOVER"], activeforeground=t["TEXT"])
    sidebar_container.configure(bg=t["BG"])
    canvas.configure(bg=t["SIDEBAR"])
    inner.configure(bg=t["SIDEBAR"])
    main_area.configure(bg=t["CARD"])
    
    # New Sidebar Show Button
    sidebar_show_container.configure(bg=t["BG"])
    show_sidebar_btn.configure(bg=t["BTN"], fg=t["TEXT"], activebackground=t["BTN_HOVER"], activeforeground=t["TEXT"])

    # Sidebar elements
    for b in sidebar_buttons:
        b.configure(bg=t["BTN"], fg=t["TEXT"], activebackground=t["BTN_HOVER"], activeforeground=t["TEXT"])
    for h in section_headers:
        h.configure(bg=t["SIDEBAR"], fg=t["TEXT"])
        
    # Main page elements
    for p in pages.values():
        for w in p.winfo_children():
            if isinstance(w, tk.Label):
                w.configure(bg=t["CARD"], fg=t["TEXT"])
            # Recursively update colors for frames inside pages (like dashboard cards)
            elif isinstance(w, tk.Frame):
                w.configure(bg=t["CARD"])
                for w_child in w.winfo_children():
                    if isinstance(w_child, tk.Frame):
                        w_child.configure(bg=t["BG"]) # Dashboard card bg
                        for card_w in w_child.winfo_children():
                            if isinstance(card_w, tk.Label):
                                card_w.configure(bg=t["BG"], fg=t["TEXT"])
    
    # Theme task list widgets (need to reload)
    if "task_list_frame" in special_widgets:
        special_widgets["task_list_frame"].configure(bg=t["SIDEBAR"])

    # Special Widgets (Journal Text areas)
    if "journal_txt" in special_widgets:
        special_widgets["journal_txt"].configure(bg=t["CARD"], fg=t["TEXT"], insertbackground=t["TEXT"])
    if "journal_history_list" in special_widgets:
        # Note: Set history list BG to SIDEBAR or BG for better contrast with the CARD background
        special_widgets["journal_history_list"].configure(bg=t["SIDEBAR"], fg=t["TEXT"]) 

def cycle_theme():
    global current_theme_name
    keys = list(THEMES.keys())
    idx = keys.index(current_theme_name)
    current_theme_name = keys[(idx + 1) % len(keys)]
    theme_btn.config(text=current_theme_name)
    apply_theme()
    
# --------------------- Fonts & sizes ---------------------
TITLE_FONT = ("Segoe UI", 18, "bold")
HEADER_FONT = ("Segoe UI", 12, "bold")
BTN_FONT = ("Segoe UI", 11)
TEXT_FONT = ("Segoe UI", 11)

# --------------------- Database setup ---------------------
DB_PATH = "mochi.db"

def db_connect():
    return sqlite3.connect(DB_PATH)

def run_query(query, params=()):
    try:
        conn = db_connect()
        c = conn.cursor()
        c.execute(query, params)
        if query.strip().upper().startswith("SELECT"):
            rows = c.fetchall()
            conn.close()
            return rows
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"DB error: {e}")
        return None

# main.py (Replace the entire init_db function with this)
def init_db():
    conn = db_connect()
    c = conn.cursor()
    # --- JOURNAL ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS journal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        entry TEXT
    )
    """)

    # --- TODOS ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task TEXT NOT NULL,
        completed INTEGER NOT NULL DEFAULT 0,
        created_date TEXT
    )
    """)

    # --- MOODS ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS moods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT UNIQUE,
        mood_emoji TEXT NOT NULL
    )
    """)

    # --- HABITS ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS habits_tbl (
        habit_id TEXT PRIMARY KEY,
        habit_name TEXT NOT NULL,
        habit_completions TEXT DEFAULT '{}'
    )
    """)

    # --- NOTES ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS notes_folders (
        folder_uid TEXT PRIMARY KEY,
        parent_uid TEXT,
        folder_name TEXT NOT NULL,
        created_at TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS notes_items (
        note_uid TEXT PRIMARY KEY,
        folder_uid TEXT,
        note_title TEXT NOT NULL,
        note_content TEXT,
        created_at TEXT
    )
    """)

    # --- IMPORTED FILES ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS study_imported_files (
        import_uid TEXT PRIMARY KEY,
        file_name TEXT NOT NULL,
        file_type TEXT,
        stored_path TEXT NOT NULL,
        date_imported TEXT NOT NULL
    )
    """)

    # --- TAROT ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS TAROT (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reading_name TEXT NOT NULL,
        category TEXT,
        spread TEXT,
        date TEXT,
        cards TEXT,
        interpretation TEXT,
        tags TEXT
    )
    """)

    # --- FINANCE ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS category_budget (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        budget REAL NOT NULL
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS spending_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        entry_date TEXT NOT NULL
    )
    """)

    # --- TV SHOWS ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS tv_shows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        release_year INTEGER,
        season INTEGER,
        episode INTEGER,
        status TEXT NOT NULL,
        genre TEXT,
        rating INTEGER,
        date_watched TEXT
    )
    """)

    # --- AU ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS AU (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT,
        link TEXT,
        "group" TEXT,
        genre TEXT,
        rating INTEGER,
        status TEXT NOT NULL
    )
    """)

    # --- DUE REMINDERS / BILL PAYMENTS ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS due_reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        due_date TEXT NOT NULL,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        status TEXT DEFAULT 'Pending'
    )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS due_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            due_date TEXT NOT NULL,
            notes TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # --- WISHLIST ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS wishlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        price REAL,
        priority TEXT,
        status TEXT NOT NULL,
        date_added TEXT NOT NULL,
        date_purchased TEXT
    )
    """)

    # --- MOVIES ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS movies (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        release_year INTEGER,
        runtime INTEGER,
        status TEXT NOT NULL,
        genre TEXT,
        rating INTEGER,
        date_watched TEXT
    )
    """)
    # --- PICK FOR ME RANDOMIZER --- 
    c.execute("""
        CREATE TABLE IF NOT EXISTS randomizer_lists (
            id INTEGER PRIMARY KEY,
            list_name TEXT NOT NULL UNIQUE, 
            items_data TEXT NOT NULL           
        )
    """)
    
    # --- WATER ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS water (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT UNIQUE,
        cups INTEGER NOT NULL
    )
    """)

    # --- EVENTS (Calendar) ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        event_date TEXT NOT NULL,
        event_time TEXT
    )
    """)

    # --- BOOKS ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        author TEXT,
        total_pages INTEGER,
        current_page INTEGER DEFAULT 0,
        status TEXT NOT NULL,
        start_date TEXT,
        finish_date TEXT,
        genre TEXT,
        rating INTEGER
    )
    """)

    # --- SLEEP ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS user_sleep_log (
        sleep_id INTEGER PRIMARY KEY,
        sleep_date TEXT,
        bed_time TEXT,
        wake_time TEXT,
        duration_minutes REAL
    )
    """)

    # --- SHOPPING & INVENTORY ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS shopping_list (
        id INTEGER PRIMARY KEY,
        item_name TEXT NOT NULL,
        quantity TEXT,
        purchased INTEGER DEFAULT 0
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY,
        item_name TEXT NOT NULL,
        current_quantity REAL,
        unit TEXT
    )
    """)

    # --- DIET ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS diet_weight_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        weight REAL NOT NULL
    )
    """)

    # --- HYPERLINKS ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS hyperlinks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        title TEXT NOT NULL,
        category TEXT,
        date_added TEXT
    )
    """)

    # --- PERIODS ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS periods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        start_date TEXT NOT NULL,
        end_date TEXT
    )
    """)

    # --- CalorieS ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS calorie_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        food TEXT NOT NULL,
        calories INTEGER NOT NULL
    )
    """)

    # --- RECIPES ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        prep_time TEXT,
        ingredients TEXT,
        instructions TEXT
    )
    """)

    # --- FLASHCARDS ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS study_flashcard_decks (
        deck_uid TEXT PRIMARY KEY,
        deck_name TEXT NOT NULL,
        created_at TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS study_flashcards (
        card_uid TEXT PRIMARY KEY,
        deck_uid TEXT NOT NULL,
        front_text TEXT NOT NULL,
        back_text TEXT NOT NULL,
        created_at TEXT,
        status TEXT DEFAULT 'new',
        FOREIGN KEY(deck_uid) REFERENCES study_flashcard_decks(deck_uid) ON DELETE CASCADE
    )
    """)

    # --- WORKOUTS ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS workouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT UNIQUE NOT NULL,
        type TEXT,
        duration REAL,
        distance REAL,
        notes TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS sets_reps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workout_id INTEGER NOT NULL,
        exercise_name TEXT NOT NULL,
        set_number INTEGER,
        weight REAL,
        reps INTEGER,
        FOREIGN KEY(workout_id) REFERENCES workouts(id) ON DELETE CASCADE
    )
    """)

    # --- GOALS ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT,
        target_date TEXT,
        current_progress REAL DEFAULT 0.0,
        target_value REAL DEFAULT 1.0,
        status TEXT DEFAULT 'Active'
    )
    """)
    
    # --- FOCUS SESSIONS (Forest-style timer) ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS focus_sessions_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        focus_date TEXT NOT NULL,
        duration_minutes INTEGER NOT NULL,
        purpose TEXT,
        notes TEXT,
        success INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """)
    
    # --- METRICS ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL UNIQUE,
        weight REAL,
        body_fat_percent REAL,
        muscle_mass REAL,
        basal_metabolic_rate REAL,
        skeletal_muscle_mass REAL,
        body_fat_mass REAL,
        bmi REAL,
        waist_hip_ratio REAL,
        visceral_fat_level REAL,
        total_body_water REAL,
        protein REAL,
        mineral REAL
    )
    """)

    # --- SONGWRITING ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS songwriting (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        lyrics TEXT,
        mood TEXT,
        tags TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    )
    """)
    
    # --- Song Drafts Table ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS song_drafts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL UNIQUE,
        lyrics TEXT,
        chords TEXT,
        mood TEXT,
        genre TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # --- TIMEBLOCKS ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS timeblocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        start_time TEXT,
        end_time TEXT,
        title TEXT,
        color TEXT,
        notes TEXT
    );
    """)
    
    # CLOSURE BOX TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS closure_box (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,         
        content TEXT NOT NULL,        
        closure_type TEXT NOT NULL,   
        closure_date TEXT NOT NULL    
    );
    """)
    
    # Events Countdown Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS events_countdown (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        target_datetime TEXT NOT NULL, 
        color TEXT DEFAULT '#ff5d8f'
    );
    """)
    
    # Project Table 
    c.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        start_date TEXT NOT NULL,   
        end_date TEXT NOT NULL,      
        color TEXT,                   
        progress INTEGER DEFAULT 0,    
        status TEXT DEFAULT 'In Progress' 
        );
    """)
        
    # --- 2. MILESTONES Table (Project Checkpoints) ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS milestones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        target_date TEXT NOT NULL,   
        is_complete INTEGER DEFAULT 0, 
        FOREIGN KEY (project_id) REFERENCES projects(id)
    );
    """)
    
    # Daily Fortunes Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_fortunes (
            id INTEGER PRIMARY KEY,
            fortune_text TEXT NOT NULL,         
            angel_number TEXT,  
            side_quest TEXT,  
            reveal_date TEXT NOT NULL UNIQUE    -- YYYY-MM-DD
        )
    """)
    
    #Weekly Overview Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS news_weekly_overview (
        week_start TEXT PRIMARY KEY,
        priorities TEXT,
        mon TEXT,
        tue TEXT,
        wed TEXT,
        thu TEXT,
        fri TEXT,
        sat TEXT,
        sun TEXT
        )
    """)
    
    # Version of Me Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS version_of_me_snapshot (
            id INTEGER PRIMARY KEY,
            snapshot_date TEXT NOT NULL UNIQUE, 
            weight REAL,                       
            songs TEXT,                     
            foods TEXT,                     
            obsession TEXT,                   
            main_activity TEXT,                
            media_consumption TEXT           
        )
    """)
    
    # COMMON PLACE KNOWLEDGE TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS commonplace (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        content TEXT,
        preview TEXT,
        tags TEXT
    )
    """)

    # --- BRAINDUMPS ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS braindumps (
        date TEXT PRIMARY KEY,
        content TEXT
    )
    """)
    
    conn.commit()
    conn.close()

def clean_water_table():
    """Remove corrupted rows in water table."""
    conn = db_connect()
    c = conn.cursor()
    c.execute("DELETE FROM water WHERE date NOT LIKE '____-__-__'")
    deleted = conn.total_changes
    conn.commit()
    conn.close()
    if deleted > 0:
        print(f"Cleaned {deleted} corrupted rows from water table.")

# Initialize DB and clean corrupted rows
init_db()
clean_water_table()

# main.py (After clean_water_table(), before root = tk.Tk())
from datetime import date, datetime, timedelta

from datetime import datetime

# --- GLOBAL ---

# --- PICK FOR ME RANDOMIZER FUNCTIONS ---
import sqlite3
import json

# --- RANDOMIZER DB FUNCTIONS (GLOBAL) ---

def save_list(name, items_data_json, list_id=None):
    """Saves a new list or updates an existing one."""
    conn = db_connect()
    c = conn.cursor()
    
    try:
        if list_id:
            # Update existing list
            c.execute("""
                UPDATE randomizer_lists SET list_name = ?, items_data = ?
                WHERE id = ?
            """, (name, items_data_json, list_id))
            conn.commit()
            return True
        else:
            # Insert new list
            c.execute("""
                INSERT INTO randomizer_lists (list_name, items_data)
                VALUES (?, ?)
            """, (name, items_data_json))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        print(f"Error: List name '{name}' already exists.")
        return False
    except Exception as e:
        print(f"DB Error saving list: {e}")
        return False
    finally:
        conn.close()


def load_list_names():
    """Retrieves all saved list names and their IDs for the selector."""
    conn = db_connect()
    c = conn.cursor()
    
    rows = c.execute("SELECT id, list_name FROM randomizer_lists ORDER BY list_name ASC").fetchall()
    conn.close()
    
    lists = []
    for row in rows:
        lists.append({
            'id': row[0],
            'name': row[1]
        })
    return lists


def load_list_by_id(list_id):
    """Retrieves the full list data (name and JSON items) for a given ID."""
    conn = db_connect()
    c = conn.cursor()
    
    row = c.execute("SELECT list_name, items_data FROM randomizer_lists WHERE id = ?", (list_id,)).fetchone()
    conn.close()
    
    if row:
        return {
            'name': row[0],
            'items_data_json': row[1],
            'id': list_id
        }
    return None


def delete_list(list_id):
    """Deletes a list entry by ID."""
    conn = db_connect()
    c = conn.cursor()
    
    try:
        c.execute("DELETE FROM randomizer_lists WHERE id = ?", (list_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"DB Error deleting list: {e}")
        return False
    finally:
        conn.close()

# --- VERSION OF ME SNAPSHOT FUNCTIONS ---
def check_if_snapshot_taken_this_month():
    """
    Checks if a snapshot has been taken within the current calendar month.
    This enforces the 'monthly' check.
    """
    today = datetime.now()
    current_month_year = today.strftime('%Y-%m')
    conn = db_connect() 
    c = conn.cursor()
    
    # Check for any snapshot date that starts with the current YYYY-MM string
    query = "SELECT id FROM version_of_me_snapshot WHERE snapshot_date LIKE ? || '-%%'"
    row = c.execute(query, (current_month_year,)).fetchone()
    conn.close()
    
    return row is not None # True if a snapshot exists this month

def load_latest_snapshot():
    """Retrieves the most recent snapshot data."""
    conn = db_connect()
    c = conn.cursor()
    
    # Select the most recent entry
    row = c.execute("""
        SELECT 
            snapshot_date, weight, songs, foods, obsession, main_activity, media_consumption
        FROM 
            version_of_me_snapshot
        ORDER BY 
            snapshot_date DESC
        LIMIT 1
    """).fetchone()
    conn.close()
    
    if row:
        return {
            'date': row[0],
            'weight': row[1],
            'songs': row[2],
            'foods': row[3],
            'obsession': row[4],
            'main_activity': row[5],
            'media_consumption': row[6]
        }
    return None

def load_snapshot_history(month_filter=None):
    """
    Loads all snapshot history, optionally filtered by month (YYYY-MM).
    Returns a list of dictionaries.
    """
    conn = db_connect()
    c = conn.cursor()
    
    query = """
        SELECT id, snapshot_date, weight, songs, foods, obsession, main_activity, media_consumption
        FROM version_of_me_snapshot
    """
    params = []
    
    if month_filter:
        query += " WHERE snapshot_date LIKE ? || '-%%'"
        params.append(month_filter)

    query += " ORDER BY snapshot_date DESC" 
    
    rows = c.execute(query, params).fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            'id': row[0],
            'date': row[1],
            'weight': row[2],
            'songs': row[3],
            'foods': row[4],
            'obsession': row[5],
            'main_activity': row[6],
            'media_consumption': row[7]
        })
    return history


def save_new_snapshot(data):
    """Saves a complete monthly snapshot."""
    
    # Ensure data dictionary contains all necessary keys
    required_keys = ['weight', 'songs', 'foods', 'obsession', 'main_activity', 'media_consumption']
    if not all(key in data for key in required_keys):
        print("Error: Missing required data fields for snapshot.")
        return False
        
    conn = db_connect()
    c = conn.cursor()
    snapshot_date = datetime.now().strftime('%Y-%m-%d')

    try:
        c.execute("""
            INSERT INTO version_of_me_snapshot 
            (snapshot_date, weight, songs, foods, obsession, main_activity, media_consumption)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot_date,
            data['weight'],
            data['songs'],
            data['foods'],
            data['obsession'],
            data['main_activity'],
            data['media_consumption']
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        print(f"Error: Snapshot already exists for {snapshot_date}. Cannot save.")
        return False
    except Exception as e:
        print(f"DB Error saving snapshot: {e}")
        return False
    finally:
        conn.close()
        
# --- GLOBAL FORTUNE COOKIE CONTENT LISTS ---

# 1. Reflective Messages / Journal Prompts (60 Options)
REFLECTIVE_MESSAGES = [
    "When did I feel most like myself recently?",
    "What emotion has been showing up the most for me lately, and why?",
    "What did I learn about myself today?",
    "What is one thing I appreciate about myself right now?",
    "What would I say to my younger self today?",
    "What inner wounds am I still healing from?",
    "What am I proud of that I don’t give myself enough credit for?",
    "What is a challenge I overcame that once felt impossible?",
    "What does “growth” look like for me right now?",
    "What is one area where I’ve grown without noticing?",
    "Who makes me feel emotionally safe, and why?",
    "Who drains me emotionally—and why do I allow it?",
    "What does success mean to me personally—not society?",
    "What skill do I want to develop in the next year?",
    "What change am I craving?",
    "What emotion am I avoiding today?",
    "What helps me move through heavy emotions?",
    "What part of myself do I rarely show others, and why?",
    "What emotions do I judge myself for feeling?",
    "What is something I want to change but keep postponing?",
    "What chapter of my life am I currently in?",
    "What decision have I been hesitating to make?",
    "What is my intuition telling me lately?",
    "Which goals matter because of me—and which because of others?",
    "What is something small that would improve my well-being?",
    "What am I grateful for that isn’t obvious?",
    "What am I afraid to admit to myself?",
    "What is something I pretend doesn’t bother me but actually does?",
    "What have I been overthinking, and why?",
    "What expectations do I put on myself that feel heavy?",
    "What story about myself have I been repeating?",
    "What apology do I wish I had received?",
    "What moment changed me without me realizing it?",
    "What dream keeps returning to me?",
    "What do I admire about my own strength?",
    "In what moments do I shrink myself?",
    "What is one thing I want to prioritize in the next month?",
    "What emotion have I been suppressing?",
    "What do I miss that I haven’t admitted?",
    "What conversation am I avoiding?",
    "What do I believe is “too much” or “not enough” about me?",
    "What feels soothing to my nervous system?",
    "What is my biggest fear in relationships?",
    "What kind of love am I craving right now?",
    "What pattern do I fall into when I care too much?",
    "What am I working toward—even subconsciously?",
    "What do I want to be known for?",
    "What is the heaviest thing I’m holding emotionally?",
    "What do I want people to notice about me without me saying it?",
    "What am I tired of explaining?",
    "What part of myself am I becoming more aware of lately?",
    "What trait of mine is a strength I used to think was a flaw?",
    "What keeps showing up in my life as a sign?",
    "What is something I’m afraid to want?",
    "What makes me feel unlovable, and where did that belief came from?",
    "What insecurity shapes my choices the most?",
    "What do I do naturally that others admire?",
    "What am I learning to be patient with?",
    "What am I secretly excited about?",
    "What version of myself do I miss?",
]

# 2. Angel Numbers (9 Options)
ANGEL_NUMBERS = [
    "000", "111", "222", "333", "444", "555", "777", "888", "999"
]

# 3. Side Quests (31 Options)
SIDE_QUESTS = [
    "do 30 situps",
    "buy one healthy ingredient",
    "clean one drawer or one small area",
    "do a 2 minute stretch",
    "take a 5 minute walk outside",
    "read one page",
    "do 30 squats",
    "add a new pin on the vision board in pinterest",
    "write on substack",
    "read 3 article on substack",
    "throw away / give away one item that you dont use anymore",
    "create / recreate a new recipe",
    "delete one unused app / 2 unused video on your phone",
    "learn one chapter of cfa",
    "learn 5 new korean words",
    "listen to a podcast episode",
    "learn one facts about history or science",
    "buy yourself a tea / coffee",
    "try doing 20 burpees",
    "use your medicube for skin care",
    "do a 3 card tarot reading",
    "learn 1 new topic (it could be about anything)",
    "make one simple coding project",
    "solve 3 math problem",
    "read the bible's daily verse",
    "pray rosario",
    "write a line for a song",
    "do the splits",
    "research a myth or legend",
    "do today's wordle",
    "discover a random historical event that happened on this day",
]

def get_fortune_content_list(category):
    """Returns the correct global list of content based on category."""
    if category == 'reflective_message':
        return REFLECTIVE_MESSAGES
    elif category == 'angel_number':
        return ANGEL_NUMBERS
    elif category == 'side_quest':
        return SIDE_QUESTS
    return [] 

def crack_daily_fortune():
    """
    Generates a unique fortune combination based on randomization.
    Returns the fortune data dictionary or None if already cracked.
    """
    if check_if_cracked_today():
        # Load and return the fortune that was already cracked today
        today_date = datetime.now().strftime('%Y-%m-%d')
        conn = db_connect()
        c = conn.cursor()
        # NOTE: Removed vibe_of_day column
        row = c.execute("SELECT fortune_text, angel_number, side_quest FROM daily_fortunes WHERE reveal_date = ?", (today_date,)).fetchone()
        conn.close()
        if row:
            return {
                'fortune_text': row[0],
                'angel_number': row[1],
                'side_quest': row[2]
            }
        return None # Should not happen

    # --- ADVANCED RANDOMIZATION LOGIC ---
    now = datetime.now()
    
    # 1. Reflective Message (True Random from 60)
    msgs = get_fortune_content_list('reflective_message')
    fortune_text = random.choice(msgs) if msgs else "Default reflective message."
    
    # 2. Angel Number (9 Options - Dependent on Minute + Day)
    angels = get_fortune_content_list('angel_number')
    idx_angel = (now.minute + now.day) % len(angels)
    angel_number = angels[idx_angel] if angels else "N/A"
    
    # 3. Side Quest (31 Options - Dependent on Day of Year)
    quests = get_fortune_content_list('side_quest')
    idx_quest = (now.timetuple().tm_yday % len(quests)) 
    side_quest = quests[idx_quest] if quests else "N/A"
    
    # Vibe of the Day logic removed.
    
    # Save the new combination
    fortune_data = {
        'fortune_text': fortune_text,
        'angel_number': angel_number,
        'side_quest': side_quest
    }
    
    # Save the fortune data to the database
    save_daily_fortune(fortune_data) 
    
    return fortune_data


def save_daily_fortune(fortune_data):
    """Saves the cracked fortune data to the daily_fortunes table."""
    conn = db_connect()
    c = conn.cursor()
    reveal_date = datetime.now().strftime('%Y-%m-%d')

    try:
        # NOTE: Removed vibe_of_day column
        c.execute("""
            INSERT INTO daily_fortunes (fortune_text, angel_number, side_quest, reveal_date)
            VALUES (?, ?, ?, ?)
        """, (
            fortune_data['fortune_text'],
            fortune_data['angel_number'],
            fortune_data['side_quest'],
            reveal_date
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"DB Error saving daily fortune: {e}")
        return False
    finally:
        conn.close()

def load_fortune_history(search_query=""):
    """Loads all saved fortunes for the archive."""
    conn = db_connect()
    c = conn.cursor()
    
    # NOTE: Removed vibe_of_day column
    query = """
        SELECT id, fortune_text, angel_number, side_quest, reveal_date
        FROM daily_fortunes
    """
    params = []
    
    if search_query:
        # Search across the main fortune text and side quest
        query += " WHERE fortune_text LIKE ? OR side_quest LIKE ?"
        search_param = f"%{search_query}%"
        params = [search_param, search_param]
    
    query += " ORDER BY reveal_date DESC" 
    
    rows = c.execute(query, params).fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            'id': row[0],
            'fortune_text': row[1],
            'angel_number': row[2],
            'side_quest': row[3],
            'date': row[4]
        })
    return history

def check_if_cracked_today():
    """
    Queries the database to see if an entry already exists for the current date.
    Used to enforce the 'once-per-day' rule.
    """
    from datetime import datetime
    
    today_date = datetime.now().strftime('%Y-%m-%d')
    
    # Assumes db_connect() is a globally defined function
    conn = db_connect() 
    c = conn.cursor()
    
    try:
        # Check for an entry with today's date in the daily_fortunes table
        row = c.execute("SELECT id FROM daily_fortunes WHERE reveal_date = ?", (today_date,)).fetchone()
        
        # If row is not None (meaning a matching entry was found), return True
        return row is not None 
        
    except Exception as e:
        print(f"DB Error checking if cracked today: {e}")
        return False # Safely assume not cracked if there's a DB error
    finally:
        conn.close()

# --- CLOSURE BOX DB FUNCTIONS (GLOBAL) ---

def save_closure_entry(title, content, closure_type):
    """Saves a new emotional entry to the closure_box table."""
    if not title or not content:
        return False
        
    conn = db_connect()
    c = conn.cursor()
    
    # Get current timestamp for sealing the entry
    closure_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        c.execute("""
            INSERT INTO closure_box (title, content, closure_type, closure_date)
            VALUES (?, ?, ?, ?)
        """, (title, content, closure_type, closure_dt))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"DB Error saving closure entry: {e}")
        return False
    finally:
        conn.close()

def load_closure_entries(search_query=""):
    """
    Loads all closure entries, optionally filtered by title or content.
    Returns a list of dictionaries.
    """
    conn = db_connect()
    c = conn.cursor()
    
    query = """
        SELECT id, title, content, closure_type, closure_date
        FROM closure_box
    """
    params = []
    
    if search_query:
        # Case-insensitive search across title and content
        query += " WHERE title LIKE ? OR content LIKE ?"
        search_param = f"%{search_query}%"
        params = [search_param, search_param]
    
    query += " ORDER BY closure_date DESC" # Newest entries first
    
    rows = c.execute(query, params).fetchall()
    conn.close()
    
    entries = []
    for row in rows:
        entries.append({
            'id': row[0],
            'title': row[1],
            'content': row[2],
            'type': row[3],
            'date': row[4]
        })
        
    return entries

def delete_closure_entry(entry_id):
    """Permanently deletes an entry from the closure_box by its ID."""
    conn = db_connect()
    c = conn.cursor()
    
    try:
        c.execute("DELETE FROM closure_box WHERE id = ?", (entry_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"DB Error deleting closure entry: {e}")
        return False
    finally:
        conn.close()

def calculate_journal_streak(c):
    """Calculates the current consecutive journal streak."""
    streak = 0
    today = date.today()
    
    # Fetch all unique journal dates, ordered descending
    journal_dates = c.execute("SELECT DISTINCT date FROM journal ORDER BY date DESC").fetchall()
    
    if not journal_dates:
        return 0

    # Convert date strings to date objects
    dates = [datetime.strptime(d[0], '%Y-%m-%d').date() for d in journal_dates]
    
    current_date = today
    
    # Check if today is logged
    if dates and dates[0] == today:
        streak = 1
        current_date = today - timedelta(days=1)
    
    # Check back through history
    for d in dates:
        if d == current_date:
            streak += 1
            current_date -= timedelta(days=1)
        elif d < current_date:
            break  # Streak broken
    
    return streak

def fetch_dashboard_stats():
    """Fetches the latest Mood, Water, To-Do, and Journal stats for the Dashboard."""
    today_iso = date.today().isoformat()
    stats = {}

    conn = db_connect()
    c = conn.cursor()
    
    # --- Mood ---
    c.execute("SELECT mood_emoji FROM moods WHERE date = ?", (today_iso,))
    mood_result = c.fetchone()
    stats["Mood"] = mood_result[0] if mood_result else "❓"
    
    # --- Water ---
    c.execute("SELECT cups FROM water WHERE date = ?", (today_iso,))
    water_result = c.fetchone()
    current_cups = water_result[0] if water_result else 0
    stats["Water"] = f"{current_cups} cups 💧"
    
    # --- To-Do ---
    sql_total = """
    SELECT COUNT(id) FROM todos
    WHERE created_date = ? OR (completed = 0 AND created_date < ?)
    """
    c.execute(sql_total, (today_iso, today_iso))
    total_tasks = c.fetchone()[0]
    
    sql_completed = """
    SELECT COUNT(id) FROM todos
    WHERE completed = 1 AND created_date = ?
    """
    c.execute(sql_completed, (today_iso,))
    completed_tasks = c.fetchone()[0]
    
    stats["Tasks Done"] = f"{completed_tasks} / {total_tasks} ✅"
    
    # --- Journal Streak ---
    journal_streak = calculate_journal_streak(c)
    stats["Journal"] = f"{journal_streak}-day streak ✍🏼"
    
    conn.close()
    return stats

# --------------------- Root window ---------------------
root = tk.Tk()
root.title("Mochi • Planner")
root.geometry("900x800")
root.minsize(500, 300)

# assuming root is the main Tk window
global content_frame
content_frame = tk.Frame(root, bg=theme()["BG"])
content_frame.pack(side="right", fill="both", expand=True)

# Dictionary to hold special widgets for easy access (e.g., for theming)
special_widgets = {} 
todos_task_widgets = {} # Dictionary to hold task labels/checkboxes

# --------------------- Sidebar visibility management ---------------------
sidebar_width = 200
sidebar_visible = True

# Frame to hold the sidebar show button when sidebar is hidden
sidebar_show_container = tk.Frame(root, width=28)
# DO NOT pack yet

def show_sidebar():
    global sidebar_visible
    sidebar_show_container.pack_forget() # Hide the show button container
    sidebar_container.pack(side="left", fill="y")
    main_area.pack_configure(padx=(12, 12)) # Re-adjust padding for main area
    sidebar_visible = True

def hide_sidebar():
    global sidebar_visible
    if sidebar_visible:
        sidebar_container.pack_forget()
        # Pack the show button container when hiding the sidebar
        sidebar_show_container.pack(side="left", fill="y", padx=(4, 0)) 
        main_area.pack_configure(padx=(12, 12)) # Main area will expand
        sidebar_visible = False
    else:
        show_sidebar()

# Create the button that appears when the sidebar is hidden
show_sidebar_btn = tk.Button(sidebar_show_container, text="▶", font=("Segoe UI", 10), 
                             command=show_sidebar, relief="flat", bd=0)
show_sidebar_btn.pack(pady=40, padx=4)

# --------------------- Header (Define widgets before main logic) ---------------------
header = tk.Frame(root, height=64)
header.pack(fill="x")
title_label = tk.Label(header, text="Mochi ✿ Journal", font=TITLE_FONT)
title_label.pack(side="left", padx=18, pady=12)

theme_btn = tk.Button(header, text=current_theme_name, font=BTN_FONT, command=cycle_theme, relief="flat", bd=0)
theme_btn.pack(side="right", padx=12, pady=12)

# --------------------- Sidebar (compact, scrollable) ---------------------
sidebar_container = tk.Frame(root)
sidebar_container.pack(side="left", fill="y")
# show_sidebar_container is defined but not packed initially

# collapse sidebar whole (hamburger)
hamburger = tk.Button(sidebar_container, text="≡", font=BTN_FONT, command=hide_sidebar, relief="flat", bd=0)
hamburger.pack(padx=6, pady=6, anchor="nw")

canvas = tk.Canvas(sidebar_container, width=sidebar_width, highlightthickness=0)
canvas.pack(side="left", fill="y", expand=False)

vsb = ttk.Scrollbar(sidebar_container, orient="vertical", command=canvas.yview)
vsb.pack(side="left", fill="y")
canvas.configure(yscrollcommand=vsb.set)

inner = tk.Frame(canvas)
canvas.create_window((0,0), window=inner, anchor="nw")

def on_inner_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))
inner.bind("<Configure>", on_inner_configure)

# --------------------- Main area (pages) ---------------------
main_area = tk.Frame(root)
main_area.pack(side="right", fill="both", expand=True, padx=12, pady=12)

pages = {}
active_page_name = "HomeHub"
sidebar_buttons = []
section_headers = []
button_to_page = {}

# --------------------- Forward Declaration of task functions for show_page ---------------------
# Dummy function to be replaced later, prevents initial NameError
def load_tasks_dummy():
    pass 

def show_page(name):
    global active_page_name
    active_page_name = name
    
    for widget in content_frame.winfo_children():
        widget.destroy()
        
    # hide all
    for p in pages.values():
        p.pack_forget()
    pages[name].pack(fill="both", expand=True)
    highlight_active(name)
    
    # Reload logic when switching pages
    if name == "HomeHub" and hasattr(pages[name], 'update_ui'): # <-- Make sure this is present!
        pages[name].update_ui()                                    
        
    if name == "To-Do" and hasattr(pages[name], 'load_tasks'):
        pages[name].load_tasks() 
    if name == "Water" and hasattr(pages[name], 'load_water_count_today'):
        pages[name].load_water_count_today()

def highlight_active(page_name):
    global active_page_name
    active_page_name = page_name
    t = theme()
    for b in sidebar_buttons:
        txt = b.cget("text").strip()
        # Remove leading emoji/spaces for matching — compare using button_to_page map
        if txt in button_to_page and button_to_page[txt] == page_name:
            # active style
            b.configure(bg=t["ACCENT"])
        else:
            b.configure(bg=t["BTN"])

# --------------------- Sidebar button & UI helpers ---------------------
def make_sidebar_button(parent, text, page_name=None):
    t = theme()
    btn = tk.Button(parent,
                     text=text,  # <-- NO manual spaces here
                     font=BTN_FONT,
                     anchor="w",
                     relief="flat",
                     bd=0,
                     padx=18, # <-- INCREASED PADX for alignment with header emoji
                     pady=8,
                     bg=t["BTN"],
                     fg=t["TEXT"],
                     activebackground=t["BTN_HOVER"])
    btn.pack(fill="x", pady=4)
    if page_name:
        btn.config(command=lambda: show_page(page_name))
        button_to_page[text.strip()] = page_name # Use stripped text for the map
    # hover
    def on_enter(e):
        btn.configure(bg=t["BTN_HOVER"])
    def on_leave(e):
        # Only revert color if not the active button
        if button_to_page.get(text.strip()) != active_page_name:
            btn.configure(bg=t["BTN"])
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    sidebar_buttons.append(btn)
    return btn


# --------------------- Build collapsible sections ---------------------
sections = {
    "Home": [
        ("🏠 Home Hub", "HomeHub")
    ],

    "Life & Productivity": [
        ("📂 Life & Productivity Hub", "ProductivityHub")
    ],

    "Self Tracking": [
        ("💗 Self Tracking Hub", "SelfHub")
    ],

    "Knowledge, Notes & Thinking": [
        ("🧠 Knowledge Hub", "KnowledgeHub")
    ],

    "Journaling": [
        ("📓 Journaling Hub", "JournalHub")
    ],

    "Lifestyle & Media": [
        ("🎨 Lifestyle & Media Hub", "LifestyleHub")
    ],

    "Finance": [
        ("💰 Finance Hub", "FinanceHub")
    ],

    "Others": [
        ("✨ Others Hub", "OthersHub")
    ]
}

# ---------- Sidebar Hubs ----------
sidebar_hubs = {
    "Home Hub": "HomeHub",
    "Life & Productivity Hub": "ProductivityHub",
    "Self Tracking Hub": "SelfHub",
    "Knowledge Hub": "KnowledgeHub",
    "Journaling Hub": "JournalHub",
    "Lifestyle & Media Hub": "LifestyleHub",
    "Finance Hub": "FinanceHub",
    "Others Hub": "OthersHub"
}

for hub_label, hub_page in sidebar_hubs.items():
    make_sidebar_button(inner, hub_label, hub_page)
    
hub_features = {
    "ProductivityHub": [
        ("Calendar", "📅", "Calendar"),
        ("Weekly Overview", "🗓️", "WeeklyOverview"),
        ("Monthly Overview", "📆", "MonthlyOverview"),
        ("Time Blocking", "⏰", "Time Blocking"),
        ("To-Do / Tasks", "✅", "To-Do"),
        ("Project", "📊", "Project"),
        ("Reminders", "⏳", "Due Items"),
        ("Events Countdown", "⏱️", "Countdown")
    ],

    "SelfHub": [
        ("Mood", "🌸", "Mood"),
        ("Sleep", "🛌", "Sleep"),
        ("Diet", "🍽️", "Diet"),
        ("Water", "💧", "Water"),
        ("Body Metrics", "⚖️", "Weight"),
        ("Period Tracker", "🩸", "Period"),
        ("Workout", "🏋️", "Workout"),
        ("Calories", "🍎", "Calories"),
        ("Habits", "📌", "Habits")
    ],

    "KnowledgeHub": [
        ("Commonplace Book", "📒", "Commonplace"),
        ("Flashcards", "🧠", "Flashcard"),
        ("Collapsible Notes", "🗂️", "Notes"),
        ("Braindump", "💡", "Braindump"),
        ("Songs / Songwriting", "♫", "Songwriting"),
        ("Study Session Log", "⏲️", "Focus Log")
    ],

    "JournalHub": [
        ("Journal Page", "📓", "Journal"),
        ("Tarot Page", "🔮", "Tarot"),
        ("Closure Box", "📦", "ClosureBox"),
        ("Daily Fortune Cookie", "🥠", "FortuneCookie"),
        ("Version of Me Tracker", "👤", "VersionMe")
    ],

    "LifestyleHub": [
        ("Media Consumption", "📚", "MediaLog"),
        ("Groceries", "🛒", "Groceries"),
        ("Recipes", "📖", "Recipes")
    ],

    "FinanceHub": [
        ("Finance Tracker", "💰", "Finance"),
        ("Wishlist", "🛍️", "Wishlist")
    ],

    "OthersHub": [
        ("Pick For Me", "🎲", "Randomizer"),
        ("Mini Games", "🎮", "MiniGames")
    ]
}

# --------------------- Create pages (placeholders + basic working widgets) ---------------------
def create_page(name, headline=None):
    p = tk.Frame(main_area)
    p.configure(bg=theme()["CARD"])
    h = tk.Label(p, text=headline or name, font=("Segoe UI", 14, "bold"), bg=theme()["CARD"], fg=theme()["TEXT"])
    h.pack(anchor="nw", pady=12, padx=12)
    # Add placeholder content area
    content = tk.Frame(p, bg=theme()["CARD"])
    content.pack(fill="both", expand=True, padx=12, pady=8)
    # return page frame and content reference
    return p, content

# Create pages for every unique page name in sections
page_names = set()
for items in sections.values():
    for _, page in items:
        page_names.add(page)
        
for feature_list in hub_features.values():
    for _, _, page in feature_list:
        page_names.add(page)
        
def build_hub_page(content, cards):
    tk.Label(
        content,
        text="Choose a section",
        font=("Segoe UI", 14, "bold"),
        bg=theme()["CARD"],
        fg=theme()["TEXT"]
    ).pack(anchor="w", padx=10, pady=(10,5))

    frame = tk.Frame(content, bg=theme()["CARD"])
    frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    def bind_all_children(widget, func):
        widget.bind("<Button-1>", func)
        for child in widget.winfo_children():
            bind_all_children(child, func)

    def make_hub_card(parent, title, emoji, page, row, col):
        card = tk.Frame(
            parent, bg=theme()["BG"],
            padx=12, pady=12, cursor="hand2",
            width=160, height=160
        )
        card.grid(row=row, column=col, padx=10, pady=10)
        card.grid_propagate(False)

        inner = tk.Frame(card, bg=theme()["BG"])
        inner.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(inner, text=emoji, font=("Segoe UI Emoji", 35),
                bg=theme()["BG"], fg=theme()["TEXT"]).pack()
        tk.Label(inner, text=title, font=("Segoe UI", 11, "bold"),
                bg=theme()["BG"], fg=theme()["TEXT"]).pack()

        card.bind("<Button-1>", lambda e: show_page(page))
        for w in card.winfo_children():
            w.bind("<Button-1>", lambda e: show_page(page))
            
        bind_all_children(card, lambda e: show_page(page))

    max_cols = 3
    for i, (title, emoji, page) in enumerate(cards):
        row, col = divmod(i, max_cols)
        make_hub_card(frame, title, emoji, page, row, col)

# ---------- Hub Pages ----------
hub_pages = ["HomeHub", "LifeHub", "SelfHub", "KnowledgeHub", "JournalHub",
             "LifestyleHub", "FinanceHub", "OthersHub"]

def build_hub_page(content, cards):
            tk.Label(
                content,
                text="Choose a section",
                font=("Segoe UI", 14, "bold"),
                bg=theme()["CARD"],
                fg=theme()["TEXT"]
            ).pack(anchor="w", padx=10, pady=(10,5))

            frame = tk.Frame(content, bg=theme()["CARD"])
            frame.pack(fill="both", expand=True, padx=10, pady=10)

            def make_card(parent, title, emoji, page, row, col):
                card = tk.Frame(
                    parent, bg=theme()["BG"],
                    padx=12, pady=12, cursor="hand2",
                    width=160, height=160
                )
                card.grid(row=row, column=col, padx=10, pady=10)
                card.grid_propagate(False)

                inner = tk.Frame(card, bg=theme()["BG"])
                inner.place(relx=0.5, rely=0.5, anchor="center")

                tk.Label(inner, text=emoji, font=("Segoe UI Emoji", 35),
                        bg=theme()["BG"], fg=theme()["TEXT"]).pack()
                tk.Label(inner, text=title, font=("Segoe UI", 11, "bold"),
                        bg=theme()["BG"], fg=theme()["TEXT"]).pack()

                card.bind("<Button-1>", lambda e: show_page(page))
                for w in card.winfo_children():
                    w.bind("<Button-1>", lambda e: show_page(page))

            for i, (title, emoji, page) in enumerate(cards):
                row, col = divmod(i, 3)
                make_card(frame, title, emoji, page, row, col)

for hub in hub_pages:
    pg, content = create_page(hub, headline=hub.replace("Hub", " Hub"))
    pages[hub] = pg
    
for pn in page_names:

    pg, content = create_page(pn, headline=pn + " Page")
    pages[pn] = pg

    if pn in hub_features:
        build_hub_page(content, hub_features[pn])

    # Example small content for a few important pages:
    if pn == "HomeHub":
        from datetime import date
        import calendar
        import tkinter as tk

        # --- UI Setup ---
        today_text = date.today().strftime("%A, %B %d, %Y")
        
        # Greeting
        tk.Label(
            content, text=f"Welcome back, Mochi! ✨", 
            font=("Segoe UI", 14, "bold"),
            bg=theme()["CARD"], fg=theme()["TEXT"]
        ).pack(anchor="nw", pady=(6,0), padx=6)

        tk.Label(
            content, text=today_text, 
            font=("Segoe UI", 11),
            bg=theme()["CARD"], fg=theme()["TEXT"]
        ).pack(anchor="nw", pady=(0,10), padx=6)

        # Dashboard container: left (cards) + right (calendar)
        main_dash = tk.Frame(content, bg=theme()["CARD"])
        main_dash.pack(fill="both", expand=True)

        left = tk.Frame(main_dash, bg=theme()["CARD"])
        left.pack(side="left", fill="both", expand=True)

        right = tk.Frame(main_dash, bg=theme()["CARD"])
        right.pack(side="right", fill="y", padx=10)

        # --- Daily stats section ---
        stats_frame = tk.Frame(left, bg=theme()["CARD"])
        stats_frame.pack(fill="x", padx=6, pady=6)

        stat_labels = {}
        initial_stats = {
            "Mood": "❓",
            "Tasks Done": "0 / 0 ✅",
            "Water": "0 cups 💧",
            "Journal": "0-day streak ✍🏼"
        }

        for name, val in initial_stats.items():
            lbl = tk.Label(
                stats_frame, text=f"{name}: {val}",
                bg=theme()["CARD"], fg=theme()["TEXT"],
                font=("Segoe UI", 10)
            )
            lbl.pack(anchor="w")
            stat_labels[name] = lbl

        # --- Refresh Function for Dashboard ---
        def update_dashboard_ui():
            stats = fetch_dashboard_stats()
            stat_labels["Mood"].config(text=f"Mood: {stats['Mood']}")
            stat_labels["Water"].config(text=f"Water: {stats['Water']}")
            stat_labels["Tasks Done"].config(text=f"Tasks Done: {stats['Tasks Done']}")
            stat_labels["Journal"].config(text=f"Journal: {stats['Journal']}")

        pg.update_ui = update_dashboard_ui
        pg.update_ui()

        # --- Responsive card grid ---
        card_frame = tk.Frame(left, bg=theme()["CARD"])
        card_frame.pack(fill="both", expand=True, padx=6, pady=(0,10))

        cards = [
            ("Mood", "🌸", "Mood"),
            ("Tasks", "📌", "To-Do"),
            ("Journal", "📓", "Journal"),
            ("Water", "💧", "Water")
        ]

        def make_card(parent, title, emoji, page, row, col):
            card = tk.Frame(
                parent, bg=theme()["BG"],
                padx=12, pady=12, cursor="hand2",
                height=130, width=120
            )
            card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
            card.grid_propagate(False)

            # Center emoji and text vertically using a grid layout
            inner = tk.Frame(card, bg=theme()["BG"])
            inner.place(relx=0.5, rely=0.5, anchor="center")

            # Adjust emoji font size for consistent height
            emoji_font = ("Segoe UI Emoji", 30)

            emoji_label = tk.Label(
                inner, text=emoji, font=emoji_font,
                bg=theme()["BG"], fg=theme()["TEXT"]
            )
            emoji_label.pack(pady=(0, 5))  # small space between icon and text

            title_label = tk.Label(
                inner, text=title,
                font=("Segoe UI", 11, "bold"),
                bg=theme()["BG"], fg=theme()["TEXT"]
            )
            title_label.pack()

            # Click binding
            def open_page(event):
                show_page(page)
            card.bind("<Button-1>", open_page)
            for w in card.winfo_children():
                w.bind("<Button-1>", open_page)

        # --- Create cards dynamically in a grid ---
        max_cols = 2
        for i, (title, emoji, page) in enumerate(cards):
            row, col = divmod(i, max_cols)
            make_card(card_frame, title, emoji, page, row, col)

        # Configure grid weights
        total_rows = (len(cards) + max_cols - 1) // max_cols
        for r in range(total_rows):
            card_frame.grid_rowconfigure(r, weight=1)
        for c in range(max_cols):
            card_frame.grid_columnconfigure(c, weight=1)

        # --- Mini Calendar ---
        tk.Label(
            right, text="Mini Calendar 📅", 
            font=("Segoe UI", 11, "bold"),
            bg=theme()["CARD"], fg=theme()["TEXT"]
        ).pack(pady=(0,4))

        cal = calendar.TextCalendar(calendar.SUNDAY)
        cal_text = cal.formatmonth(date.today().year, date.today().month)
        tk.Label(
            right, text=cal_text,
            font=("Consolas", 9),
            justify="left",
            bg=theme()["CARD"], fg=theme()["TEXT"]
        ).pack()
        
        # ----------------- Focus Timer Widget -----------------
        focus_widget = tk.Frame(right, bg="white", bd=0)
        focus_widget.pack(fill="x", pady=10)

        tk.Label(focus_widget, text="🌱 Focus Timer", bg="white",
                fg="#333", font=("Segoe UI", 14, "bold")).pack(anchor="w")

        tk.Label(focus_widget, text="Purpose:", bg="white",
                fg="#555", font=("Segoe UI", 10)).pack(anchor="w", pady=(5,0))
        focus_purpose_entry = tk.Entry(focus_widget, bg="#ffe6ef", fg="#000", font=("Segoe UI", 10))
        focus_purpose_entry.pack(fill="x", pady=2)

        tk.Label(focus_widget, text="Set Duration (minutes):", bg="white",
                fg="#555", font=("Segoe UI", 10)).pack(anchor="w", pady=(5,0))
        duration_entry = tk.Entry(focus_widget, bg="#ffe6ef", fg="#000", font=("Segoe UI", 10))
        duration_entry.insert(0, "25")  # default 25 minutes
        duration_entry.pack(fill="x", pady=2)

        focus_timer_var = tk.StringVar(value="25:00")
        tk.Label(focus_widget, textvariable=focus_timer_var,
                bg="white", fg="#ff5d8f", font=("Segoe UI", 32, "bold")).pack(pady=5)

        # ----------------- Timer Logic -----------------
        focus_state = {"running": False, "seconds_left": 1500}

        def update_focus_timer():
            if focus_state["running"]:
                if focus_state["seconds_left"] > 0:
                    mins = focus_state["seconds_left"] // 60
                    secs = focus_state["seconds_left"] % 60
                    focus_timer_var.set(f"{mins:02d}:{secs:02d}")
                    focus_state["seconds_left"] -= 1
                    focus_widget.after(1000, update_focus_timer)
                else:
                    focus_state["running"] = False
                    focus_timer_var.set("Done!")
                    save_focus_session(success=1)

        def start_focus_timer():
            if not focus_state["running"]:
                try:
                    mins = int(duration_entry.get())
                    focus_state["seconds_left"] = mins * 60
                except ValueError:
                    focus_state["seconds_left"] = 1500  # fallback
                focus_state["running"] = True
                update_focus_timer()

        def stop_focus_timer():
            if focus_state["running"]:
                focus_state["running"] = False
                save_focus_session(success=0)
                focus_timer_var.set("Stopped")
                
        def get_today_focus_minutes():
            conn = db_connect()
            c = conn.cursor()
            row = c.execute("""
                SELECT SUM(duration_minutes)
                FROM focus_sessions_new
                WHERE focus_date = date('now')
            """).fetchone()
            conn.close()
            return row[0] if row and row[0] else 0

        def save_focus_session(success):
            purpose = focus_purpose_entry.get().strip()
            duration = round((int(duration_entry.get()) if duration_entry.get().isdigit() else 25))
            conn = db_connect()
            c = conn.cursor()
            c.execute("""
                INSERT INTO focus_sessions_new (focus_date, duration_minutes, purpose, success)
                VALUES (date('now'), ?, ?, ?)
            """, (duration, purpose, success))
            conn.commit()
            conn.close()

        # ----------------- Buttons -----------------
        
        # Widget display
        today_focus_var = tk.StringVar()
        today_focus_var.set(f"{get_today_focus_minutes()} min focused today")

        tk.Label(focus_widget, textvariable=today_focus_var,
                bg="white", fg="#ff5d8f", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(2,5))
        
        buttons_frame = tk.Frame(focus_widget, bg="white")
        buttons_frame.pack(pady=5)

        tk.Button(buttons_frame, text="Start", bg="#ff5d8f", fg="white",
                font=("Segoe UI", 10, "bold"), width=10, command=start_focus_timer).grid(row=0, column=0, padx=5)
        tk.Button(buttons_frame, text="Stop", bg="#ffb6c8", fg="white",
                font=("Segoe UI", 10, "bold"), width=10, command=stop_focus_timer).grid(row=0, column=1, padx=5)
        
        # --- DUE REMINDERS WIDGET ---
        dashboard_due_frame = tk.Frame(right, bg=theme()["CARD"])
        dashboard_due_frame.pack(fill="x", pady=6)
        tk.Label(dashboard_due_frame, text="📌 Upcoming Due Items",
                bg=theme()["CARD"], fg="#333", font=("Arial", 12, "bold")).pack(anchor="w", padx=4)

        due_labels = []

        def refresh_due_widget():
            for lbl in due_labels:
                lbl.destroy()
            due_labels.clear()

            conn = db_connect()
            c = conn.cursor()
            rows = c.execute("""
                SELECT title, due_date FROM due_items
                WHERE status='Pending'
                ORDER BY due_date ASC LIMIT 3
            """).fetchall()
            conn.close()

            for title, due_date in rows:
                lbl = tk.Label(dashboard_due_frame, text=f"{title} — {due_date}",
                            bg=theme()["CARD"], fg="#ff5d8f", font=("Arial", 10))
                lbl.pack(anchor="w", padx=8)
                due_labels.append(lbl)

        refresh_due_widget()
    
    # Randomizer Page
    if pn == "Randomizer":
        import tkinter as tk
        from tkinter import ttk, messagebox
        import json
        import random
        import time
        
        # --- UI GLOBALS ---
        current_list_id = None
        list_text_area = None # Text widget for input/editing items
        result_label = None   # Label to show the final result
        
        # Define the theme function if not globally available
        def theme():
            return {
                "BG": "#fff1f3",
                "SIDEBAR": "#ffe6ea",
                "CARD": "#ffffff",
                "BTN": "#ffd7dd",
                "BTN_HOVER": "#ffb6c2",
                "TEXT": "#2b2b2b",
                "TEXT_SECONDARY": "#888888",
                "ACCENT": "#ffdfe6"
            }

        # --- LIST UTILITIES (Client-Side) ---

        def parse_items_from_text(text_content):
            """
            Parses the text area input into a dictionary format suitable for JSON storage:
            {'item': 'Pizza', 'weight': 1}
            Handles simple one-item-per-line input.
            """
            items = []
            for line in text_content.splitlines():
                line = line.strip()
                if not line:
                    continue
                
                # Simple parsing: assumes item and weight are separated by '|' if weights are used
                parts = line.split('|')
                item_name = parts[0].strip()
                weight = 1
                
                # If weight is explicitly provided (e.g., "Pizza | 3")
                if len(parts) > 1 and parts[1].strip().isdigit():
                    weight = int(parts[1].strip())
                
                items.append({'item': item_name, 'weight': weight})
            return items

        def format_items_for_text(items_list):
            """Formats the list of item dictionaries back into a string for the text area."""
            lines = []
            for item in items_list:
                if item.get('weight', 1) > 1:
                    lines.append(f"{item['item']} | {item['weight']}")
                else:
                    lines.append(item['item'])
            return "\n".join(lines)


        # --- RANDOMIZER CORE LOGIC ---

        def run_randomizer():
            """Picks a random item based on weights and initiates the visual spin."""
            
            # 1. Get items from the current text area
            text_content = list_text_area.get("1.0", tk.END).strip()
            if not text_content:
                messagebox.showerror("Error", "Please add items to the list first.")
                return

            items = parse_items_from_text(text_content)
            if not items:
                messagebox.showerror("Error", "List is empty after parsing.")
                return

            # 2. Prepare weighted list for random choice
            weighted_list = []
            for item in items:
                weighted_list.extend([item['item']] * item.get('weight', 1))

            if not weighted_list:
                messagebox.showerror("Error", "Weighted list is empty.")
                return

            # 3. Pick the result
            chosen_item = random.choice(weighted_list)
            
            # 4. Initiate visual spin effect (using Tkinter's after method for animation)
            visual_spin(items, chosen_item)


        def visual_spin(items, final_item, duration=1500):
            """Creates a visual scrolling/shuffling effect before revealing the result."""
            
            start_time = time.time()
            spin_frame = tk.Frame(list_text_area.master, bg=theme()["CARD"])
            
            # Temporarily hide the text area and show the spin frame
            list_text_area.grid_remove() 
            spin_frame.grid(row=0, column=0, columnspan=2, sticky="nsew") 

            # Create labels for the spin
            spin_labels = []
            for i in range(10): # Show 10 items in the spin visual
                label = tk.Label(spin_frame, text="", font=("Segoe UI", 14, "bold"), 
                                bg=theme()["CARD"], fg=theme()["TEXT"])
                label.pack(fill="x", pady=2)
                spin_labels.append(label)

            def animate():
                elapsed = (time.time() - start_time) * 1000
                
                if elapsed < duration:
                    # Still spinning: shuffle and pick a random center item
                    random.shuffle(items)
                    
                    # Highlight the center item (which is the 5th label)
                    for i, label in enumerate(spin_labels):
                        item_name = items[(i + int(elapsed / 100)) % len(items)]['item']
                        label.config(text=item_name, 
                                    fg="#ff66b2" if i == 5 else theme()["TEXT"])
                    
                    # Call animate again after a short delay
                    list_text_area.master.after(50, animate)
                else:
                    # Spin finished: display the final result clearly
                    spin_frame.destroy()
                    list_text_area.grid() # Bring back the text area
                    result_label.config(text=f"✨ {final_item} ✨", fg="#ff66b2")
            
            # Start animation
            result_label.config(text="...Picking...")
            animate()


        # --- LIST MANAGEMENT ACTIONS ---

        def load_selected_list(list_id, list_name):
            """Loads the items for the given list ID into the text area."""
            global current_list_id
            
            try:
                # Assumes load_list_by_id is global
                list_data = load_list_by_id(list_id)
            except NameError:
                messagebox.showerror("Setup Error", "'load_list_by_id' DB function is not defined globally.")
                return
                
            if list_data:
                current_list_id = list_id
                items_list = json.loads(list_data['items_data_json'])
                
                # Update Text Area
                list_text_area.delete("1.0", tk.END)
                list_text_area.insert("1.0", format_items_for_text(items_list))
                
                # Update Header
                list_edit_frame.config(text=f"📝 Editing: {list_name}")
                save_button.config(text="💾 Update List")
                result_label.config(text="Ready to Pick!")
            else:
                messagebox.showerror("Error", "Failed to load list data.")


        def save_current_list():
            """Saves or updates the list currently in the text area."""
            global current_list_id
            
            # 1. Get name
            list_name = simpledialog.askstring("Save List", "Enter a name for this list:", parent=content)
            if not list_name: return

            # 2. Parse items
            text_content = list_text_area.get("1.0", tk.END).strip()
            if not text_content:
                messagebox.showerror("Error", "List is empty.")
                return
                
            items_list = parse_items_from_text(text_content)
            if not items_list:
                messagebox.showerror("Error", "No valid items found in the list.")
                return
                
            items_json = json.dumps(items_list)
            
            # 3. Save to DB
            try:
                # Assumes save_list is global
                if save_list(list_name, items_json, current_list_id):
                    messagebox.showinfo("Success", f"List '{list_name}' saved successfully!")
                    refresh_list_sidebar()
                    if not current_list_id: # If new, set the new ID
                        # Best practice: reload to get the new ID, but for simplicity, we refresh the sidebar
                        pass 
                else:
                    messagebox.showerror("Error", f"Failed to save list (Name conflict or DB issue).")
            except NameError:
                messagebox.showerror("Setup Error", "'save_list' DB function is not defined globally.")


        def new_list():
            """Clears the text area to start a new, unsaved list."""
            global current_list_id
            current_list_id = None
            list_text_area.delete("1.0", tk.END)
            list_edit_frame.config(text="📝 New List")
            save_button.config(text="💾 Save New List")
            result_label.config(text="Enter items below!")


        def delete_selected_list_action(list_id, list_name):
            """Confirms and deletes a saved list."""
            
            response = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the list '{list_name}'?")
            if response:
                try:
                    # Assumes delete_list is global
                    if delete_list(list_id):
                        messagebox.showinfo("Deleted", f"List '{list_name}' deleted.")
                        refresh_list_sidebar()
                        # If deleting the current list, start a new one
                        if current_list_id == list_id:
                            new_list() 
                    else:
                        messagebox.showerror("Error", "Failed to delete list.")
                except NameError:
                    messagebox.showerror("Error", "'delete_list' DB function is not defined globally.")


        def refresh_list_sidebar():
            """Clears and repopulates the list selection sidebar."""
            
            # Clear all widgets except the 'New List' button
            for widget in list_select_frame.winfo_children():
                if widget.winfo_name() != 'new_list_button':
                    widget.destroy()

            try:
                # Assumes load_list_names is global
                lists = load_list_names()
            except NameError:
                tk.Label(list_select_frame, text="DB Functions Missing", bg=theme()["SIDEBAR"]).pack(pady=10)
                return

            if not lists:
                tk.Label(list_select_frame, text="No Saved Lists Yet.", bg=theme()["SIDEBAR"]).pack(pady=10, padx=5)
                return
            
            tk.Label(list_select_frame, text="--- Saved Wheels ---", 
                    bg=theme()["SIDEBAR"], fg=theme()["TEXT_SECONDARY"]).pack(fill="x", pady=(5, 0))

            for lst in lists:
                # Main button to load the list
                btn = tk.Button(list_select_frame, text=lst['name'], 
                                command=lambda id=lst['id'], name=lst['name']: load_selected_list(id, name),
                                bg=theme()["CARD"], fg=theme()["TEXT"], 
                                font=("Segoe UI", 10), anchor="w", bd=1, relief="flat")
                btn.pack(fill="x", padx=5, pady=2)
                
                # Context Menu for right-click actions (Delete)
                context_menu = tk.Menu(content, tearoff=0, bg=theme()["CARD"], fg=theme()["TEXT"])
                context_menu.add_command(label="Delete List", command=lambda id=lst['id'], name=lst['name']: delete_selected_list_action(id, name))
                
                # Bind right-click event
                btn.bind("<Button-3>", lambda event, menu=context_menu: menu.post(event.x_root, event.y_root))


        # ----------------------------------------
        # --- MAIN UI LAYOUT ---
        # ----------------------------------------
        
        for widget in content.winfo_children():
            widget.destroy()

        main_frame = tk.Frame(content, bg=theme()["BG"])
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Use PanedWindow for adjustable columns
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill="both", expand=True)

        # --- LEFT SIDEBAR: List Selector ---
        list_select_frame = tk.Frame(paned_window, bg=theme()["SIDEBAR"], width=200)
        paned_window.add(list_select_frame, weight=0)
        
        # New List Button
        new_btn = tk.Button(list_select_frame, text="➕ Start New List", command=new_list, 
                            bg=theme()["BTN_HOVER"], fg=theme()["TEXT"], 
                            font=("Segoe UI", 10, "bold"), name='new_list_button')
        new_btn.pack(fill="x", padx=5, pady=(10, 5))


        # --- RIGHT MAIN AREA: Editor and Randomizer ---
        main_randomizer_frame = tk.Frame(paned_window, bg=theme()["ACCENT"])
        paned_window.add(main_randomizer_frame, weight=1)
        
        # Grid configuration for the main area
        main_randomizer_frame.grid_columnconfigure(0, weight=1)
        main_randomizer_frame.grid_columnconfigure(1, weight=1)
        
        # --- TOP: Result and Controls ---
        
        # Result Label
        result_label = tk.Label(main_randomizer_frame, text="Welcome! Enter items to start.", 
                                bg=theme()["ACCENT"], fg=theme()["TEXT"], 
                                font=("Segoe UI", 20, "bold"))
        result_label.grid(row=0, column=0, columnspan=2, sticky="n", pady=15, padx=10)
        
        # Spin Button
        spin_button = tk.Button(main_randomizer_frame, text="🎰 PICK FOR ME!", command=run_randomizer,
                                bg="#ff66b2", fg="white", 
                                font=("Segoe UI", 16, "bold"), padx=20, pady=10)
        spin_button.grid(row=1, column=0, columnspan=2, pady=10)

        # --- MIDDLE: List Editor ---
        
        list_edit_frame = tk.LabelFrame(main_randomizer_frame, text="📝 New List", 
                                    bg=theme()["CARD"], fg=theme()["TEXT"], padx=10, pady=10)
        list_edit_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(10, 5), rowspan=2)
        list_edit_frame.grid_columnconfigure(0, weight=1)
        list_edit_frame.grid_rowconfigure(0, weight=1)

        # Text Area for Items
        list_text_area = tk.Text(list_edit_frame, wrap="word", bg=theme()["CARD"], fg=theme()["TEXT"], 
                                font=("Segoe UI", 10), height=15)
        list_text_area.insert("1.0", "Enter one item per line.\nOptionally use weights: Item | 3")
        list_text_area.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Save Button
        save_button = tk.Button(list_edit_frame, text="💾 Save New List", command=save_current_list,
                                bg=theme()["BTN"], fg=theme()["TEXT"], 
                                font=("Segoe UI", 10, "bold"))
        save_button.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        # --- Initial Load ---
        refresh_list_sidebar()
    
    # Version of Me Tracker Page
    if pn == "VersionMe":
        import tkinter as tk
        from tkinter import ttk, messagebox
        from datetime import datetime
        
        # --- UI GLOBALS ---
        form_entries = {} # Dictionary to hold form Entry widgets
        history_list_frame = None
        
        # Define the theme function if not globally available
        def theme():
            return {
                "BG": "#fff1f3",
                "SIDEBAR": "#ffe6ea",
                "CARD": "#ffffff",
                "BTN": "#ffd7dd",
                "BTN_HOVER": "#ffb6c2",
                "TEXT": "#2b2b2b",
                "TEXT_SECONDARY": "#888888",
                "ACCENT": "#ffdfe6"
            }
            
        # --- UI ACTION FUNCTIONS ---
        
        def save_snapshot_action():
            """Gathers data from the form and saves it to the DB."""
            
            # 1. Gather Data
            data = {}
            required_keys = ['weight', 'songs', 'foods', 'obsession', 'main_activity', 'media_consumption']
            
            try:
                for key in required_keys:
                    value = form_entries[key].get().strip()
                    if not value:
                        messagebox.showerror("Missing Data", f"Please fill out the '{key.replace('_', ' ').title()}' field.")
                        return
                    
                    # Special handling for weight (needs to be float/real)
                    if key == 'weight':
                        data[key] = float(value)
                    else:
                        data[key] = value

            except ValueError:
                messagebox.showerror("Input Error", "Weight must be a valid number.")
                return
            except NameError as e:
                messagebox.showerror("Setup Error", f"Missing global DB function: {e}. Ensure all helper functions are defined globally.")
                return

            # 2. Check Monthly Constraint
            if check_if_snapshot_taken_this_month():
                response = messagebox.askyesno(
                    "Already Saved This Month",
                    "A snapshot already exists for this month. Do you want to save a new entry anyway?"
                )
                if not response:
                    return

            # 3. Save to DB (Assumes save_new_snapshot is global)
            if save_new_snapshot(data):
                messagebox.showinfo("Success", f"Snapshot saved for {datetime.now().strftime('%B %Y')}!")
                # Clear form and refresh history
                for key in required_keys:
                    form_entries[key].delete(0, tk.END)
                refresh_history()
            else:
                messagebox.showerror("DB Error", "Failed to save the snapshot. Check console for details.")


        def refresh_history(month_filter=None):
            """Loads and displays the history of snapshots."""
            
            # Clear the old widgets
            for widget in history_list_frame.winfo_children():
                widget.destroy()
                
            try:
                # Assumes load_snapshot_history is global
                history = load_snapshot_history(month_filter) 
            except NameError:
                tk.Label(history_list_frame, text="Cannot load history: 'load_snapshot_history' not defined.", 
                        bg=theme()["ACCENT"], fg="red", font=("Segoe UI", 10)).pack(padx=20, pady=10)
                return

            if not history:
                tk.Label(history_list_frame, text="No snapshots recorded yet.", 
                        bg=theme()["ACCENT"], fg=theme()["TEXT_SECONDARY"], 
                        font=("Segoe UI", 10)).pack(padx=20, pady=10)
                return

            for entry in history:
                create_history_card(entry)

        def create_history_card(entry):
            """Creates the UI widget for a single archived snapshot."""
            
            card_frame = tk.Frame(history_list_frame, bg=theme()["CARD"], bd=1, relief="flat") 
            card_frame.pack(fill="x", padx=5, pady=3)
            
            # Left Side (Date, Weight, and Main Activity)
            info_frame = tk.Frame(card_frame, bg=theme()["CARD"])
            info_frame.pack(side="left", fill="x", padx=10, pady=5, expand=True)

            date_obj = datetime.strptime(entry['date'], '%Y-%m-%d')
            
            # Date & Weight
            tk.Label(info_frame, text=f"📅 {date_obj.strftime('%B %Y')}", 
                    font=("Segoe UI", 11, "bold"), 
                    bg=theme()["CARD"], fg=theme()["TEXT"], anchor="w").pack(fill="x")
                    
            tk.Label(info_frame, text=f"Weight: {entry['weight']:.1f} kg | Activity: {entry['main_activity']}", 
                    font=("Segoe UI", 9), 
                    bg=theme()["CARD"], fg=theme()["TEXT_SECONDARY"], anchor="w").pack(fill="x")
                    
            # Obsession Snippet
            tk.Label(info_frame, text=f"Obsession: {entry['obsession']}", 
                    font=("Segoe UI", 9, "italic"), wraplength=400,
                    bg=theme()["CARD"], fg="#ff66b2", anchor="w").pack(fill="x")

            # Right Side (View Button)
            tk.Button(card_frame, text="Details", 
                    command=lambda e=entry: show_full_snapshot(e), 
                    bg=theme()["BTN"], fg=theme()["TEXT"], font=("Segoe UI", 8)).pack(side="right", padx=10)

        def show_full_snapshot(entry):
            """Opens a top-level window to view the full archived snapshot."""
            
            details_window = tk.Toplevel(content)
            date_obj = datetime.strptime(entry['date'], '%Y-%m-%d')
            details_window.title(f"Snapshot for {date_obj.strftime('%B %Y')}")
            details_window.config(bg=theme()["ACCENT"])
            
            main_frame = tk.Frame(details_window, bg=theme()["ACCENT"], padx=15, pady=15)
            main_frame.pack(fill="both", expand=True)

            # Header
            tk.Label(main_frame, text=f"Portrait of Me: {date_obj.strftime('%B %Y')}", 
                    font=("Segoe UI", 14, "bold"), bg=theme()["ACCENT"], 
                    fg=theme()["TEXT"]).pack(pady=(0, 15))
                    
            
            data_display = {
                "⚖️ Weight": f"{entry['weight']:.1f} kg",
                "🎵 Top 3 Songs": entry['songs'],
                "🍕 Top 3 Foods": entry['foods'],
                "🧠 Current Obsession": entry['obsession'],
                "💼 Main Activity": entry['main_activity'],
                "📚 Media Consumption": entry['media_consumption'],
            }

            # Use a secondary frame for the key/value pairs
            detail_frame = tk.Frame(main_frame, bg=theme()["CARD"], padx=15, pady=15)
            detail_frame.pack(fill="x")
            
            row_num = 0
            for label_text, value_text in data_display.items():
                
                # Label (Key)
                tk.Label(detail_frame, text=label_text, font=("Segoe UI", 10, "bold"), 
                        bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=row_num, column=0, sticky="nw", pady=3, padx=5)
                
                # Value
                tk.Label(detail_frame, text=value_text, font=("Segoe UI", 10), wraplength=350,
                        bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=row_num, column=1, sticky="nw", pady=3, padx=10)
                
                row_num += 1
            
            # Configure columns to distribute space
            detail_frame.grid_columnconfigure(0, weight=0)
            detail_frame.grid_columnconfigure(1, weight=1)

        # ----------------------------------------
        # --- MAIN UI LAYOUT ---
        # ----------------------------------------
        
        for widget in content.winfo_children():
            widget.destroy()

        main_frame = tk.Frame(content, bg=theme()["BG"])
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Use PanedWindow to separate the input form from the archive
        paned_window = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        paned_window.pack(fill="both", expand=True)

        # --- TOP PANEL: Input Form ---
        input_panel = tk.LabelFrame(paned_window, text=f"⭐ Monthly Snapshot: {datetime.now().strftime('%B %Y')}", 
                                    bg=theme()["ACCENT"], fg=theme()["TEXT"], padx=10, pady=10)
        paned_window.add(input_panel, weight=1)
        
        form_frame = tk.Frame(input_panel, bg=theme()["ACCENT"])
        form_frame.pack(fill="both", expand=True)

        # Form Fields Definition
        field_data = [
            ("Current Weight (kg):", 'weight', "e.g., 65.5"),
            ("Top 3 Fav Songs (comma sep):", 'songs', "e.g., Song A, Song B, Song C"),
            ("Top 3 Fav Foods (comma sep):", 'foods', "e.g., Sushi, Pizza, Salad"),
            ("Current Obsession/Hobby:", 'obsession', "e.g., Learning Spanish verbs"),
            ("Main Activity:", 'main_activity', "e.g., Finishing Project Alpha"),
            ("Media Consumption:", 'media_consumption', "e.g., Sapiens (Book)")
        ]
        
        # Create the Form Grid
        for i, (label_text, key, placeholder) in enumerate(field_data):
            tk.Label(form_frame, text=label_text, bg=theme()["ACCENT"], fg=theme()["TEXT"], 
                    font=("Segoe UI", 10, "bold"), anchor="w").grid(row=i, column=0, sticky="w", padx=10, pady=5)
                    
            entry = tk.Entry(form_frame, width=50, bg=theme()["CARD"], fg=theme()["TEXT"])
            entry.insert(0, placeholder)
            entry.bind("<FocusIn>", lambda event, e=entry, p=placeholder: e.delete(0, tk.END) if e.get() == p else None)
            entry.bind("<FocusOut>", lambda event, e=entry, p=placeholder: e.insert(0, p) if not e.get() else None)
            entry.grid(row=i, column=1, sticky="ew", padx=10, pady=5)
            form_entries[key] = entry
            
        # Configure columns for resizing
        form_frame.grid_columnconfigure(1, weight=1)

        # Save Button
        save_btn = tk.Button(input_panel, text="💾 Save Monthly Portrait", 
                            command=save_snapshot_action,
                            bg=theme()["BTN_HOVER"], fg=theme()["TEXT"], 
                            font=("Segoe UI", 11, "bold"), padx=15, pady=8)
        save_btn.pack(pady=15)
        

        # --- BOTTOM PANEL: Archive History ---
        archive_panel = tk.LabelFrame(paned_window, text="📜 Snapshot History", 
                                    bg=theme()["BG"], fg=theme()["TEXT"], padx=5, pady=5)
        paned_window.add(archive_panel, weight=1)

        # Filter/Search functionality (simplified to month filter for monthly tracking)
        filter_frame = tk.Frame(archive_panel, bg=theme()["BG"])
        filter_frame.pack(fill="x", pady=5)
        
        tk.Label(filter_frame, text="Filter by Month (YYYY-MM):", bg=theme()["BG"], fg=theme()["TEXT"]).pack(side="left", padx=(10, 5))
        month_entry = tk.Entry(filter_frame, width=15, bg=theme()["CARD"], fg=theme()["TEXT"])
        month_entry.pack(side="left", padx=5)
        
        def apply_month_filter(event=None):
            """Triggers refresh of history with the month query."""
            refresh_history(month_entry.get().strip())
            
        month_entry.bind('<KeyRelease>', apply_month_filter)
        tk.Button(filter_frame, text="Apply Filter", command=apply_month_filter, bg=theme()["BTN"]).pack(side="left", padx=5)

        # Scrollable Archive List Container
        list_container = tk.Frame(archive_panel, bg=theme()["ACCENT"], bd=1, relief="sunken")
        list_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        archive_canvas = tk.Canvas(list_container, bg=theme()["ACCENT"])
        v_scrollbar = tk.Scrollbar(list_container, orient="vertical", command=archive_canvas.yview)
        history_list_frame = tk.Frame(archive_canvas, bg=theme()["ACCENT"])
        
        archive_canvas.create_window((0, 0), window=history_list_frame, anchor="nw")
        archive_canvas.configure(yscrollcommand=v_scrollbar.set)
        
        v_scrollbar.pack(side="right", fill="y")
        archive_canvas.pack(side="left", fill="both", expand=True)

        history_list_frame.bind("<Configure>", lambda e: archive_canvas.configure(
            scrollregion=archive_canvas.bbox("all"), width=history_list_frame.winfo_width()
        ))
        
        # --- Initial Load ---
        refresh_history()
    
    # Fortune Cookie Page
    if pn == "FortuneCookie":
        import tkinter as tk
        from tkinter import ttk, messagebox
        import random
        from datetime import datetime
        
        # --- UI GLOBALS ---
        reveal_frame = None
        archive_list_frame = None
        fortune_data_today = None # Stores the result of crack_daily_fortune()
        crack_button = None

        # Define the theme function if not globally available
        def theme():
            return {
                "BG": "#fff1f3",
                "SIDEBAR": "#ffe6ea",
                "CARD": "#ffffff",
                "BTN": "#ffd7dd",
                "BTN_HOVER": "#ffb6c2",
                "TEXT": "#2b2b2b",
                "TEXT_SECONDARY": "#888888",
                "ACCENT": "#ffdfe6"
            }
            
        # --- UI ACTION FUNCTIONS ---
        
        def crack_cookie_action():
            """
            The main action: attempts to crack the cookie, 
            saves the result, and refreshes the display.
            Assumes crack_daily_fortune() and check_if_cracked_today() are global.
            """
            global fortune_data_today
            
            try:
                # Check if already cracked using the global helper function
                if check_if_cracked_today():
                    messagebox.showinfo("Wait a Moment", "You have already cracked your fortune for today! Check back tomorrow.")
                    # Load the existing fortune to display it
                    fortune_data_today = crack_daily_fortune()
                else:
                    # Crack and save the new fortune
                    fortune_data_today = crack_daily_fortune()
                    messagebox.showinfo("Fortune Cracked!", "Your daily wisdom has been revealed.")

                # Always refresh the display after the action
                display_fortune()
                refresh_fortune_history()
                
            except NameError as e:
                messagebox.showerror("Setup Error", f"Missing global DB function: {e}. Ensure all helper functions are defined globally.")


        def display_fortune():
            """Updates the central reveal frame with the current day's fortune."""
            global fortune_data_today
            
            # Clear the reveal frame
            for widget in reveal_frame.winfo_children():
                widget.destroy()

            if fortune_data_today:
                data = fortune_data_today
                
                # Disable the button and update text
                crack_button.config(state=tk.DISABLED, text="🔮 Cracked Today")

                # --- 1. Header and Date ---
                tk.Label(reveal_frame, text=f"Daily Reveal: {datetime.now().strftime('%Y-%m-%d')}", 
                        bg=theme()["CARD"], fg=theme()["TEXT_SECONDARY"], 
                        font=("Segoe UI", 10, "italic")).pack(pady=(15, 0))

                # --- 2. Reflective Message (Main Focus) ---
                tk.Label(reveal_frame, text=data['fortune_text'], 
                        bg=theme()["CARD"], fg=theme()["TEXT"], 
                        font=("Segoe UI", 14, "bold"), wraplength=450, 
                        justify=tk.CENTER).pack(pady=15, padx=20)
                
                # --- Separator ---
                ttk.Separator(reveal_frame, orient='horizontal').pack(fill='x', padx=30, pady=5)

                # --- 3. Angel Number ---
                tk.Label(reveal_frame, text="✨ Angel Number ✨", 
                        bg=theme()["CARD"], fg=theme()["TEXT"], 
                        font=("Segoe UI", 10, "bold")).pack(pady=(10, 0))
                tk.Label(reveal_frame, text=data['angel_number'], 
                        bg=theme()["CARD"], fg="#ff66b2", 
                        font=("Segoe UI", 24, "bold")).pack(pady=(0, 15))

                # --- 4. Side Quest ---
                tk.Label(reveal_frame, text="⚔️ Daily Side Quest ⚔️", 
                        bg=theme()["CARD"], fg=theme()["TEXT"], 
                        font=("Segoe UI", 10, "bold")).pack(pady=(10, 0))
                tk.Label(reveal_frame, text=data['side_quest'], 
                        bg=theme()["CARD"], fg=theme()["TEXT"], 
                        font=("Segoe UI", 11), wraplength=450, 
                        justify=tk.CENTER).pack(pady=(0, 20), padx=20)

            else:
                # Display pre-cracked state
                crack_button.config(state=tk.NORMAL, text="🔮 Crack Your Fortune")
                tk.Label(reveal_frame, text="Your Daily Fortune Awaits!", 
                        bg=theme()["CARD"], fg=theme()["TEXT"], 
                        font=("Segoe UI", 16, "bold")).pack(pady=50)
                tk.Label(reveal_frame, text="Click the button below to reveal your reflective prompt and daily side quest.", 
                        bg=theme()["CARD"], fg=theme()["TEXT_SECONDARY"], 
                        font=("Segoe UI", 10), wraplength=400).pack(pady=(0, 30))


        def refresh_fortune_history(search_query=""):
            """Loads and displays the history of cracked fortunes. Assumes load_fortune_history() is global."""
            
            # Clear the old widgets
            for widget in archive_list_frame.winfo_children():
                widget.destroy()
                
            try:
                history = load_fortune_history(search_query) # Global DB function
            except NameError:
                tk.Label(archive_list_frame, text="Cannot load history: 'load_fortune_history' not defined.", 
                        bg=theme()["ACCENT"], fg="red", font=("Segoe UI", 10)).pack(padx=20, pady=10)
                return

            if not history:
                tk.Label(archive_list_frame, text="No fortune history yet.", 
                        bg=theme()["ACCENT"], fg=theme()["TEXT_SECONDARY"], 
                        font=("Segoe UI", 10)).pack(padx=20, pady=10)
                return

            for entry in history:
                create_history_card(entry)


        def create_history_card(entry):
            """Creates the UI widget for a single archived fortune."""
            
            card_frame = tk.Frame(archive_list_frame, bg=theme()["CARD"], bd=1, relief="flat") 
            card_frame.pack(fill="x", padx=5, pady=3)
            
            # Left Side (Date and Fortune)
            info_frame = tk.Frame(card_frame, bg=theme()["CARD"])
            info_frame.pack(side="left", fill="x", padx=10, pady=5, expand=True)

            # Date 
            tk.Label(info_frame, text=f"🍪 {entry['date']}", 
                    font=("Segoe UI", 9, "bold"), 
                    bg=theme()["CARD"], fg=theme()["TEXT_SECONDARY"], anchor="w").pack(fill="x")
                    
            # Fortune Text
            tk.Label(info_frame, text=entry['fortune_text'], 
                    font=("Segoe UI", 10), wraplength=400,
                    bg=theme()["CARD"], fg=theme()["TEXT"], anchor="w").pack(fill="x")
                    
            # Angel Number & Quest Snippet
            # Show only the first 5 words of the side quest to keep it clean
            quest_snippet = " ".join(entry['side_quest'].split()[:5]) + "..."
            tk.Label(info_frame, text=f"Number: {entry['angel_number']} | Quest: {quest_snippet}", 
                    font=("Segoe UI", 8, "italic"), 
                    bg=theme()["CARD"], fg="#ff66b2", anchor="w").pack(fill="x")

            # Right Side (View Button)
            tk.Button(card_frame, text="View All", 
                    command=lambda e=entry: show_full_fortune(e), 
                    bg=theme()["BTN"], fg=theme()["TEXT"], font=("Segoe UI", 8)).pack(side="right", padx=10)


        def show_full_fortune(entry):
            """Opens a top-level window to view the full archived fortune content."""
            
            details_window = tk.Toplevel(content)
            details_window.title(f"Fortune for {entry['date']}")
            details_window.config(bg=theme()["ACCENT"])
            
            main_frame = tk.Frame(details_window, bg=theme()["ACCENT"], padx=15, pady=15)
            main_frame.pack(fill="both", expand=True)

            # Date/Header
            tk.Label(main_frame, text=f"Fortune Revealed on: {entry['date']}", 
                    font=("Segoe UI", 12, "bold"), bg=theme()["ACCENT"], 
                    fg=theme()["TEXT"]).pack(pady=(0, 10))
                    
            # --- Angel Number ---
            tk.Label(main_frame, text=f"Angel Number: {entry['angel_number']}", 
                    font=("Segoe UI", 14, "bold"), bg=theme()["CARD"], 
                    fg="#ff66b2", bd=2, relief="solid", pady=5).pack(fill="x", pady=5)

            # --- Reflective Message ---
            tk.Label(main_frame, text="Reflective Prompt:", 
                    font=("Segoe UI", 10, "underline"), bg=theme()["ACCENT"], 
                    fg=theme()["TEXT"]).pack(pady=(10, 0))
            tk.Label(main_frame, text=entry['fortune_text'], 
                    font=("Segoe UI", 12), bg=theme()["CARD"], 
                    fg=theme()["TEXT"], wraplength=400, justify=tk.LEFT, 
                    padx=10, pady=10).pack(fill="x")

            # --- Side Quest ---
            tk.Label(main_frame, text="Daily Side Quest:", 
                    font=("Segoe UI", 10, "underline"), bg=theme()["ACCENT"], 
                    fg=theme()["TEXT"]).pack(pady=(10, 0))
            tk.Label(main_frame, text=entry['side_quest'], 
                    font=("Segoe UI", 12), bg=theme()["CARD"], 
                    fg=theme()["TEXT"], wraplength=400, justify=tk.LEFT, 
                    padx=10, pady=10).pack(fill="x")
                    
            
        # ----------------------------------------
        # --- MAIN UI LAYOUT ---
        # ----------------------------------------
        
        for widget in content.winfo_children():
            widget.destroy()

        main_frame = tk.Frame(content, bg=theme()["BG"])
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Use PanedWindow to separate the main reveal area from the archive
        paned_window = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        paned_window.pack(fill="both", expand=True)

        # --- TOP PANEL: Fortune Reveal Area ---
        reveal_panel = tk.Frame(paned_window, bg=theme()["ACCENT"])
        paned_window.add(reveal_panel, weight=1)

        # 1. Button Container Frame (PACKED FIRST: Ensures button stays centered at the bottom)
        button_container = tk.Frame(reveal_panel, bg=theme()["ACCENT"])
        button_container.pack(side="bottom", fill="x", pady=10)
        
        # Crack Button (Now packed into its container)
        crack_button = tk.Button(button_container, text="🔮 Crack Your Fortune", 
                                command=crack_cookie_action,
                                bg=theme()["BTN_HOVER"], fg=theme()["TEXT"], 
                                font=("Segoe UI", 12, "bold"), padx=20, pady=10)
        crack_button.pack(anchor="center") # Centers the button within the container
        
        # 2. Reveal Frame (White Card - PACKED SECOND: Takes the remaining space)
        reveal_frame = tk.Frame(reveal_panel, bg=theme()["CARD"], bd=1, relief="raised")
        reveal_frame.pack(fill="both", expand=True, padx=20, pady=(20, 5)) 

        # --- BOTTOM PANEL: Archive History ---
        archive_panel = tk.LabelFrame(paned_window, text="📜 Fortune History", 
                                    bg=theme()["BG"], fg=theme()["TEXT"], padx=5, pady=5)
        paned_window.add(archive_panel, weight=1)

        # Search Bar 
        search_frame = tk.Frame(archive_panel, bg=theme()["BG"])
        search_frame.pack(fill="x", pady=5)
        
        search_entry = tk.Entry(search_frame, width=30, bg=theme()["CARD"], fg=theme()["TEXT"])
        search_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        def apply_history_search(event=None):
            """Triggers refresh of history with the search query."""
            refresh_fortune_history(search_entry.get().strip())
            
        search_entry.bind('<KeyRelease>', apply_history_search)
        tk.Button(search_frame, text="🔍 Search", command=apply_history_search, bg=theme()["BTN"]).pack(side="left", padx=5)

        # Scrollable Archive List Container
        list_container = tk.Frame(archive_panel, bg=theme()["ACCENT"], bd=1, relief="sunken")
        list_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        archive_canvas = tk.Canvas(list_container, bg=theme()["ACCENT"])
        v_scrollbar = tk.Scrollbar(list_container, orient="vertical", command=archive_canvas.yview)
        archive_list_frame = tk.Frame(archive_canvas, bg=theme()["ACCENT"])
        
        archive_canvas.create_window((0, 0), window=archive_list_frame, anchor="nw")
        archive_canvas.configure(yscrollcommand=v_scrollbar.set)
        
        v_scrollbar.pack(side="right", fill="y")
        archive_canvas.pack(side="left", fill="both", expand=True)

        archive_list_frame.bind("<Configure>", lambda e: archive_canvas.configure(
            scrollregion=archive_canvas.bbox("all"), width=archive_list_frame.winfo_width()
        ))
        
        # --- Initial Load ---
        # Attempt to load the existing fortune, or generate a new one if not cracked
        try:
            fortune_data_today = crack_daily_fortune() 
        except NameError:
            fortune_data_today = None # Fails gracefully if helper functions are missing
            
        display_fortune() 
        refresh_fortune_history()
    
    # Closure Box Page
    if pn == "ClosureBox":
        import tkinter as tk
        from tkinter import messagebox, scrolledtext, ttk
        from datetime import datetime
        
        # Define the theme dictionary based on your specification
        # NOTE: This should ideally be a globally defined function/dictionary in your main file.
        def theme():
            return {
                "BG": "#fff1f3",
                "SIDEBAR": "#ffe6ea",
                "CARD": "#ffffff",
                "BTN": "#ffd7dd",
                "BTN_HOVER": "#ffb6c2",
                "TEXT": "#2b2b2b",
                "TEXT_SECONDARY": "#888888", # Using secondary for light text
                "ACCENT": "#ffdfe6" # The primary light accent color
            }
        
        # --- INPUT WIDGET GLOBALS ---
        closure_title_entry = None
        closure_content_text = None
        closure_type_var = tk.StringVar(value="Letter") 
        
        # --- DISPLAY GLOBALS ---
        archive_list_frame = None
        search_entry = None

        # ----------------------------------------
        # --- UI ACTION FUNCTIONS ---
        # ----------------------------------------

        def refresh_archive(search_query=""):
            """Clears the archive display and repopulates it with current data."""
            
            # Clear the old widgets
            for widget in archive_list_frame.winfo_children():
                widget.destroy()
                
            # load_closure_entries is assumed to be globally defined
            # If it's not defined, this will raise a NameError.
            try:
                entries = load_closure_entries(search_query) 
            except NameError:
                tk.Label(archive_list_frame, text="DB Functions Missing! Please define save/load/delete_closure_entry globally.", 
                        bg=theme()["CARD"], fg="red", font=("Segoe UI", 10, "bold")).pack(padx=20, pady=40)
                return

            if not entries:
                tk.Label(archive_list_frame, text="The vault is empty. Write your first closure entry.", 
                        bg=theme()["CARD"], fg=theme()["TEXT_SECONDARY"], font=("Segoe UI", 10)).pack(padx=20, pady=40)
                return

            for entry in entries:
                create_archive_card(entry)

        def seal_and_close():
            """Handles saving the new closure entry."""
            title = closure_title_entry.get().strip()
            content = closure_content_text.get("1.0", "end-1c").strip()
            entry_type = closure_type_var.get()

            if not title or not content:
                messagebox.showwarning("Input Missing", "Please enter a Title and Content.")
                return
                
            if messagebox.askyesno("Confirm Closure", 
                                "Are you sure you want to seal this entry? It will be filed away for reflection."):
                
                # save_closure_entry is assumed to be globally defined
                try:
                    if save_closure_entry(title, content, entry_type): 
                        messagebox.showinfo("Success", "Entry sealed and filed away.")
                        
                        # Reset fields
                        closure_title_entry.delete(0, "end")
                        closure_content_text.delete("1.0", "end")
                        
                        # Refresh the archive display
                        refresh_archive()
                    else:
                        messagebox.showerror("Error", "Could not save entry to the database.")
                except NameError:
                    messagebox.showerror("Error", "Database function 'save_closure_entry' is not defined.")

        def permanent_delete_action(entry_id, card_frame):
            """Deletes an entry and removes its UI card."""
            if messagebox.askyesno("Confirm Permanent Deletion", 
                                "WARNING: This action is permanent. Delete this entry?"):
                
                # delete_closure_entry is assumed to be globally defined
                try:
                    if delete_closure_entry(entry_id): 
                        card_frame.destroy()
                        refresh_archive()
                    else:
                        messagebox.showerror("Error", "Could not delete entry from the database.")
                except NameError:
                    messagebox.showerror("Error", "Database function 'delete_closure_entry' is not defined.")


        def show_full_content(entry):
            """Opens a top-level window to view the full archived content."""
            
            details_window = tk.Toplevel(content)
            details_window.title(f"Sealed Entry: {entry['title']}")
            details_window.config(bg=theme()["CARD"])
            
            # Color mapping for card visualization (using theme colors where possible)
            type_color_map = {"Letter": "#ffc4d3", "Emotion": "#ff9baa", "Memory": "#ffc0cb", "Other": theme()["ACCENT"]}
            card_bg = type_color_map.get(entry['type'], theme()["ACCENT"])

            # Title/Header
            tk.Label(details_window, text=entry['title'], font=("Segoe UI", 16, "bold"), 
                    bg=card_bg, fg=theme()["TEXT"], padx=15, pady=10).pack(fill="x")
                    
            # Date and Type
            tk.Label(details_window, text=f"Type: {entry['type']} | Sealed On: {entry['date'].split(' ')[0]}", 
                    font=("Segoe UI", 9, "italic"), bg=theme()["CARD"], fg=theme()["TEXT_SECONDARY"], padx=15).pack(fill="x", pady=(5, 0))

            # Content (Read-Only Text Box)
            content_box = scrolledtext.ScrolledText(details_window, width=60, height=15, 
                                                    font=("Segoe UI", 10), wrap=tk.WORD, 
                                                    bg=card_bg, fg=theme()["TEXT"], padx=10, pady=10)
            content_box.insert(tk.END, entry['content'])
            content_box.config(state=tk.DISABLED) # Make it read-only
            content_box.pack(padx=15, pady=15, fill="both", expand=True)

        def create_archive_card(entry):
            """Creates the UI widget for a single archived item."""
            
            # Color mapping for card visualization (using theme colors where possible)
            type_color_map = {"Letter": "#ffc4d3", "Emotion": "#ff9baa", "Memory": "#ffc0cb", "Other": theme()["ACCENT"]}
            card_bg = type_color_map.get(entry['type'], theme()["ACCENT"])
            
            card_frame = tk.Frame(archive_list_frame, bg=card_bg, bd=1, relief="flat") 
            card_frame.pack(fill="x", padx=10, pady=5)
            
            # Left Side (Title and Date)
            info_frame = tk.Frame(card_frame, bg=card_bg)
            info_frame.pack(side="left", fill="x", padx=10, pady=5, expand=True)

            tk.Label(info_frame, text=entry['title'], font=("Segoe UI", 11, "bold"), 
                    bg=card_bg, fg=theme()["TEXT"], anchor="w").pack(fill="x")
                    
            # Only show the date part
            date_part = entry['date'].split(' ')[0] 
            tk.Label(info_frame, text=f"Filed: {date_part} | Type: {entry['type']}", 
                    font=("Segoe UI", 8), bg=card_bg, fg=theme()["TEXT_SECONDARY"], anchor="w").pack(fill="x")
                    
            # Right Side (Actions)
            action_frame = tk.Frame(card_frame, bg=card_bg)
            action_frame.pack(side="right", padx=10, pady=5)
            
            # View Button
            tk.Button(action_frame, text="View 👀", command=lambda e=entry: show_full_content(e), 
                    bg=theme()["BTN_HOVER"], fg=theme()["TEXT"], font=("Segoe UI", 8)).pack(side="left", padx=5)
                    
            # Delete Button (Permanent)
            tk.Button(action_frame, text="Delete 🗑️", 
                    command=lambda eid=entry['id'], cf=card_frame: permanent_delete_action(eid, cf), 
                    bg="#f8adad", fg="white", font=("Segoe UI", 8)).pack(side="left")

        # ----------------------------------------
        # --- MAIN UI LAYOUT ---
        # ----------------------------------------
        
        for widget in content.winfo_children():
            widget.destroy()

        main_frame = tk.Frame(content, bg=theme()["BG"]) # Use BG for the main frame
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # --- TOP 1: Input Panel (Write a new entry) ---
        input_panel = tk.LabelFrame(main_frame, text="✍️ Seal a New Entry", 
                                    bg=theme()["ACCENT"], fg=theme()["TEXT"], 
                                    font=("Segoe UI", 11, "bold"), padx=10, pady=10)
        input_panel.pack(fill="x", pady=10, padx=10)
        
        # 1. Title/Recipient
        tk.Label(input_panel, text="Title/Recipient:", bg=theme()["ACCENT"], fg=theme()["TEXT"]).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        closure_title_entry = tk.Entry(input_panel, width=50, bg=theme()["CARD"], fg=theme()["TEXT"])
        closure_title_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        # 2. Type Selector
        type_options = ["Letter", "Emotion", "Memory", "Other"]
        tk.Label(input_panel, text="Type:", bg=theme()["ACCENT"], fg=theme()["TEXT"]).grid(row=0, column=2, sticky="w", padx=10)
        
        style = ttk.Style()
        style.theme_use('default')
        style.map('TCombobox', fieldbackground=[('readonly', theme()["CARD"])], selectbackground=[('readonly', theme()["CARD"])], selectforeground=[('readonly', theme()["TEXT"])])

        type_combo = ttk.Combobox(input_panel, textvariable=closure_type_var, values=type_options, state="readonly", width=10)
        type_combo.grid(row=0, column=3, sticky="w", pady=5)
        
        # 3. Content/Letter Body
        tk.Label(input_panel, text="Content:", bg=theme()["ACCENT"], fg=theme()["TEXT"]).grid(row=1, column=0, sticky="nw", padx=5, pady=5)
        closure_content_text = scrolledtext.ScrolledText(input_panel, width=60, height=5, font=("Segoe UI", 10), wrap=tk.WORD, bg=theme()["CARD"], fg=theme()["TEXT"])
        closure_content_text.grid(row=1, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # 4. Seal Button
        tk.Button(input_panel, text="🔒 Seal and Close Entry", command=seal_and_close, 
                bg=theme()["BTN_HOVER"], fg=theme()["TEXT"], font=("Segoe UI", 10, "bold")).grid(row=1, column=3, sticky="n", padx=10, pady=10)

        input_panel.grid_columnconfigure(1, weight=1)

        # --- MIDDLE 2: Search Bar ---
        search_frame = tk.Frame(main_frame, bg=theme()["BG"])
        search_frame.pack(fill="x", pady=5, padx=10)
        
        tk.Label(search_frame, text="Search Vault:", bg=theme()["BG"], fg=theme()["TEXT"]).pack(side="left", padx=5)
        search_entry = tk.Entry(search_frame, width=50, bg=theme()["CARD"], fg=theme()["TEXT"])
        search_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        def apply_search(event=None):
            """Triggers refresh with the current search query."""
            refresh_archive(search_entry.get().strip())
            
        search_entry.bind('<KeyRelease>', apply_search)
        tk.Button(search_frame, text="🔍", command=apply_search, bg=theme()["BTN"]).pack(side="left", padx=5)
        
        # --- BOTTOM 3: Archived List (Scrollable) ---
        list_container = tk.Frame(main_frame, bg=theme()["CARD"], bd=1, relief="sunken")
        list_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Setup scrollable area
        archive_canvas = tk.Canvas(list_container, bg=theme()["CARD"])
        v_scrollbar = tk.Scrollbar(list_container, orient="vertical", command=archive_canvas.yview)
        archive_list_frame = tk.Frame(archive_canvas, bg=theme()["CARD"])
        
        # Configure scrolling
        archive_canvas.create_window((0, 0), window=archive_list_frame, anchor="nw")
        archive_canvas.configure(yscrollcommand=v_scrollbar.set)
        
        v_scrollbar.pack(side="right", fill="y")
        archive_canvas.pack(side="left", fill="both", expand=True)

        # Reconfigure scroll region whenever the list frame size changes
        archive_list_frame.bind("<Configure>", lambda e: archive_canvas.configure(
            scrollregion=archive_canvas.bbox("all"), width=archive_list_frame.winfo_width()
        ))
        
        # --- Initial Load ---
        refresh_archive()
    
    # Event Countdown Page 
    if pn == "Countdown": 
        import tkinter as tk
        from tkinter import colorchooser, ttk
        from tkinter import messagebox
        from tkcalendar import DateEntry
        from datetime import datetime, date, timedelta
        
        # --- UI Color Constant ---
        FRAME_BG_COLOR = "#ffe6ef" 
        
        # --- Global Variables for Dynamic Display ---
        countdown_widgets = {} 

        # --- INPUT WIDGETS (Initialized as None) ---
        event_name_entry = None
        event_target_date = None
        event_hour_var = None
        event_minute_var = None
        event_color_var = tk.StringVar(value=theme()["ACCENT"]) 
        
        # Management Widgets
        management_combo = None 
        
        # --- DB HELPERS ---
        
        def save_event(name, target_datetime, color):
            """Saves a new countdown event with a new unique ID."""
            conn = db_connect()
            c = conn.cursor()
            c.execute("""
                INSERT INTO events_countdown (name, target_datetime, color)
                VALUES (?, ?, ?)
            """, (name, target_datetime, color))
            conn.commit()
            conn.close()

        def delete_event(event_id):
            """Deletes a countdown event by its ID."""
            conn = db_connect()
            c = conn.cursor()
            c.execute("DELETE FROM events_countdown WHERE id = ?", (event_id,))
            conn.commit()
            conn.close()

        def load_events():
            """Loads ALL active countdown events."""
            conn = db_connect()
            c = conn.cursor()
            
            event_rows = c.execute("SELECT id, name, target_datetime, color FROM events_countdown ORDER BY target_datetime ASC").fetchall()
            
            conn.close()
            
            events = []
            for eid, name, target_dt_str, color in event_rows:
                events.append({
                    'id': eid, 
                    'name': name, 
                    'target_dt': datetime.strptime(target_dt_str, "%Y-%m-%d %H:%M:%S"), 
                    'color': color
                })
            return events

        # --- ACTION FUNCTIONS ---
        
        def set_event():
            """Handles getting input and saving the new event."""
            try:
                name = event_name_entry.get().strip()
                if not name:
                    messagebox.showerror("Error", "Event Name is required.")
                    return

                d = event_target_date.get_date()
                h = int(event_hour_var.get())
                m = int(event_minute_var.get())
                
                target_dt_obj = datetime(d.year, d.month, d.day, h, m, 0)
                
                if target_dt_obj <= datetime.now():
                    messagebox.showerror("Error", "Target date must be in the future.")
                    return
                    
                target_dt_str = target_dt_obj.strftime("%Y-%m-%d %H:%M:%S")
                color = event_color_var.get()

                save_event(name, target_dt_str, color)
                
                event_name_entry.delete(0, 'end')
                refresh_countdown_page()
                
            except ValueError:
                messagebox.showerror("Error", "Please enter valid time values.")
            except Exception as e:
                messagebox.showerror("DB Error", f"Could not save event: {e}")

        def delete_event_action():
            """Handles deletion of a selected event."""
            selected_event_text = management_combo.get()
            if not selected_event_text or ":" not in selected_event_text:
                messagebox.showerror("Error", "Please select an event to delete.")
                return
                
            try:
                event_id = int(selected_event_text.split(":")[0].strip())
                
                if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete '{selected_event_text}'?"):
                    delete_event(event_id)
                    management_combo.set("") 
                    refresh_countdown_page()
                    
            except ValueError:
                messagebox.showerror("Error", "Invalid event selection.")


        def refresh_countdown_page():
            """
            Clears the display frame, repopulates management combo, 
            and ensures the dynamic update loop is running.
            """
            # 1. Clear the old display widgets
            for widget_set in countdown_widgets.values():
                for widget in widget_set.values():
                    widget.destroy()
            countdown_widgets.clear()
            
            # 2. Repopulate the management combobox
            populate_management_combo()
            
            # 3. Start/Continue the dynamic update loop
            update_countdown()


        def populate_management_combo():
            """Populates the Combobox with Event IDs and Names for management."""
            events = load_events()
            options = [f"{e['id']}: {e['name']}" for e in events]
            
            management_combo['values'] = options
            if not options:
                management_combo.set("No Events Set")


        def update_countdown():
            """Calculates and updates ALL countdown displays every second."""
            
            if not countdown_display_frame.winfo_exists():
                return
                
            events = load_events()
            now = datetime.now()
            
            # Step 1: Remove widgets for events that no longer exist in the database
            db_ids = {e['id'] for e in events}
            for event_id in list(countdown_widgets.keys()):
                if event_id not in db_ids:
                    for widget in countdown_widgets[event_id].values():
                        widget.destroy()
                    del countdown_widgets[event_id]
                    
            # Step 2: Update existing or create new widgets for each event
            for event in events:
                event_id = event['id']
                target_dt = event['target_dt']
                accent_color = event['color']
                
                if event_id not in countdown_widgets:
                    create_event_countdown_widgets(event_id, event, countdown_display_frame)
                
                time_left = target_dt - now
                
                if time_left.total_seconds() <= 0:
                    status_text = f"PASSED: {event['name']} ({target_dt.strftime('%b %d')})"
                    countdown_widgets[event_id]['name_label'].config(text=status_text, fg="gray")
                    for key in ['d', 'h', 'm', 's']:
                        countdown_widgets[event_id][f'{key}_val'].config(text="00", fg="gray")
                    continue

                # Time Calculation
                total_seconds = int(time_left.total_seconds())
                days = total_seconds // (24 * 3600)
                
                total_seconds %= (24 * 3600)
                hours = total_seconds // 3600
                
                total_seconds %= 3600
                minutes = total_seconds // 60
                
                seconds = total_seconds % 60
                
                # Update Display
                countdown_widgets[event_id]['name_label'].config(text=f"{event['name']} (Target: {target_dt.strftime('%b %d, %Y')})", fg=accent_color)
                countdown_widgets[event_id]['d_val'].config(text=f"{days:,}", fg=accent_color) 
                countdown_widgets[event_id]['h_val'].config(text=f"{hours:02d}", fg=accent_color)
                countdown_widgets[event_id]['m_val'].config(text=f"{minutes:02d}", fg=accent_color)
                countdown_widgets[event_id]['s_val'].config(text=f"{seconds:02d}", fg=accent_color)

            # Reschedule update after 1 second
            countdown_display_frame.after(1000, update_countdown)
            

        def create_event_countdown_widgets(event_id, event_data, parent_frame):
            """Creates a dedicated frame and labels for a single event countdown."""
            global countdown_widgets
            
            event_frame = tk.Frame(parent_frame, bg=theme()["CARD"], pady=10)
            event_frame.pack(fill="x", padx=20, pady=5)
            
            countdown_widgets[event_id] = {}
            accent = event_data['color']
            
            # 1. Name Label
            name_label = tk.Label(event_frame, text=event_data['name'], 
                                font=("Segoe UI", 12, "bold"), 
                                bg=theme()["CARD"], fg=accent)
            name_label.pack(anchor="w")
            countdown_widgets[event_id]['name_label'] = name_label

            # 2. Timer Frame (side-by-side units)
            timer_frame = tk.Frame(event_frame, bg=theme()["CARD"])
            timer_frame.pack(fill="x", pady=5)
            
            time_font = ("Consolas", 30, "bold") 
            units = [("d", "DAYS"), ("h", "HRS"), ("m", "MINS"), ("s", "SECS")]
            
            col = 0
            for unit_key, unit_label in units:
                val_label = tk.Label(timer_frame, text="--", font=time_font, fg=accent, bg=theme()["CARD"])
                val_label.grid(row=0, column=col, padx=(10, 5))
                countdown_widgets[event_id][f'{unit_key}_val'] = val_label
                
                unit_text_label = tk.Label(timer_frame, text=unit_label, 
                                        font=("Segoe UI", 8), 
                                        bg=theme()["CARD"], fg=theme()["TEXT"])
                unit_text_label.grid(row=1, column=col, sticky="n")
                
                col += 1
                
                if unit_key != 's':
                    separator = tk.Label(timer_frame, text=":", font=time_font, fg=accent, bg=theme()["CARD"])
                    separator.grid(row=0, column=col)
                    col += 1


        def pick_event_color():
            chosen = colorchooser.askcolor(title="Choose Event Accent Color")
            if chosen[1]:
                event_color_var.set(chosen[1])
                color_preview.config(bg=chosen[1])


        # ----------------------------------------
        # --- MAIN UI LAYOUT (Drawing the Frames)---
        # ----------------------------------------
        
        for widget in content.winfo_children():
            widget.destroy()

        main_frame = tk.Frame(content, bg=theme()["CARD"])
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Top: Countdown Display (Now for multiple events)
        countdown_display_frame = tk.Frame(main_frame, bg=theme()["CARD"])
        countdown_display_frame.pack(fill="both", expand=True, pady=10)
        
        # Bottom: Input and Management Forms
        input_frame = tk.Frame(main_frame, bg=theme()["CARD"])
        input_frame.pack(fill="x", expand=False, padx=20) 

        # --- Event Input Section (Left Side) ---
        event_frame = tk.LabelFrame(input_frame, text="➕ Set New Countdown Event", 
                                    bg=FRAME_BG_COLOR, fg=theme()["TEXT"], padx=10, pady=10) 
        event_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        r = 0
        tk.Label(event_frame, text="Event Name:", bg=FRAME_BG_COLOR, fg=theme()["TEXT"]).grid(row=r, column=0, sticky="w", pady=5);
        event_name_entry = tk.Entry(event_frame, width=25);
        event_name_entry.grid(row=r, column=1, columnspan=3, padx=5, sticky="ew", pady=5); r+=1
        
        tk.Label(event_frame, text="Target Date:", bg=FRAME_BG_COLOR, fg=theme()["TEXT"]).grid(row=r, column=0, sticky="w", pady=5);
        event_target_date = DateEntry(event_frame, width=10, date_pattern='yyyy-mm-dd');
        event_target_date.grid(row=r, column=1, padx=5, sticky="w");
        
        tk.Label(event_frame, text="Time:", bg=FRAME_BG_COLOR, fg=theme()["TEXT"]).grid(row=r, column=2, sticky="e", padx=(10, 0));
        
        event_hour_var = tk.StringVar(value="12")
        tk.Spinbox(event_frame, from_=0, to=23, wrap=True, width=3, format="%02.0f", textvariable=event_hour_var).grid(row=r, column=3, sticky="w");
        tk.Label(event_frame, text=":", bg=FRAME_BG_COLOR, fg=theme()["TEXT"]).grid(row=r, column=3, sticky="w", padx=(35, 0));
        event_minute_var = tk.StringVar(value="00")
        tk.Spinbox(event_frame, from_=0, to=59, wrap=True, width=3, format="%02.0f", textvariable=event_minute_var).grid(row=r, column=3, sticky="w", padx=(45, 0)); 
        r+=1

        tk.Label(event_frame, text="Accent Color:", bg=FRAME_BG_COLOR, fg=theme()["TEXT"]).grid(row=r, column=0, sticky="w", pady=10);
        
        color_btn = tk.Button(event_frame, text="Pick Color", command=pick_event_color, font=("Segoe UI", 8), bg=theme().get("BTN", "#cccccc"), fg="black")
        color_btn.grid(row=r, column=1, padx=5, sticky="w");
        
        color_preview = tk.Label(event_frame, bg=event_color_var.get(), width=3, height=1, relief="solid", bd=1)
        color_preview.grid(row=r, column=1, padx=(70, 0), sticky="w"); 
        
        tk.Button(event_frame, text="Set Countdown", command=set_event, 
                bg=theme().get("ACCENT", "#ff5d8f"), fg="white", 
                font=("Segoe UI", 10, "bold")).grid(row=r, column=3, sticky="e", pady=10)


        # --- Management Section (Right Side) ---
        management_frame = tk.LabelFrame(input_frame, text="🗑️ Manage Countdowns", 
                                    bg=FRAME_BG_COLOR, fg=theme()["TEXT"], padx=10, pady=10) 
        management_frame.pack(side="right", fill="y", padx=(10, 0))

        tk.Label(management_frame, text="Select Event:", bg=FRAME_BG_COLOR, fg=theme()["TEXT"]).grid(row=0, column=0, sticky="w", pady=5);
        management_combo = ttk.Combobox(management_frame, width=25, state="readonly");
        management_combo.grid(row=0, column=1, padx=5, sticky="ew", pady=5);

        tk.Button(management_frame, text="Delete Selected", command=delete_event_action, 
                bg="#fcaab8", fg="white", 
                font=("Segoe UI", 10, "bold")).grid(row=1, column=1, sticky="e", pady=10)


        # Initial setup 
        refresh_countdown_page()
    
    # Project Page
    if pn == "Project":
        import tkinter as tk
        from tkinter import colorchooser, ttk
        from tkinter import messagebox
        from tkcalendar import DateEntry
        from datetime import datetime, date, timedelta
        
        # --- UI Color Constant ---
        FRAME_BG_COLOR = "#ffe6ef" # Light pink background for input frames

        # --- Project Timeline Constants ---
        PROJECT_BAR_HEIGHT = 20
        X_SCALE_FACTOR = 10 
        MILESTONE_RADIUS = 5 
        CANVAS_HEIGHT_BASE = 50 

        # --- INPUT WIDGETS (Initialized as None) ---
        project_title_entry = None
        project_start_date = None
        project_end_date = None
        project_color_var = tk.StringVar(value="#4CAF50") 
        
        milestone_name_entry = None
        milestone_target_date = None
        project_list_combo = None 
        
        progress_project_combo = None
        progress_entry = None

        # --- DB HELPERS ---
        
        def save_project(name, start_date, end_date, color):
            """Saves a new project, defaulting progress to 0."""
            conn = db_connect()
            c = conn.cursor()
            c.execute("""
                INSERT INTO projects (name, start_date, end_date, color, progress)
                VALUES (?, ?, ?, ?, 0)
            """, (name, start_date, end_date, color))
            conn.commit()
            project_id = c.lastrowid
            conn.close()
            return project_id

        def save_milestone(project_id, name, target_date):
            """Saves a new milestone, defaulting completion to 0 (incomplete)."""
            conn = db_connect()
            c = conn.cursor()
            c.execute("""
                INSERT INTO milestones (project_id, name, target_date, is_complete)
                VALUES (?, ?, ?, 0)
            """, (project_id, name, target_date))
            conn.commit()
            conn.close()

        def update_project_progress(project_id, progress):
            """Updates the progress percentage of an existing project."""
            conn = db_connect()
            c = conn.cursor()
            c.execute("""
                UPDATE projects SET progress = ? WHERE id = ?
            """, (progress, project_id))
            conn.commit()
            conn.close()

        def load_all_projects_and_milestones():
            """Loads all active projects and their milestones for visualization."""
            conn = db_connect()
            c = conn.cursor()
            
            projects_rows = c.execute("SELECT id, name, start_date, end_date, color, progress FROM projects ORDER BY start_date ASC").fetchall()
            milestones_rows = c.execute("SELECT project_id, name, target_date, is_complete FROM milestones").fetchall()
            
            conn.close()
            
            projects = {}
            for pid, name, start, end, color, progress in projects_rows:
                projects[pid] = {
                    'id': pid, 
                    'name': name, 
                    'start': datetime.strptime(start, "%Y-%m-%d").date(), 
                    'end': datetime.strptime(end, "%Y-%m-%d").date(), 
                    'color': color if color else '#cccccc', 
                    'progress': progress if progress is not None else 0, 
                    'milestones': []
                }
                
            for pid, name, target, complete in milestones_rows:
                if pid in projects:
                    projects[pid]['milestones'].append({
                        'name': name, 
                        'target': datetime.strptime(target, "%Y-%m-%d").date(), 
                        'complete': complete
                    })
                    
            return list(projects.values())

        # --- ACTION FUNCTIONS ---
        def refresh_timeline():
            """Reloads data and redraws the canvas, and updates project comboboxes."""
            draw_timeline()
            populate_project_list() 
            populate_progress_project_list()

        def add_project():
            try:
                name = project_title_entry.get().strip()
                start = project_start_date.get_date().isoformat()
                end = project_end_date.get_date().isoformat()
                color = project_color_var.get()
                
                if not name:
                    messagebox.showerror("Error", "Project Name is required.")
                    return

                save_project(name, start, end, color)
                
                project_title_entry.delete(0, 'end')
                
                refresh_timeline()
                
            except Exception as e:
                messagebox.showerror("DB Error", f"Could not save project: {e}")

        def add_milestone():
            try:
                selected_project_text = project_list_combo.get()
                if ":" not in selected_project_text:
                    messagebox.showerror("Error", "Please select a Project.")
                    return
                
                project_id_str = selected_project_text.split(":")[0].strip()
                project_id = int(project_id_str)
                name = milestone_name_entry.get().strip()
                target = milestone_target_date.get_date().isoformat()
                
                if not name:
                    messagebox.showerror("Error", "Milestone Name is required.")
                    return

                save_milestone(project_id, name, target)
                
                milestone_name_entry.delete(0, 'end')
                
                refresh_timeline()
                
            except Exception as e:
                messagebox.showerror("DB Error", f"Could not save milestone: {e}")
                
        def update_progress_action():
            """Handles getting progress input and updating the selected project's progress."""
            try:
                selected_project_text = progress_project_combo.get()
                if ":" not in selected_project_text:
                    messagebox.showerror("Error", "Please select a Project to update.")
                    return
                
                project_id_str = selected_project_text.split(":")[0].strip()
                project_id = int(project_id_str)
                
                progress = int(progress_entry.get().strip())
                
                if not (0 <= progress <= 100):
                    messagebox.showerror("Error", "Progress must be between 0 and 100.")
                    return

                update_project_progress(project_id, progress)
                
                refresh_timeline()
                
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number (0-100) for progress.")
            except Exception as e:
                messagebox.showerror("DB Error", f"Could not update progress: {e}")
                
        def populate_project_list():
            """Populates the Combobox for Milestones."""
            projects = load_all_projects_and_milestones()
            options = [f"{p['id']}: {p['name']}" for p in projects]
            
            project_list_combo['values'] = options
            if options and project_list_combo.get() == "":
                project_list_combo.set(options[0])
            elif not options:
                project_list_combo.set("")

        def populate_progress_project_list():
            """Populates the Combobox for Progress Update."""
            projects = load_all_projects_and_milestones()
            options = [f"{p['id']}: {p['name']}" for p in projects]
            
            progress_project_combo['values'] = options
            if options and progress_project_combo.get() == "":
                progress_project_combo.set(options[0])
            elif not options:
                progress_project_combo.set("")

        # --- TIMELINE DRAWING FUNCTION (Gantt Chart Style) ---
        def draw_timeline():
            projects_data = load_all_projects_and_milestones()
            canvas.delete("all")
            
            # Display empty message if no projects exist
            if not projects_data:
                canvas.create_text(250, 100, text="Add a project to see the timeline.", fill=theme()["TEXT"])
                canvas.config(height=200)
                return
                
            today = date.today()
            
            # --- 1. Determine the Timeframe for the X-Axis (Fixed Logic) ---
            all_dates = [p['start'] for p in projects_data] + [p['end'] for p in projects_data]
            
            min_date_raw = min(all_dates + [today])
            max_date_raw = max(all_dates + [today])
                
            # Visualization range starts at the 1st of the month before the earliest project
            start_date_viz = (min_date_raw - timedelta(days=1)).replace(day=1)
            
            # Visualization range ends after the latest project
            temp_end = max_date_raw.replace(day=1) + timedelta(days=32)
            end_date_viz = temp_end.replace(day=1)

            total_days = (end_date_viz - start_date_viz).days
            if total_days < 90: # Ensure a minimum visible window of 90 days
                total_days = 90
                end_date_viz = start_date_viz + timedelta(days=90)

            canvas_width = total_days * X_SCALE_FACTOR + 150 
            
            # --- 2. Configure Canvas Size and Scroll Region ---
            current_canvas_height = CANVAS_HEIGHT_BASE + len(projects_data) * (PROJECT_BAR_HEIGHT + 15) + 50
            canvas.config(width=canvas_width, height=current_canvas_height, scrollregion=(0, 0, canvas_width, current_canvas_height))
            
            y_offset = 30 
            
            # --- 3. Draw X-Axis (Dates/Months Grid) ---
            current_day = start_date_viz
            while current_day <= end_date_viz:
                x_pos = 100 + (current_day - start_date_viz).days * X_SCALE_FACTOR
                
                if current_day.day == 1:
                    canvas.create_text(x_pos, 15, text=current_day.strftime("%b %Y"), anchor="n", fill="#555555", font=("Segoe UI", 8))
                    canvas.create_line(x_pos, 25, x_pos, current_canvas_height - 10, fill="#eeeeee") 
                    
                current_day += timedelta(days=7) 
            
            # --- 4. Draw Today Line ---
            days_from_start = (today - start_date_viz).days
            today_x = 100 + days_from_start * X_SCALE_FACTOR
            canvas.create_line(today_x, 0, today_x, current_canvas_height, fill="red", dash=(4, 2), width=1, tags="today_line")
            canvas.create_text(today_x, 5, text="TODAY", fill="red", anchor="nw", tags="today_line", font=("Segoe UI", 8, "bold"))
            
            
            # --- 5. Draw Project Bars and Milestones ---
            y_pos = y_offset
            for project in projects_data:
                
                # Project Name Label (Y-Axis)
                canvas.create_text(5, y_pos + PROJECT_BAR_HEIGHT / 2, text=project['name'], anchor="w", font=("Segoe UI", 9, "bold"), fill=theme()["TEXT"])

                # Calculate Bar Coordinates
                start_days = (project['start'] - start_date_viz).days
                end_days = (project['end'] - start_date_viz).days
                
                x0 = 100 + start_days * X_SCALE_FACTOR
                x1 = 100 + end_days * X_SCALE_FACTOR
                
                # Draw Project Bar 
                canvas.create_rectangle(x0, y_pos, x1, y_pos + PROJECT_BAR_HEIGHT, 
                                        fill=project['color'], outline="#333333", tags=f"p_{project['id']}")
                                        
                # Draw Progress Bar (Manual %)
                progress_width = (x1 - x0) * (project['progress'] / 100.0)
                canvas.create_rectangle(x0, y_pos, x0 + progress_width, y_pos + PROJECT_BAR_HEIGHT, 
                                        fill=project['color'], stipple="gray50", outline="")
                
                # Percentage text
                canvas.create_text(x1 + 5, y_pos + PROJECT_BAR_HEIGHT / 2, text=f"{project['progress']}%", anchor="w", font=("Segoe UI", 8), fill="#333333")
                
                # Draw Milestones
                for milestone in project['milestones']:
                    milestone_days = (milestone['target'] - start_date_viz).days
                    mx = 100 + milestone_days * X_SCALE_FACTOR
                    
                    # Incomplete color is now black. Complete color is green.
                    marker_color = "green" if milestone['complete'] else "black"
                    
                    # Draw Circle (Cuter Milestone Marker)
                    R = MILESTONE_RADIUS
                    cy = y_pos + PROJECT_BAR_HEIGHT / 2
                    canvas.create_oval(mx - R, cy - R, mx + R, cy + R,
                                        fill=marker_color, outline="#333333", tags=f"m_{project['id']}")
                                        
                    # Tooltip/Label for Milestone
                    canvas.create_text(mx, y_pos - 10, text=milestone['name'], anchor="s", fill=marker_color, font=("Segoe UI", 7))
                
                y_pos += PROJECT_BAR_HEIGHT + 15 
                

        # ----------------------------------------
        # --- MAIN UI LAYOUT (Drawing the Frames)---
        # ----------------------------------------
        
        for widget in content.winfo_children():
            widget.destroy()

        main_frame = tk.Frame(content, bg=theme()["CARD"])
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Column 0: Input Forms
        input_column = tk.Frame(main_frame, bg=theme()["CARD"], padx=10, pady=10)
        input_column.pack(side="left", fill="y", expand=False)
        
        # Column 1: Timeline Visualization
        timeline_column = tk.Frame(main_frame, bg=theme()["CARD"])
        timeline_column.pack(side="left", fill="both", expand=True) 

        # --- Project Input Section ---
        project_frame = tk.LabelFrame(input_column, text="➕ Add New Project", bg=FRAME_BG_COLOR, fg=theme()["TEXT"], padx=10, pady=10) 
        project_frame.pack(fill="x", pady=5)
        
        r = 0
        tk.Label(project_frame, text="Name:", bg=FRAME_BG_COLOR, fg=theme()["TEXT"]).grid(row=r, column=0, sticky="w");
        project_title_entry = tk.Entry(project_frame, width=20);
        project_title_entry.grid(row=r, column=1, columnspan=2, padx=5, sticky="ew"); r+=1
        
        tk.Label(project_frame, text="Start Date:", bg=FRAME_BG_COLOR, fg=theme()["TEXT"]).grid(row=r, column=0, sticky="w");
        project_start_date = DateEntry(project_frame, width=10, date_pattern='yyyy-mm-dd');
        project_start_date.grid(row=r, column=1, padx=5, sticky="w"); r+=1
        
        tk.Label(project_frame, text="End Date:", bg=FRAME_BG_COLOR, fg=theme()["TEXT"]).grid(row=r, column=0, sticky="w");
        project_end_date = DateEntry(project_frame, width=10, date_pattern='yyyy-mm-dd');
        project_end_date.grid(row=r, column=1, padx=5, sticky="w"); r+=1
        
        tk.Label(project_frame, text="Color:", bg=FRAME_BG_COLOR, fg=theme()["TEXT"]).grid(row=r, column=0, sticky="w");
        
        def pick_project_color():
            chosen = colorchooser.askcolor(title="Choose Project Color")
            if chosen[1]:
                project_color_var.set(chosen[1])
                color_preview.config(bg=chosen[1])

        color_btn = tk.Button(project_frame, text="Pick", command=pick_project_color, font=("Segoe UI", 8), bg=theme().get("BTN", "#cccccc"), fg="black")
        color_btn.grid(row=r, column=1, padx=5, sticky="w");
        
        color_preview = tk.Label(project_frame, bg=project_color_var.get(), width=3, height=1, relief="solid", bd=1)
        color_preview.grid(row=r, column=2, padx=5, sticky="w"); r+=1

        tk.Button(project_frame, text="Save Project", command=add_project, bg=theme().get("ACCENT", "#ff5d8f"), fg="white").grid(row=r, column=0, columnspan=3, pady=10)

        # --- Progress Update Section ---
        progress_frame = tk.LabelFrame(input_column, text="📈 Update Progress", bg=FRAME_BG_COLOR, fg=theme()["TEXT"], padx=10, pady=10) 
        progress_frame.pack(fill="x", pady=15)
        
        r = 0
        tk.Label(progress_frame, text="Project:", bg=FRAME_BG_COLOR, fg=theme()["TEXT"]).grid(row=r, column=0, sticky="w");
        progress_project_combo = ttk.Combobox(progress_frame, width=18, state="readonly");
        progress_project_combo.grid(row=r, column=1, padx=5, sticky="ew"); r+=1
        
        tk.Label(progress_frame, text="Progress (%):", bg=FRAME_BG_COLOR, fg=theme()["TEXT"]).grid(row=r, column=0, sticky="w");
        progress_entry = tk.Entry(progress_frame, width=5);
        progress_entry.grid(row=r, column=1, padx=5, sticky="w");
        progress_entry.insert(0, "0")
        r+=1

        tk.Button(progress_frame, text="Update Progress", command=update_progress_action, bg=theme().get("ACCENT", "#ff5d8f"), fg="white").grid(row=r, column=0, columnspan=2, pady=10)

        # --- Milestone Input Section ---
        milestone_frame = tk.LabelFrame(input_column, text="🚩 Add New Milestone", bg=FRAME_BG_COLOR, fg=theme()["TEXT"], padx=10, pady=10) 
        milestone_frame.pack(fill="x", pady=15)
        
        r = 0
        tk.Label(milestone_frame, text="Project:", bg=FRAME_BG_COLOR, fg=theme()["TEXT"]).grid(row=r, column=0, sticky="w");
        project_list_combo = ttk.Combobox(milestone_frame, width=18, state="readonly");
        project_list_combo.grid(row=r, column=1, padx=5, sticky="ew"); r+=1
        
        tk.Label(milestone_frame, text="Milestone Name:", bg=FRAME_BG_COLOR, fg=theme()["TEXT"]).grid(row=r, column=0, sticky="w");
        milestone_name_entry = tk.Entry(milestone_frame, width=20);
        milestone_name_entry.grid(row=r, column=1, padx=5, sticky="ew"); r+=1
        
        tk.Label(milestone_frame, text="Target Date:", bg=FRAME_BG_COLOR, fg=theme()["TEXT"]).grid(row=r, column=0, sticky="w");
        milestone_target_date = DateEntry(milestone_frame, width=10, date_pattern='yyyy-mm-dd');
        milestone_target_date.grid(row=r, column=1, padx=5, sticky="w"); r+=1

        tk.Button(milestone_frame, text="Save Milestone", command=add_milestone, bg=theme().get("ACCENT", "#ff5d8f"), fg="white").grid(row=r, column=0, columnspan=2, pady=10)

        # --- Timeline Visualization Canvas ---
        
        canvas_container = tk.Frame(timeline_column)
        canvas_container.pack(fill="both", expand=True)

        v_scrollbar = tk.Scrollbar(canvas_container, orient="vertical")
        h_scrollbar = tk.Scrollbar(canvas_container, orient="horizontal")

        canvas = tk.Canvas(canvas_container, bg="white", yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        v_scrollbar.config(command=canvas.yview)
        h_scrollbar.config(command=canvas.xview)
        
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        canvas.pack(side="left", fill="both", expand=True) 

        # Initial load and draw
        refresh_timeline()
    
    # Monthly Overview Page
    if pn == "MonthlyOverview":
        # Ensure necessary imports are available at this scope
        import tkinter as tk
        from tkinter import Toplevel
        from datetime import datetime, date, timedelta
        import calendar as py_calendar
        
        # --- STATE ---
        current_month_dt = date.today().replace(day=1) 
        
        # --- DB HELPERS ---
        
        def get_monthly_timeblock_summary(start_date):
            """Fetches a summary of time blocks (count) for every day of the given month."""
            
            next_month = start_date.replace(day=28) + timedelta(days=4)
            end_of_month = next_month - timedelta(days=next_month.day)
            
            start_date_iso = start_date.isoformat()
            end_date_iso = end_of_month.isoformat()
            
            conn = db_connect()
            c = conn.cursor()
            
            rows = c.execute("""
                SELECT date, COUNT(id) 
                FROM timeblocks 
                WHERE date BETWEEN ? AND ?
                GROUP BY date
            """, (start_date_iso, end_date_iso)).fetchall()
            
            conn.close()
            summary = {r[0]: r[1] for r in rows}
            return summary
            
        def get_daily_timeblocks(target_date_str):
            """NEW: Fetches all time block details for a specific date."""
            conn = db_connect()
            c = conn.cursor()
            rows = c.execute("""
                SELECT start_time, end_time, title, color, notes 
                FROM timeblocks 
                WHERE date = ?
                ORDER BY start_time ASC
            """, (target_date_str,)).fetchall()
            conn.close()
            return rows


        # --- UI & NAVIGATION ---
        
        for widget in content.winfo_children():
            widget.destroy()

        # --- Header Frame (Top Row) ---
        header_frame = tk.Frame(content, bg=theme()["CARD"], pady=10)
        header_frame.pack(fill="x", padx=10)

        month_label = tk.Label(header_frame, text="", font=("Segoe UI", 16, "bold"), 
                            bg=theme()["CARD"], fg=theme()["ACCENT"])
        month_label.pack(side="left", expand=True)
        
        # Navigation Function
        def navigate_month(direction):
            global current_month_dt
            
            if direction == 'prev':
                current_month_dt = current_month_dt.replace(day=1) - timedelta(days=1)
                current_month_dt = current_month_dt.replace(day=1)
            elif direction == 'next':
                next_month = current_month_dt.replace(day=28) + timedelta(days=4)
                current_month_dt = next_month.replace(day=1)
                
            refresh_monthly_view()

        # Navigation Buttons
        tk.Button(header_frame, text="< Prev Month", command=lambda: navigate_month('prev'), 
                bg=theme().get("BTN", "#cccccc"), fg="black").pack(side="left", padx=5)

        tk.Button(header_frame, text="Next Month >", command=lambda: navigate_month('next'), 
                bg=theme().get("BTN", "#cccccc"), fg="black").pack(side="right", padx=5)


        # --- Calendar Grid Frame ---
        calendar_grid_frame = tk.Frame(content, bg=theme()["CARD"])
        calendar_grid_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        
        # --- POP-UP DISPLAY FUNCTION (The core change) ---
        def on_date_click(clicked_date_str):
            """Fetches daily time blocks and shows them in a pop-up window."""
            
            daily_blocks = get_daily_timeblocks(clicked_date_str)
            
            popup = Toplevel(content)
            popup.title(f"Time Blocks for {clicked_date_str}")
            popup.geometry("350x400")
            popup.config(bg=theme()["CARD"])

            tk.Label(popup, text=f"Blocks for: {clicked_date_str}", font=("Segoe UI", 12, "bold"),
                    bg=theme()["CARD"], fg=theme()["TEXT"]).pack(pady=10)

            # Container for the list of blocks
            list_frame = tk.Frame(popup, bg="white")
            list_frame.pack(padx=10, pady=5, fill="both", expand=True)

            if not daily_blocks:
                tk.Label(list_frame, text="No time blocks scheduled.", bg="white", 
                        fg=theme()["TEXT"], pady=20).pack(fill="x")
            else:
                row_num = 0
                for start, end, title, color, notes in daily_blocks:
                    block_frame = tk.Frame(list_frame, bg="white", padx=5, pady=5, bd=1, relief="groove")
                    block_frame.pack(fill="x", pady=3)
                    
                    # Use a small colored square (or strip)
                    color_strip = tk.Label(block_frame, bg=color, width=1, height=2)
                    color_strip.pack(side="left", fill="y", padx=(0, 5))
                    
                    # Display block details
                    details_text = f"🕒 {start} - {end}\n{title}"
                    details_label = tk.Label(block_frame, text=details_text, justify="left", 
                                            bg="white", fg="black", font=("Segoe UI", 10, "bold"))
                    details_label.pack(side="left", fill="x", expand=True)
                    
                    # Optionally add a small notes indicator if notes exist
                    if notes and notes.strip():
                        tk.Label(block_frame, text="📝", bg="white").pack(side="right", padx=5)

                    row_num += 1

            tk.Button(popup, text="Close", command=popup.destroy, 
                    bg=theme()["ACCENT"], fg="white").pack(pady=10)


        # --- REFRESH FUNCTION ---
        
        def refresh_monthly_view():
            month_label.config(text=current_month_dt.strftime("%B %Y"))
            
            for widget in calendar_grid_frame.winfo_children():
                widget.destroy()
                
            activity_summary = get_monthly_timeblock_summary(current_month_dt)
            
            # Day Headers (S, M, T, W, T, F, S)
            days_of_week = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            for i, day in enumerate(days_of_week):
                tk.Label(calendar_grid_frame, text=day, bg=theme()["CARD"], fg=theme()["TEXT"], 
                        font=("Segoe UI", 10, "bold")).grid(row=0, column=i, sticky="nsew", ipady=5)

            cal = py_calendar.Calendar(firstweekday=py_calendar.SUNDAY)
            month_matrix = cal.monthdatescalendar(current_month_dt.year, current_month_dt.month)

            row_index = 1
            
            # Populate the grid
            for week in month_matrix:
                for col_index, day_dt in enumerate(week):
                    
                    date_str = day_dt.isoformat()
                    
                    # Default appearance
                    bg_color = theme()["CARD"] 
                    fg_color = theme()["TEXT"]
                    font_style = ("Segoe UI", 10)
                    
                    has_activity = activity_summary.get(date_str, 0) > 0
                    is_current_month = day_dt.month == current_month_dt.month
                    
                    # Apply visual rules
                    if is_current_month:
                        if has_activity:
                            bg_color = "#e0f2f1" # Light Blue/Teal for scheduled activity
                            font_style = ("Segoe UI", 10, "bold")
                            
                        if day_dt == date.today():
                            fg_color = theme()["ACCENT"]
                            if not has_activity: 
                                bg_color = "#fbe5e7" # Light pink for today
                    else:
                        fg_color = "#aaaaaa" 
                        bg_color = theme()["CARD"]
                        
                    # Create the cell frame
                    cell_frame = tk.Frame(calendar_grid_frame, bg=bg_color, bd=1, relief="solid")
                    cell_frame.grid(row=row_index, column=col_index, sticky="nsew", padx=1, pady=1)

                    # Date Label
                    date_label = tk.Label(cell_frame, text=day_dt.day, bg=bg_color, fg=fg_color, font=font_style)
                    date_label.pack(pady=5)
                    
                    # Activity Indicator
                    if has_activity and is_current_month:
                        tk.Label(cell_frame, text="•", bg=bg_color, fg="blue", 
                                font=("Segoe UI", 12)).pack(pady=0)
                    
                    # Bind click event to the cell frame (and the label)
                    cell_frame.bind('<Button-1>', lambda e, d=date_str: on_date_click(d))
                    date_label.bind('<Button-1>', lambda e, d=date_str: on_date_click(d))
                    
                row_index += 1

            # Configure rows and columns to expand equally
            for i in range(7):
                calendar_grid_frame.grid_columnconfigure(i, weight=1)
            for i in range(row_index):
                calendar_grid_frame.grid_rowconfigure(i, weight=1)

        # Initial call to populate the view
        refresh_monthly_view()
    
    # Weekly Overview Page    
    if pn == "WeeklyOverview":
    
    # --- Helper Function (INSIDE THE BLOCK) ---
        def get_current_week_start():
            """Calculates the start date of the current week (Monday)."""
            today = datetime.now().date()
            # Monday is day 0
            start_of_week = today - timedelta(days=today.weekday())
            return start_of_week.strftime("%Y-%m-%d")

        # --- Variables ---
        current_week_start_var = tk.StringVar()
        # daily_entries will hold the Text widgets
        daily_entries = {} 
        # daily_labels will hold the Date Label widgets (e.g., Mon: 2025-11-24)
        daily_labels = {} 

        # --- Database Functions ---

        def fetch_week_starts():
            """Fetches all week_start dates from the DB for the combobox."""
            conn = db_connect()
            c = conn.cursor()
            rows = c.execute("SELECT week_start FROM news_weekly_overview ORDER BY week_start DESC").fetchall()
            conn.close()
            return [row[0] for row in rows]

        def ensure_week_exists(week_start):
            """
            Checks if a row for the given week_start date exists. 
            If not, a new row is inserted with empty values.
            """
            conn = db_connect()
            c = conn.cursor()
            
            c.execute("SELECT week_start FROM news_weekly_overview WHERE week_start=?", (week_start,))
            if c.fetchone() is None:
                try:
                    # Insert a new row with empty data for all columns
                    c.execute("""
                        INSERT INTO news_weekly_overview (week_start, priorities, mon, tue, wed, thu, fri, sat, sun)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (week_start, "", "", "", "", "", "", "", ""))
                    conn.commit()
                except Exception as e:
                    messagebox.showerror("Database Error", f"Failed to create new week entry: {e}")
            
            conn.close()

        def clear_ui():
            """Clears all text entry fields."""
            priorities_entry.delete("1.0", "end")
            for entry_widget in daily_entries.values():
                entry_widget.delete("1.0", "end")

        def update_daily_dates(week_start_str):
            """Calculates and updates the date label for each day of the selected week."""
            if not week_start_str or week_start_str == "No Weeks Available":
                for label in daily_labels.values():
                    label.config(text=": ---")
                return

            try:
                week_start_date = datetime.strptime(week_start_str, "%Y-%m-%d").date()
            except ValueError:
                return 
            
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
            
            for i, day in enumerate(days):
                current_date = week_start_date + timedelta(days=i)
                display_text = f"{day_names[i]}: {current_date.strftime('%Y-%m-%d')}"
                daily_labels[day].config(text=display_text)


        def load_week_data(week_start):
            """Loads data for the selected week into the UI elements."""
            clear_ui()
            update_daily_dates(week_start) # Update dates first
            
            if not week_start or week_start == "No Weeks Available":
                return
                
            conn = db_connect()
            c = conn.cursor()
            row = c.execute("SELECT priorities, mon, tue, wed, thu, fri, sat, sun FROM news_weekly_overview WHERE week_start=?", (week_start,)).fetchone()
            conn.close()

            if row:
                priorities, mon, tue, wed, thu, fri, sat, sun = row
                
                # Populate Priorities
                if priorities:
                    priorities_entry.insert("1.0", priorities)
                
                # Populate Daily Notes
                daily_data = {"mon": mon, "tue": tue, "wed": wed, "thu": thu, "fri": fri, "sat": sat, "sun": sun}
                for day, entry_widget in daily_entries.items():
                    data = daily_data.get(day)
                    if data:
                        entry_widget.insert("1.0", data)

        def save_overview(week_start):
            """Saves the current data for the specified week."""
            if not week_start or week_start == "No Weeks Available":
                messagebox.showwarning("Error", "No week selected to save.")
                return

            new_priorities = priorities_entry.get("1.0", "end").strip()
            new_daily_notes = {day: entry.get("1.0", "end").strip() for day, entry in daily_entries.items()}

            conn = db_connect()
            c = conn.cursor()
            
            try:
                # Update the existing row
                c.execute("""
                    UPDATE news_weekly_overview
                    SET priorities=?, mon=?, tue=?, wed=?, thu=?, fri=?, sat=?, sun=?
                    WHERE week_start=?
                """, (
                    new_priorities, 
                    new_daily_notes["mon"], new_daily_notes["tue"], new_daily_notes["wed"], 
                    new_daily_notes["thu"], new_daily_notes["fri"], new_daily_notes["sat"], 
                    new_daily_notes["sun"], week_start
                ))
                conn.commit()
                messagebox.showinfo("Success", f"Overview for {week_start} saved.")
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to save data: {e}")
            finally:
                conn.close()
                
        # --- Navigation Logic ---
        def navigate_week(direction):
            """Moves the selected week one week forward or backward."""
            current_week_str = current_week_start_var.get()
            
            if not current_week_str or current_week_str == "No Weeks Available":
                return

            try:
                current_date = datetime.strptime(current_week_str, "%Y-%m-%d").date()
            except ValueError:
                messagebox.showerror("Error", "Invalid week start date format.")
                return

            if direction == 'prev':
                new_date = current_date - timedelta(days=7)
            elif direction == 'next':
                new_date = current_date + timedelta(days=7)
            else:
                return

            new_week_str = new_date.strftime("%Y-%m-%d")
            
            # 1. Ensure the new week exists (creates if needed)
            ensure_week_exists(new_week_str)

            # 2. Update the combobox values
            week_starts = fetch_week_starts()
            week_combobox['values'] = week_starts
            
            # 3. Set the new week as selected in the combobox and load the data
            current_week_start_var.set(new_week_str)
            load_week_data(new_week_str)

        # --- UI Setup ---

        for widget in content.winfo_children():
            widget.destroy()

        # --- Page Header ---
        tk.Label(
            content,
            text="📅 Weekly Overview",
            font=("Segoe UI", 14, "bold"),
            bg=theme()["CARD"],
            fg=theme()["TEXT"]
        ).pack(anchor="nw", pady=12, padx=12)

        # --- Week Selection and View Frame ---
        view_frame = tk.Frame(content, bg=theme()["CARD"])
        view_frame.pack(fill="x", padx=12, pady=(0, 8))
        
        # 1. New Previous Week Button
        tk.Button(view_frame, text="< Prev Week", bg=theme()["BTN"], fg="black", command=lambda: navigate_week('prev')).pack(side="left", padx=2, pady=2)

        tk.Label(view_frame, text="Select Week (Start Date):", bg=theme()["CARD"], fg=theme()["TEXT"]).pack(side="left", padx=4, pady=2)
        
        week_combobox = ttk.Combobox(view_frame, textvariable=current_week_start_var, state="readonly", width=15)
        week_combobox.pack(side="left", padx=4, pady=2)
        
        # 2. New Next Week Button
        tk.Button(view_frame, text="Next Week >", bg=theme()["BTN"], fg="black", command=lambda: navigate_week('next')).pack(side="left", padx=2, pady=2)
        
        # Save Button
        tk.Button(view_frame, text="Save Changes", bg=theme()["BTN"], fg="white", command=lambda: save_overview(current_week_start_var.get())).pack(side="right", padx=4, pady=2)
        
        # --- Detail Input and Display Area ---
        details_frame = tk.Frame(content, bg=theme()["CARD"])
        details_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Priorities Section
        priorities_frame = tk.Frame(details_frame, bg=theme()["CARD"])
        priorities_frame.pack(fill="x", pady=5)
        tk.Label(priorities_frame, text="🎯 **Priorities for the Week**", font=("Segoe UI", 10, "bold"), bg=theme()["CARD"], fg=theme()["TEXT"]).pack(anchor="nw", padx=4, pady=2)
        priorities_entry = tk.Text(priorities_frame, width=80, height=3, bg="#ffe6ef", fg="#000", wrap="word")
        priorities_entry.pack(fill="x", padx=4, pady=2)
        
        # Daily Notes Section
        daily_notes_frame = tk.Frame(details_frame, bg=theme()["CARD"])
        daily_notes_frame.pack(fill="both", expand=True, pady=5)

        days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        for i, day in enumerate(days):
            day_frame = tk.Frame(daily_notes_frame, bg=theme()["CARD"])
            day_frame.grid(row=i, column=0, sticky="ew", pady=2, padx=4) 
            daily_notes_frame.grid_columnconfigure(0, weight=1)

            # Updated Label to hold the Day Name AND Date
            date_label = tk.Label(day_frame, text=f"{day_names[i]}: ---", width=25, anchor="w", bg=theme()["CARD"], fg=theme()["TEXT"], font=("Segoe UI", 10, "bold"))
            date_label.pack(side="left", padx=4)
            daily_labels[day] = date_label # Store the label widget for later date updating
            
            daily_entries[day] = tk.Text(day_frame, width=65, height=2, bg="#ffe6ef", fg="#000", wrap="word")
            daily_entries[day].pack(side="left", expand=True, fill="x", padx=4)

        # --- Page Refresh Logic ---

        def refresh_page():
            """Handles ensuring the current week exists, fetches all weeks, and loads data."""
            
            selected_week = get_current_week_start()
            
            # 1. Ensure the current week (starting Monday) exists in the database
            ensure_week_exists(selected_week)

            # 2. Fetch all week start dates (including the one we may have just added)
            week_starts = fetch_week_starts()
            week_combobox['values'] = week_starts

            # 3. Set the current week in the combobox
            if selected_week in week_starts:
                current_week_start_var.set(selected_week)
            elif week_starts:
                current_week_start_var.set(week_starts[0])
            else:
                current_week_start_var.set("No Weeks Available")

            # 4. Load the data for the selected week (this calls update_daily_dates)
            load_week_data(current_week_start_var.get())

        # Bind the combobox selection change to the loading function
        week_combobox.bind("<<ComboboxSelected>>", lambda event: load_week_data(current_week_start_var.get()))

        # --- Initial Refresh ---
        refresh_page()
    
    # DUE ITEMS PAGE // REMINDERS                
    if pn == "Due Items":
        import tkinter as tk
        from tkinter import messagebox, ttk
        from datetime import datetime

        # --- SAFETY: Ensure refresh_due_widget exists ---
        if "refresh_due_widget" not in globals():
            def refresh_due_widget():
                pass

        # --- Page Header ---
        tk.Label(content, text="📝 Due Items",
                font=("Segoe UI", 14, "bold"),
                bg=theme()["CARD"], fg=theme()["TEXT"]).pack(anchor="nw", pady=12, padx=12)

        # --- Input Section ---
        input_frame = tk.Frame(content, bg=theme()["CARD"])
        input_frame.pack(fill="x", padx=12, pady=(0, 8))

        tk.Label(input_frame, text="Title:", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=0, column=0, padx=4, pady=2)
        title_entry_due = tk.Entry(input_frame, bg="#ffe6ef", fg="#000")
        title_entry_due.grid(row=0, column=1, padx=4, pady=2)

        tk.Label(input_frame, text="Due Date (YYYY-MM-DD):", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=0, column=2, padx=4, pady=2)
        due_date_entry = tk.Entry(input_frame, bg="#ffe6ef", fg="#000")
        due_date_entry.grid(row=0, column=3, padx=4, pady=2)

        tk.Label(input_frame, text="Notes:", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=1, column=0, padx=4, pady=2)
        notes_entry = tk.Entry(input_frame, bg="#ffe6ef", fg="#000", width=40)
        notes_entry.grid(row=1, column=1, columnspan=3, padx=4, pady=2, sticky="w")

        tk.Label(input_frame, text="Status:", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=2, column=0, padx=4, pady=2)
        due_status_combo = ttk.Combobox(input_frame, values=["Pending", "Completed"], state="readonly", width=12)
        due_status_combo.set("Pending")
        due_status_combo.grid(row=2, column=1, padx=4, pady=2)

        # --- Scrollable Table ---
        canvas = tk.Canvas(content, bg=theme()["CARD"])
        scrollbar = tk.Scrollbar(content, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=theme()["CARD"])
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        headers = ["Title", "Due Date", "Notes", "Status", "Actions"]
        header_frame = tk.Frame(scroll_frame, bg=theme()["CARD"])
        header_frame.pack(fill="x", pady=(0, 2))
        for h in headers:
            tk.Label(header_frame, text=h, bg=theme()["CARD"], fg=theme()["TEXT"],
                    font=("Segoe UI", 10, "bold"), borderwidth=1, relief="solid", padx=4, pady=2).pack(side="left", expand=True, fill="x")

        # --- Functions ---
        def refresh_due_items_table():
            for widget in scroll_frame.winfo_children():
                if widget != header_frame:
                    widget.destroy()
            conn = db_connect()
            c = conn.cursor()
            rows = c.execute("SELECT id, title, due_date, notes, status FROM due_items ORDER BY due_date ASC").fetchall()
            conn.close()

            for row in rows:
                r_frame = tk.Frame(scroll_frame, bg=theme()["CARD"])
                r_frame.pack(fill="x", pady=1)
                id_, title, due_date, notes, status = row

                tk.Label(r_frame, text=title, bg=theme()["CARD"], fg=theme()["TEXT"],
                        font=("Segoe UI", 10), borderwidth=1, relief="solid", padx=4, pady=2).pack(side="left", expand=True, fill="x")
                tk.Label(r_frame, text=due_date, bg=theme()["CARD"], fg=theme()["TEXT"],
                        font=("Segoe UI", 10), borderwidth=1, relief="solid", padx=4, pady=2).pack(side="left", expand=True, fill="x")
                tk.Label(r_frame, text=notes, bg=theme()["CARD"], fg=theme()["TEXT"],
                        font=("Segoe UI", 10), borderwidth=1, relief="solid", padx=4, pady=2).pack(side="left", expand=True, fill="x")
                tk.Label(r_frame, text=status, bg=theme()["CARD"], fg=theme()["TEXT"],
                        font=("Segoe UI", 10), borderwidth=1, relief="solid", padx=4, pady=2).pack(side="left", expand=True, fill="x")

                btn_frame = tk.Frame(r_frame, bg=theme()["CARD"])
                btn_frame.pack(side="left", expand=True, fill="x")

                def edit_item(item_id=id_):
                    edit_win = tk.Toplevel()
                    edit_win.title("Edit Due Item")
                    edit_win.configure(bg="white")

                    tk.Label(edit_win, text="Title:").grid(row=0, column=0, padx=4, pady=2)
                    e_title = tk.Entry(edit_win)
                    e_title.insert(0, title)
                    e_title.grid(row=0, column=1, padx=4, pady=2)

                    tk.Label(edit_win, text="Due Date (YYYY-MM-DD):").grid(row=1, column=0, padx=4, pady=2)
                    e_due = tk.Entry(edit_win)
                    e_due.insert(0, due_date)
                    e_due.grid(row=1, column=1, padx=4, pady=2)

                    tk.Label(edit_win, text="Notes:").grid(row=2, column=0, padx=4, pady=2)
                    e_notes = tk.Entry(edit_win)
                    e_notes.insert(0, notes)
                    e_notes.grid(row=2, column=1, padx=4, pady=2)

                    tk.Label(edit_win, text="Status:").grid(row=3, column=0, padx=4, pady=2)
                    e_status = ttk.Combobox(edit_win, values=["Pending", "Completed"], state="readonly")
                    e_status.set(status)
                    e_status.grid(row=3, column=1, padx=4, pady=2)

                    def save_edit():
                        conn = db_connect()
                        c = conn.cursor()
                        c.execute("""
                            UPDATE due_items SET title=?, due_date=?, notes=?, status=? WHERE id=?
                        """, (e_title.get(), e_due.get(), e_notes.get(), e_status.get(), item_id))
                        conn.commit()
                        conn.close()
                        refresh_due_items_table()
                        if "refresh_due_widget" in globals():
                            refresh_due_widget()
                        edit_win.destroy()

                    tk.Button(edit_win, text="Save", bg="#ff5d8f", fg="white", command=save_edit).grid(row=4, column=0, columnspan=2, pady=4)

                def delete_item(item_id=id_):
                    if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this item?"):
                        conn = db_connect()
                        c = conn.cursor()
                        c.execute("DELETE FROM due_items WHERE id=?", (item_id,))
                        conn.commit()
                        conn.close()
                        refresh_due_items_table()
                        if "refresh_due_widget" in globals():
                            refresh_due_widget()

                tk.Button(btn_frame, text="Edit", bg="#ff5d8f", fg="white", command=edit_item, width=5).pack(side="left", padx=1)
                tk.Button(btn_frame, text="Del", bg="#ffb6c8", fg="white", command=delete_item, width=5).pack(side="left", padx=1)

        # --- Add Button Function ---
        def add_due_item():
            title = title_entry_due.get().strip()
            due_date = due_date_entry.get().strip()
            notes = notes_entry.get().strip()
            status = due_status_combo.get()

            if not title or not due_date:
                messagebox.showwarning("Missing Info", "Title and Due Date are required.")
                return
            try:
                datetime.strptime(due_date, "%Y-%m-%d")
            except:
                messagebox.showwarning("Invalid Date", "Please enter date in YYYY-MM-DD format.")
                return

            conn = db_connect()
            c = conn.cursor()
            c.execute("""
                INSERT INTO due_items (title, due_date, notes, status)
                VALUES (?, ?, ?, ?)
            """, (title, due_date, notes, status))
            conn.commit()
            conn.close()

            refresh_due_items_table()
            if "refresh_due_widget" in globals():
                refresh_due_widget()

            title_entry_due.delete(0, "end")
            due_date_entry.delete(0, "end")
            notes_entry.delete(0, "end")
            due_status_combo.set("Pending")

        tk.Button(input_frame, text="Add", bg="#ff5d8f", fg="white", command=add_due_item).grid(row=2, column=3, padx=4, pady=2)

        # --- Initial Refresh ---
        refresh_due_items_table()
        if "refresh_due_widget" in globals():
            refresh_due_widget()
    
    # TIME BLOCKING PAGE
    if pn == "Time Blocking":
        import tkinter as tk
        from tkinter import messagebox, colorchooser
        from tkcalendar import DateEntry 
        from datetime import datetime, date, timedelta
        
        # Define constants for timeline drawing (COMPACT)
        HOUR_HEIGHT = 35     # Pixels per hour 
        TIMELINE_WIDTH = 250 # Width of the canvas 
        HOUR_START = 0       
        HOUR_END = 24        
        
        # Define the input background color
        INPUT_BG_COLOR = "#ffe6ef" # Light pink/peach color

        # --- INPUT WIDGET GLOBALS (Defined later, but referenced by nested functions) ---
        # Need to declare these here so nested functions like 'add_block' can use them 
        # before they are fully initialized at the bottom of the page setup.
        timeblock_title_entry = None
        start_entry = None
        end_entry = None
        notes_entry = None
        color_var = tk.StringVar(value=theme().get("BTN", "#cccccc"))
        color_preview = None
        tb_date = None
        timeline_canvas = None

        # --- DB HELPERS ---
        def load_timeblocks(target_date):
            conn = db_connect()
            c = conn.cursor()
            rows = c.execute("""
                SELECT id, start_time, end_time, title, color, notes 
                FROM timeblocks 
                WHERE date = ?
                ORDER BY start_time ASC
            """, (target_date.isoformat(),)).fetchall()
            conn.close()
            return rows

        def save_timeblock(date_val, start, end, title, color, notes):
            conn = db_connect()
            c = conn.cursor()
            c.execute("""
                INSERT INTO timeblocks (date, start_time, end_time, title, color, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (date_val, start, end, title, color, notes))
            conn.commit()
            conn.close()
            # Explicit refresh after save
            refresh_timeblocks() 

        def delete_timeblock(block_id):
            if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this time block?"):
                return
                
            conn = db_connect()
            c = conn.cursor()
            c.execute("DELETE FROM timeblocks WHERE id = ?", (block_id,))
            conn.commit()
            conn.close()
            # Explicit refresh after delete
            refresh_timeblocks() 

        # --- CANVAS HELPER ---
        def time_to_y(time_str):
            """Converts 'HH:MM' string to a Y-coordinate on the canvas."""
            try:
                # We use datetime.strptime to handle time conversion consistently
                t = datetime.strptime(time_str, "%H:%M").time()
                total_minutes = t.hour * 60 + t.minute
                y_coord = int((total_minutes / 60) * HOUR_HEIGHT)
                return y_coord
            except ValueError:
                return 0 

        def safe_color(c):
            """Ensures the color is a valid hex code or returns a fallback."""
            if not c or (isinstance(c, str) and not (c.startswith("#") and len(c) == 7)):
                return theme().get("BTN", "#cccccc") 
            return c

        # --- NAVIGATION FUNCTION ---
        def navigate_day(direction):
            """Moves the selected date one day forward or backward."""
            current_date = tb_date.get_date()
            
            if direction == 'prev':
                new_date = current_date - timedelta(days=1)
            elif direction == 'next':
                new_date = current_date + timedelta(days=1)
            else:
                return

            tb_date.set_date(new_date)
            refresh_timeblocks()
            
        # --- ACTION FUNCTION ---
        def add_block():
            """Handles input validation and saving a new time block."""
            
            # 1. Get input values (Correctly using .get() for Entry and Text widgets)
            s = start_entry.get().strip()
            e = end_entry.get().strip()
            t = timeblock_title_entry.get().strip()
            # Correctly retrieving notes from the tk.Text widget
            n = notes_entry.get("1.0", "end-1c").strip() 
            
            if not s or not e or not t:
                messagebox.showwarning("Warning", "Title, Start, and End times are required.")
                return
            
            # 2. Validation Logic (Time format and sequence)
            try:
                # Check for valid time format
                start_dt = datetime.strptime(s, "%H:%M")
                end_dt = datetime.strptime(e, "%H:%M")
                
                # Check if End time is after Start time
                if end_dt <= start_dt:
                    messagebox.showerror("Error", "End time must be strictly after the Start time.")
                    return
                    
            except ValueError:
                messagebox.showerror("Error", "Time format must be valid HH:MM (e.g., 09:30 or 15:00).")
                return
            
            # 3. Save to DB
            save_timeblock(
                tb_date.get_date().isoformat(),
                s,
                e,
                t,
                color_var.get(),
                n
            )

            # 4. Reset fields
            timeblock_title_entry.delete(0, "end")
            start_entry.delete(0, "end")
            end_entry.delete(0, "end")
            notes_entry.delete("1.0", "end")
            
            # Reset color back to default/theme
            default_color = theme().get("BTN", "#cccccc")
            color_var.set(default_color)
            color_preview.config(bg=default_color)
            
            
        def refresh_timeblocks():
            """Clears the canvas, loads data for the selected date, and redraws the timeline."""
            timeline_canvas.delete("all") 

            current_date_obj = tb_date.get_date()
            rows = load_timeblocks(current_date_obj)

            # 1. Draw the Timeline Grid (Hour Markings)
            timeline_canvas.create_text(TIMELINE_WIDTH / 2, 10, text=f"Timeline for {current_date_obj.isoformat()}", 
                                        fill=theme().get("TEXT", "black"), font=("Segoe UI", 10, "bold"))
                                        
            for hour in range(HOUR_START, HOUR_END + 1):
                # +30 offset to push content below the header text
                y = (hour - HOUR_START) * HOUR_HEIGHT + 30 
                
                # Draw hour line
                timeline_canvas.create_line(40, y, TIMELINE_WIDTH, y, fill="#dddddd")
                
                # Draw hour label 
                hour_label = f"{hour:02d}:00"
                timeline_canvas.create_text(20, y, anchor="center", text=hour_label, fill=theme().get("TEXT", "black"), font=("Segoe UI", 8, "bold"))

            if not rows:
                timeline_canvas.create_text(TIMELINE_WIDTH / 2, 60, text="No time blocks planned.", 
                                            fill=theme().get("TEXT", "gray"), font=("Segoe UI", 10))
                return

            # 2. Draw the Time Blocks 
            for block_id, start, end, title, color, notes in rows:
                block_color = safe_color(color)
                
                # +30 offset must be applied to y coordinates
                y_start = time_to_y(start) + 30 
                y_end = time_to_y(end) + 30 
                
                x0 = 50 
                x1 = TIMELINE_WIDTH - 10 
                
                # Draw the colored rectangle
                timeline_canvas.create_rectangle(x0, y_start, x1, y_end, 
                                                fill=block_color, 
                                                outline=block_color, 
                                                width=1)
                
                # Add the title/info text
                info = f"{start} - {end} | {title}"
                text_y = y_start + 5
                
                # Draw the primary text
                timeline_canvas.create_text(x0 + 5, text_y, anchor="nw", 
                                            text=info, fill="black", font=("Segoe UI", 8, "bold"),
                                            width=(x1 - x0) - 10) 
                
                # Add a delete tag/icon (bind to click)
                delete_tag = f"delete_{block_id}"
                delete_text_x = x1 - 10
                delete_text_y = y_start + 10
                
                timeline_canvas.create_text(delete_text_x, delete_text_y, anchor="ne", 
                                            text="❌", fill="red", tags=(delete_tag,), font=("Segoe UI", 9))
                
                # Bind the click event to the delete tag, passing the block ID
                timeline_canvas.tag_bind(delete_tag, '<Button-1>', 
                                        lambda e, bid=block_id: delete_timeblock(bid))


        # --- UI SETUP ---
        
        for widget in content.winfo_children():
            widget.destroy()

        # --- 1. Header & Date Selection (Top Row) ---
        header = tk.Frame(content, bg=theme()["CARD"])
        header.pack(fill="x", pady=10, padx=10)

        # Previous Day Button
        tk.Button(header, text="< Prev Day", command=lambda: navigate_day('prev'), 
                bg=theme().get("BTN", "#cccccc"), fg="black").pack(side="left", padx=5)

        tk.Label(header, text="📅 Time Blocking: Select Date:", bg=theme()["CARD"], 
                fg=theme()["TEXT"], font=("Segoe UI", 12, "bold")).pack(side="left")

        tb_date = DateEntry(
            header, width=12, date_pattern='yyyy-mm-dd',
            background='darkblue', foreground='white'
        )
        tb_date.set_date(date.today())
        tb_date.pack(side="left", padx=10)
        
        # Next Day Button
        tk.Button(header, text="Next Day >", command=lambda: navigate_day('next'), 
                bg=theme().get("BTN", "#cccccc"), fg="black").pack(side="left", padx=5)

        # --- 2. Main Content Frame (Two Columns) ---
        main_frame = tk.Frame(content, bg=theme()["CARD"])
        main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Column 0: Input Form
        input_column = tk.Frame(main_frame, bg=theme()["CARD"], padx=10, pady=10)
        input_column.pack(side="left", fill="y", expand=False)
        
        # Column 1: Timeline Visualization
        timeline_column = tk.Frame(main_frame, bg=theme()["CARD"], bd=1, relief="sunken")
        timeline_column.pack(side="left", fill="both", expand=True) 

        # --- INPUT FORM (COMPACT LAYOUT) ---
        form = tk.Frame(input_column, bg=theme()["CARD"])
        form.pack(fill="x", expand=True)
        
        # Row 0: Title 
        tk.Label(form, text="Title:", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=0, column=0, sticky="w", pady=2)
        timeblock_title_entry = tk.Entry(form, width=30, bg=INPUT_BG_COLOR) 
        timeblock_title_entry.grid(row=0, column=1, columnspan=3, padx=5, sticky="ew", pady=2)
        
        # Row 1: Start Time and End Time
        tk.Label(form, text="Start (HH:MM):", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=1, column=0, sticky="w", pady=2)
        start_entry = tk.Entry(form, width=8, bg=INPUT_BG_COLOR)
        start_entry.grid(row=1, column=1, sticky="w", pady=2, padx=(5, 0))

        tk.Label(form, text="End (HH:MM):", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=1, column=2, sticky="w", pady=2, padx=(5, 0))
        end_entry = tk.Entry(form, width=8, bg=INPUT_BG_COLOR)
        end_entry.grid(row=1, column=3, sticky="w", pady=2, padx=(5, 0))

        # Row 2: Color Picker and Add Block Button
        tk.Label(form, text="Color:", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=2, column=0, sticky="w", pady=2)
        # color_var already defined globally

        def pick_color():
            chosen = colorchooser.askcolor(title="Choose a color")
            if chosen[1]:
                color_var.set(chosen[1])
                color_preview.config(bg=chosen[1])

        color_btn = tk.Button(form, text="Pick Color", command=pick_color, bg=theme().get("ACCENT", "#ff5d8f"), fg="white", font=("Segoe UI", 8))
        color_btn.grid(row=2, column=1, sticky="w", pady=2, padx=(5, 0))

        color_preview = tk.Label(form, bg=color_var.get(), width=3, height=1, relief="solid", bd=1)
        color_preview.grid(row=2, column=2, padx=5, sticky="w", pady=2)

        tk.Button(
            form, text="Add Block",
            command=add_block,
            bg=theme().get("ACCENT", "#ff5d8f"), fg="white"
        ).grid(row=2, column=3, pady=2, sticky="w") 

        # Row 3: Notes (Full width)
        tk.Label(form, text="Notes:", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=3, column=0, sticky="nw", pady=2)
        notes_entry = tk.Text(form, width=30, height=3, bg=INPUT_BG_COLOR) 
        notes_entry.grid(row=3, column=1, columnspan=3, pady=5, sticky="ew", padx=(5, 0))
        
        form.grid_columnconfigure(3, weight=1) 
        
        # --- YPT-STYLE TIMELINE VIEW (In timeline_column) ---
        
        canvas_height = (HOUR_END - HOUR_START) * HOUR_HEIGHT + 40 
        
        timeline_canvas = tk.Canvas(timeline_column, bg="white", width=TIMELINE_WIDTH, height=500, 
                                    scrollregion=(0, 0, TIMELINE_WIDTH, canvas_height))
        
        v_scrollbar = tk.Scrollbar(timeline_column, orient="vertical", command=timeline_canvas.yview)
        timeline_canvas.configure(yscrollcommand=v_scrollbar.set)
        
        v_scrollbar.pack(side="right", fill="y")
        timeline_canvas.pack(side="left", fill="both", expand=True)

        # --- FINAL SETUP ---
        
        # Bind the date selection change to the refresh function
        tb_date.bind("<<DateSelected>>", lambda e: refresh_timeblocks())
        
        # Initial load of time blocks
        refresh_timeblocks()
        
    # COMMONPLACE BOOK PAGE
    if pn == "Commonplace":
        import tkinter as tk
        from tkinter import messagebox, ttk
        from datetime import datetime

        # --- Page Header ---
        tk.Label(
            content,
            text="📚 Commonplace Book",
            font=("Segoe UI", 14, "bold"),
            bg=theme()["CARD"],
            fg=theme()["TEXT"]
        ).pack(anchor="nw", pady=12, padx=12)

        # --- Input Section ---
        input_frame = tk.Frame(content, bg=theme()["CARD"])
        input_frame.pack(fill="x", padx=12, pady=(0, 8))

        tk.Label(input_frame, text="Content:", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=0, column=0, padx=4, pady=2)
        cp_content_entry = tk.Text(input_frame, width=45, height=4, bg="#ffe6ef", fg="#000")
        cp_content_entry.grid(row=0, column=1, columnspan=3, padx=4, pady=2)

        tk.Label(input_frame, text="Tags (comma-separated):", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=1, column=0, padx=4, pady=2)
        cp_tags_entry = tk.Entry(input_frame, bg="#ffe6ef", fg="#000", width=40)
        cp_tags_entry.grid(row=1, column=1, columnspan=3, padx=4, pady=2, sticky="w")

        # --- Scrollable Table ---
        canvas = tk.Canvas(content, bg=theme()["CARD"])
        scrollbar = tk.Scrollbar(content, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=theme()["CARD"])
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        headers = ["Preview", "Date", "Tags", "Actions"]
        header_frame = tk.Frame(scroll_frame, bg=theme()["CARD"])
        header_frame.pack(fill="x", pady=(0, 2))
        for h in headers:
            tk.Label(
                header_frame,
                text=h,
                bg=theme()["CARD"],
                fg=theme()["TEXT"],
                font=("Segoe UI", 10, "bold"),
                borderwidth=1,
                relief="solid",
                padx=4,
                pady=2
            ).pack(side="left", expand=True, fill="x")

        # --- Functions ---
        def refresh_commonplace_table():
            for widget in scroll_frame.winfo_children():
                if widget != header_frame:
                    widget.destroy()

            conn = db_connect()
            c = conn.cursor()
            rows = c.execute("SELECT id, date, content, preview, tags FROM commonplace ORDER BY id DESC").fetchall()
            conn.close()

            for row in rows:
                id_, date_, content, preview, tags = row

                r_frame = tk.Frame(scroll_frame, bg=theme()["CARD"])
                r_frame.pack(fill="x", pady=1)

                tk.Label(
                    r_frame,
                    text=preview,
                    bg=theme()["CARD"],
                    fg=theme()["TEXT"],
                    font=("Segoe UI", 10),
                    borderwidth=1,
                    relief="solid",
                    padx=4,
                    pady=2
                ).pack(side="left", expand=True, fill="x")

                tk.Label(
                    r_frame,
                    text=date_,
                    bg=theme()["CARD"],
                    fg=theme()["TEXT"],
                    font=("Segoe UI", 10),
                    borderwidth=1,
                    relief="solid",
                    padx=4,
                    pady=2
                ).pack(side="left", expand=True, fill="x")

                tk.Label(
                    r_frame,
                    text=tags,
                    bg=theme()["CARD"],
                    fg=theme()["TEXT"],
                    font=("Segoe UI", 10),
                    borderwidth=1,
                    relief="solid",
                    padx=4,
                    pady=2
                ).pack(side="left", expand=True, fill="x")

                btn_frame = tk.Frame(r_frame, bg=theme()["CARD"])
                btn_frame.pack(side="left", expand=True, fill="x")

                # --- Edit ---
                def edit_entry(item_id=id_, old_content=content, old_tags=tags):
                    edit_win = tk.Toplevel()
                    edit_win.title("Edit Entry")
                    edit_win.configure(bg="white")

                    tk.Label(edit_win, text="Content:").grid(row=0, column=0, padx=4, pady=2)
                    e_content = tk.Text(edit_win, width=50, height=6)
                    e_content.insert("1.0", old_content)
                    e_content.grid(row=0, column=1, padx=4, pady=2)

                    tk.Label(edit_win, text="Tags:").grid(row=1, column=0, padx=4, pady=2)
                    e_tags = tk.Entry(edit_win)
                    e_tags.insert(0, old_tags)
                    e_tags.grid(row=1, column=1, padx=4, pady=2)

                    def save_edit():
                        new_content = e_content.get("1.0", "end").strip()
                        new_tags = e_tags.get().strip()
                        new_preview = (new_content[:40] + "…") if len(new_content) > 40 else new_content

                        conn = db_connect()
                        c = conn.cursor()
                        c.execute("""
                            UPDATE commonplace 
                            SET content=?, preview=?, tags=? 
                            WHERE id=?
                        """, (new_content, new_preview, new_tags, item_id))
                        conn.commit()
                        conn.close()
                        edit_win.destroy()
                        refresh_commonplace_table()

                    tk.Button(edit_win, text="Save", bg="#ff5d8f", fg="white", command=save_edit).grid(
                        row=2, column=0, columnspan=2, pady=4
                    )

                # --- Delete ---
                def delete_entry(item_id=id_):
                    if messagebox.askyesno("Confirm Delete", "Delete this entry?"):
                        conn = db_connect()
                        c = conn.cursor()
                        c.execute("DELETE FROM commonplace WHERE id=?", (item_id,))
                        conn.commit()
                        conn.close()
                        refresh_commonplace_table()

                tk.Button(btn_frame, text="Edit", bg="#ff5d8f", fg="white", command=edit_entry, width=5).pack(side="left", padx=1)
                tk.Button(btn_frame, text="Del", bg="#ffb6c8", fg="white", command=delete_entry, width=5).pack(side="left", padx=1)

        # --- Add Button Function ---
        def add_commonplace():
            content = cp_content_entry.get("1.0", "end").strip()
            tags = cp_tags_entry.get().strip()
            if not content:
                messagebox.showwarning("Empty", "Content cannot be empty.")
                return

            preview_txt = (content[:40] + "…") if len(content) > 40 else content
            today = datetime.now().strftime("%Y-%m-%d")

            conn = db_connect()
            c = conn.cursor()
            c.execute("""
                INSERT INTO commonplace (date, content, preview, tags)
                VALUES (?, ?, ?, ?)
            """, (today, content, preview_txt, tags))
            conn.commit()
            conn.close()

            cp_content_entry.delete("1.0", "end")
            cp_tags_entry.delete(0, "end")
            refresh_commonplace_table()

        tk.Button(input_frame, text="Add", bg="#ff5d8f", fg="white", command=add_commonplace).grid(
            row=1, column=3, padx=4, pady=2
        )

        # --- Initial Refresh ---
        refresh_commonplace_table()
    # Focus Log
    if pn == "Focus Log":
        import tkinter as tk

        # Scrollable frame setup
        canvas = tk.Canvas(content, bg=theme()["CARD"], highlightthickness=0)
        scrollbar = tk.Scrollbar(content, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=theme()["CARD"])

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=(12,0), pady=6)
        scrollbar.pack(side="right", fill="y", padx=(0,12), pady=6)

        # Table headers
        headers = ["Date", "Duration (min)", "Purpose", "Success"]
        header_frame = tk.Frame(scroll_frame, bg="#ffe6ef", bd=0)
        header_frame.pack(fill="x", pady=(0,4))

        for h in headers:
            tk.Label(header_frame, text=h, bg="#ffe6ef", fg="#333",
                    font=("Segoe UI", 10, "bold"), padx=6, pady=4).pack(side="left", expand=True, fill="x")

        # Fetch data from DB
        conn = db_connect()
        c = conn.cursor()
        rows = c.execute("""
            SELECT focus_date, duration_minutes, purpose, success
            FROM focus_sessions_new
            ORDER BY created_at DESC
        """).fetchall()
        conn.close()

        # Populate rows with alternating colors
        row_colors = ["#ffffff", "#fff0f5"]
        for i, row in enumerate(rows):
            bg_color = row_colors[i % 2]
            r_frame = tk.Frame(scroll_frame, bg=theme()["BG"], bd=0)
            r_frame.pack(fill="x", pady=1)

            success_text = "✓" if row[3] else "✗"

            for val in [row[0], row[1], row[2], success_text]:
                tk.Label(r_frame, text=val, bg=theme()["BG"], fg="#333", 
                        font=("Segoe UI", 10), padx=6, pady=4).pack(side="left", expand=True, fill="x")

    # --- SONGWRITING PAGE ---
    if pn == "Songwriting":
        global song_title_entry, song_mood_entry, song_genre_entry, song_lyrics_text, song_listbox

        # 🩷 PAGE BACKGROUND
        content.config(bg=theme()["BG"])

        # --- Layout Frame ---
        main_frame = tk.Frame(content, bg=theme()["BG"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Two columns: Left (drafts) and Right (editor)
        left_frame = tk.Frame(main_frame, bg=theme()["BG"])
        right_frame = tk.Frame(main_frame, bg=theme()["BG"])
        left_frame.pack(side="left", fill="y", padx=(0, 10), pady=5)
        right_frame.pack(side="left", fill="both", expand=True, pady=5)

        # --- LEFT COLUMN: Saved Drafts ---
        tk.Label(left_frame, text="Saved Drafts", font=("Segoe UI", 12, "bold"),
                bg=theme()["BG"], fg=theme()["TEXT"]).pack(anchor="w", pady=(0, 5))

        drafts_frame = tk.Frame(left_frame, bg=theme()["BG"])
        drafts_frame.pack(fill="both", expand=True)

        song_list_scrollbar = tk.Scrollbar(drafts_frame)
        song_list_scrollbar.pack(side="right", fill="y")

        song_listbox = tk.Listbox(
            drafts_frame,
            font=("Segoe UI", 10),
            bg="white",
            fg="black",
            selectbackground=theme()["ACCENT"],
            selectforeground="black",
            yscrollcommand=song_list_scrollbar.set,
            height=20,
        )
        song_listbox.pack(side="left", fill="both", expand=True)
        song_list_scrollbar.config(command=song_listbox.yview)

        # --- RIGHT COLUMN: Song Editor ---
        tk.Label(right_frame, text="Song Details", font=("Segoe UI", 12, "bold"),
                bg=theme()["BG"], fg=theme()["TEXT"]).pack(anchor="w", pady=(0, 5))

        form_frame = tk.Frame(right_frame, bg=theme()["BG"])
        form_frame.pack(fill="x", pady=(0, 10))

        # Title
        tk.Label(form_frame, text="Title:", bg=theme()["BG"], fg=theme()["TEXT"]).grid(row=0, column=0, sticky="w")
        song_title_entry = tk.Entry(form_frame, bg=theme()["ACCENT"], fg="black", insertbackground="white",
                                    font=("Segoe UI", 10), width=40)
        song_title_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        # Mood
        tk.Label(form_frame, text="Mood:", bg=theme()["BG"], fg=theme()["TEXT"]).grid(row=1, column=0, sticky="w")
        song_mood_entry = tk.Entry(form_frame, bg=theme()["ACCENT"], fg="black", insertbackground="white",
                                font=("Segoe UI", 10), width=40)
        song_mood_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # Genre
        tk.Label(form_frame, text="Genre:", bg=theme()["BG"], fg=theme()["TEXT"]).grid(row=2, column=0, sticky="w")
        song_genre_entry = tk.Entry(form_frame, bg=theme()["ACCENT"], fg="black", insertbackground="white",
                                    font=("Segoe UI", 10), width=40)
        song_genre_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        # Lyrics
        tk.Label(right_frame, text="Lyrics:", bg=theme()["BG"], fg=theme()["TEXT"]).pack(anchor="w", pady=(5, 0))
        lyrics_frame = tk.Frame(right_frame, bg=theme()["BG"])
        lyrics_frame.pack(fill="both", expand=True, pady=(0, 10))

        lyrics_scrollbar = tk.Scrollbar(lyrics_frame)
        lyrics_scrollbar.pack(side="right", fill="y")

        song_lyrics_text = tk.Text(lyrics_frame, wrap="word", font=("Segoe UI", 10),
                                bg=theme()["ACCENT"], fg="black", insertbackground="white",
                                yscrollcommand=lyrics_scrollbar.set)
        song_lyrics_text.pack(side="left", fill="both", expand=True)
        lyrics_scrollbar.config(command=song_lyrics_text.yview)

        # --- Save and Load Logic ---
        def save_song():
            title = song_title_entry.get().strip()
            mood = song_mood_entry.get().strip()
            genre = song_genre_entry.get().strip()
            lyrics = song_lyrics_text.get("1.0", tk.END).strip()

            if not title:
                messagebox.showwarning("Missing Title", "Please enter a song title.")
                return

            conn = db_connect()
            c = conn.cursor()
            c.execute("""
                INSERT OR REPLACE INTO song_drafts (title, lyrics, mood, genre)
                VALUES (?, ?, ?, ?)
            """, (title, lyrics, mood, genre))
            conn.commit()
            conn.close()

            load_song_drafts()
            messagebox.showinfo("Saved", f"'{title}' has been saved!")

        def load_song_drafts():
            song_listbox.delete(0, tk.END)
            conn = db_connect()
            c = conn.cursor()
            for row in c.execute("SELECT title FROM song_drafts ORDER BY created_at DESC"):
                song_listbox.insert(tk.END, row[0])
            conn.close()

        def load_selected_song(event):
            selected = song_listbox.get(tk.ACTIVE)
            if not selected:
                return
            conn = db_connect()
            c = conn.cursor()
            c.execute("SELECT title, lyrics, mood, genre FROM song_drafts WHERE title=?", (selected,))
            row = c.fetchone()
            conn.close()
            if row:
                song_title_entry.delete(0, tk.END)
                song_title_entry.insert(0, row[0])
                song_lyrics_text.delete("1.0", tk.END)
                song_lyrics_text.insert("1.0", row[1] or "")
                song_mood_entry.delete(0, tk.END)
                song_mood_entry.insert(0, row[2] or "")
                song_genre_entry.delete(0, tk.END)
                song_genre_entry.insert(0, row[3] or "")

        song_listbox.bind("<<ListboxSelect>>", load_selected_song)

        # --- Save Button ---
        tk.Button(right_frame, text="Save Song", command=save_song,
                bg=theme()["ACCENT"], fg="white",
                font=("Segoe UI", 11, "bold"), padx=10, pady=5).pack(anchor="e", pady=(5, 10))

        # Load all songs on open
        load_song_drafts()

    # JOURNAL PAGE
    if pn == "Journal":

        # --- HELPER FUNCTIONS FOR JOURNAL ---

        def load_entry_for_date():
            """Load the journal entry for the selected date into the editor."""
            selected_date_str = date_entry.get_date().isoformat()

            txt.delete("1.0", "end")

            conn = db_connect()
            c = conn.cursor()
            row = c.execute("SELECT entry FROM journal WHERE date = ?", (selected_date_str,)).fetchone()
            conn.close()

            if row:
                txt.insert("1.0", row[0])

        def load_journal_history():
            """Loads and displays the last 20 journal entries."""
            if "journal_history_list" in special_widgets:
                history_list = special_widgets["journal_history_list"]
                history_list.config(state="normal")
                history_list.delete("1.0", "end")

                conn = db_connect()
                c = conn.cursor()
                rows = c.execute(
                    "SELECT date, entry FROM journal ORDER BY date DESC, id DESC LIMIT 20"
                ).fetchall()
                conn.close()

                for d, e in rows:
                    history_list.insert("end", f"**{d}**\n{e}\n\n")

                history_list.config(state="disabled")

        def save_journal():
            selected_date_str = date_entry.get_date().isoformat()
            entry_text = txt.get("1.0", "end").strip()

            if not entry_text:
                messagebox.showwarning("Empty", "Write something first.")
                return

            conn = db_connect()
            c = conn.cursor()

            # Check if entry for the date exists
            c.execute("SELECT id FROM journal WHERE date = ?", (selected_date_str,))
            existing_id = c.fetchone()

            if existing_id:
                # Ask user if they want to overwrite
                if messagebox.askyesno(
                    "Entry Exists",
                    f"An entry for {selected_date_str} exists. Overwrite?"
                ):
                    c.execute(
                        "UPDATE journal SET entry = ? WHERE id = ?",
                        (entry_text, existing_id[0])
                    )
                    messagebox.showinfo("Updated", f"Updated entry for {selected_date_str}")
                else:
                    conn.close()
                    return
            else:
                # Insert new
                c.execute(
                    "INSERT INTO journal (date, entry) VALUES (?, ?)",
                    (selected_date_str, entry_text)
                )
                messagebox.showinfo("Saved", f"Saved entry for {selected_date_str}")

            conn.commit()
            conn.close()

            load_journal_history()

        # --- UI ELEMENTS FOR JOURNAL PAGE ---

        # Date Picker Section
        date_frame = tk.Frame(content, bg=theme()["CARD"])
        date_frame.pack(anchor="nw", padx=6, pady=(6, 0))

        tk.Label(date_frame, text="Entry Date:", bg=theme()["CARD"], fg=theme()["TEXT"]).pack(side="left", padx=(0, 6))

        date_entry = DateEntry(
            date_frame, width=12,
            background='darkblue', foreground='white', borderwidth=2,
            date_pattern='yyyy-mm-dd', locale='en_US',
            selectmode='day', showweeknumbers=False
        )
        date_entry.set_date(date.today())
        date_entry.pack(side="left")

        # ⬇️ ADD THIS — loads past entries when user selects a date
        def on_date_change(event):
            load_entry_for_date()
        date_entry.bind("<<DateEntrySelected>>", on_date_change)

        # Journal Editor Section
        tk.Label(content, text="Journal Editor:", bg=theme()["CARD"], fg=theme()["TEXT"]).pack(anchor="nw", padx=6, pady=(6, 0))

        txt = tk.Text(content, height=12, wrap="word")
        txt.pack(fill="both", expand=True, padx=6, pady=6)
        special_widgets["journal_txt"] = txt

        tk.Button(content, text="Save/Update Entry", command=save_journal).pack(anchor="e", padx=6, pady=6)

        # Journal History Section
        tk.Label(content, text="Journal History:", bg=theme()["CARD"], fg=theme()["TEXT"]).pack(anchor="nw", padx=6, pady=(6, 2))

        history_frame = tk.Frame(content, bg=theme()["CARD"])
        history_frame.pack(fill="both", expand=True, padx=6, pady=6)

        history_list = tk.Text(history_frame, height=8, wrap="word", state="disabled")
        history_list.pack(fill="both", expand=True)
        special_widgets["journal_history_list"] = history_list

        # Initial load
        load_entry_for_date()
        load_journal_history()
        
    # TO DO PAGE 
    if pn == "To-Do":
        
        # ------------------- To-Do Logic -------------------
        # Container for new task entry
        entry_frame = tk.Frame(content, bg=theme()["CARD"])
        entry_frame.pack(fill="x", padx=6, pady=(6,0))
        
        tk.Label(entry_frame, text="Add a task:", bg=theme()["CARD"], fg=theme()["TEXT"]).pack(side="left", padx=(0, 6))
        
        task_entry = tk.Entry(entry_frame)
        task_entry.pack(side="left", fill="x", expand=True, padx=6)
        
        # Container for displaying tasks
        task_list_frame = tk.Frame(content, bg=theme()["SIDEBAR"])
        task_list_frame.pack(fill="both", expand=True, padx=6, pady=6)
        special_widgets["task_list_frame"] = task_list_frame

        # --- Task Functions ---
        def delete_task(task_id):
            """Deletes a task permanently from the database."""
            if messagebox.askyesno("Delete Task", "Are you sure you want to permanently delete this task?"):
                conn = db_connect()
                c = conn.cursor()
                c.execute("DELETE FROM todos WHERE id = ?", (task_id,))
                conn.commit()
                conn.close()
                pg.load_tasks()
                update_dashboard_ui()  # Update dashboard stats
            
        def toggle_task_completion(task_id, completed_var):
            """Toggle task completion status."""
            new_state = completed_var.get()
            conn = db_connect()
            c = conn.cursor()
            c.execute("UPDATE todos SET completed = ? WHERE id = ?", (new_state, task_id))
            conn.commit()
            conn.close()
            pg.load_tasks()
            update_dashboard_ui()  # Update dashboard stats

        def load_tasks():
            """Load tasks from the database and display them in the UI."""
            today_iso = date.today().isoformat()
            
            # Clear previous widgets
            for widget in task_list_frame.winfo_children():
                widget.destroy()
                
            t = theme()
            conn = db_connect()
            c = conn.cursor()
            
            sql_query = """
            SELECT id, task, completed 
            FROM todos 
            WHERE created_date = ? OR (completed = 0 AND created_date < ?)
            ORDER BY completed ASC, created_date ASC, id DESC
            """
            
            rows = c.execute(sql_query, (today_iso, today_iso)).fetchall()
            conn.close()

            for task_id, task_text, completed in rows:
                task_row = tk.Frame(task_list_frame, bg=t["SIDEBAR"])
                task_row.pack(fill="x", pady=2, padx=4)

                completed_var = tk.IntVar(value=completed)
                
                check = tk.Checkbutton(
                    task_row, 
                    variable=completed_var, 
                    text=task_text, 
                    font=TEXT_FONT, 
                    anchor="w",
                    bg=t["SIDEBAR"], fg=t["TEXT"], 
                    activebackground=t["SIDEBAR"],
                    selectcolor=t["SIDEBAR"],
                    command=lambda tid=task_id, cv=completed_var: toggle_task_completion(tid, cv)
                )
                
                # Apply strikethrough if completed
                if completed:
                    check.config(fg="gray", font=(TEXT_FONT[0], TEXT_FONT[1], "overstrike"))

                check.pack(side="left", fill="x", expand=True)

                delete_btn = tk.Button(
                    task_row, 
                    text="✖", 
                    command=lambda tid=task_id: delete_task(tid),
                    relief="flat", bd=0, bg=t["SIDEBAR"], fg="red"
                )
                delete_btn.pack(side="right", padx=5)

        def add_task():
            """Add a new task to the database."""
            task = task_entry.get().strip()
            if not task:
                messagebox.showwarning("Empty Task", "Please enter a task before adding.")
                return

            conn = db_connect()
            c = conn.cursor()
            today_iso = date.today().isoformat()
            c.execute("INSERT INTO todos (task, completed, created_date) VALUES (?, ?, ?)", (task, 0, today_iso))
            conn.commit()
            conn.close()
            
            task_entry.delete(0, "end")
            pg.load_tasks()
            update_dashboard_ui()  # Update dashboard stats

        # Add button
        tk.Button(entry_frame, text="Add", command=add_task).pack(side="right", padx=6)

        # Attach functions to the page object for external calls
        pg.load_tasks = load_tasks
        pg.delete_task = delete_task
        
        # Initial load of tasks
        pg.load_tasks()
        
    # WATER TRACKER PAGE
    if pn == "Water":
        # --- imports used only on this page (safe to re-import) ---
        from datetime import datetime, date
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        WATER_GOAL = 8  # cups per day
        current_cups = tk.IntVar(value=0)

        # --- UI Containers ---
        chart_frame = tk.Frame(content, bg=theme()["CARD"])
        raw_history_list = tk.Text(
            content, height=4, wrap="word", state="disabled",
            bg=theme()["BG"], fg=theme()["TEXT"]
        )

        # --- DATABASE HELPERS ---
        def load_water_data(limit=30):
            """Fetch last `limit` days of water intake (oldest -> newest)."""
            conn = db_connect()
            c = conn.cursor()
            try:
                rows = c.execute(
                    "SELECT date, cups FROM water ORDER BY date DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            except Exception as e:
                print("DB error (load_water_data):", e)
                rows = []
            finally:
                conn.close()

            # rows currently newest -> oldest, reverse to oldest -> newest for plotting
            rows.reverse()
            return rows

        def save_water_count(cups, target_date):
            """Insert or update the given date's water count, then refresh UI."""
            if not isinstance(target_date, date):
                # defensive: if a datetime passed, convert
                try:
                    target_date = target_date.date()
                except:
                    target_date = date.today()

            selected_date = target_date.isoformat()
            conn = db_connect()
            c = conn.cursor()
            try:
                c.execute("SELECT id FROM water WHERE date = ?", (selected_date,))
                existing = c.fetchone()
                if existing:
                    c.execute("UPDATE water SET cups = ? WHERE id = ?", (cups, existing[0]))
                else:
                    c.execute("INSERT INTO water (date, cups) VALUES (?, ?)", (selected_date, cups))
                conn.commit()
            except Exception as e:
                print("DB error (save_water_count):", e)
                messagebox.showerror("Database Error", f"Could not save water data:\n{e}")
            finally:
                conn.close()

            # Refresh UI for the currently-selected date
            refresh_water_ui(selected_date=selected_date)

        # --- DISPLAY HELPERS ---
        def display_raw_history(rows):
            """Display recent water entries as text (newest first)."""
            raw_history_list.config(state="normal")
            raw_history_list.delete("1.0", "end")

            if not rows:
                raw_history_list.insert("end", "No recent entries yet.\n")
            else:
                # rows is oldest->newest, show newest first and cap emoji length
                recent = rows[-8:]
                recent.reverse()
                for d, cups in recent:
                    cups_int = int(cups) if cups is not None else 0
                    cups_int = max(0, min(cups_int, 10))  # keep emoji string reasonable
                    raw_history_list.insert("end", f"📅 {d}: {'🥤' * cups_int}\n")

            raw_history_list.config(state="disabled")

        def plot_water_history_chart():
            """Plot the last 30 days of water intake."""
            rows = load_water_data()

            # Clear previous chart
            for widget in chart_frame.winfo_children():
                widget.destroy()

            # If empty, show message and history, then return
            if not rows:
                tk.Label(
                    chart_frame, text="No water data yet!",
                    bg=theme()["CARD"], fg=theme()["TEXT"]
                ).pack(pady=20)
                display_raw_history(rows)
                return

            # Prepare chart data
            try:
                dates = [datetime.strptime(r[0], "%Y-%m-%d") for r in rows]
            except Exception as e:
                # Fallback: ignore invalid-format rows
                dates = []
                for r in rows:
                    try:
                        dates.append(datetime.strptime(r[0], "%Y-%m-%d"))
                    except:
                        continue

            cups = [int(r[1] or 0) for r in rows]
            if not dates:
                tk.Label(chart_frame, text="Invalid date data for chart.", bg=theme()["CARD"], fg=theme()["TEXT"]).pack(pady=10)
                display_raw_history(rows)
                return

            goal_line = [WATER_GOAL] * len(dates)

            fig, ax = plt.subplots(figsize=(6, 3), facecolor=theme()["CARD"])
            ax.plot(dates, cups, marker='o', linestyle='-', color=theme()["ACCENT"], label="Water Intake")
            ax.plot(dates, goal_line, linestyle='--', color=theme()["TEXT"], label=f"Goal ({WATER_GOAL} cups)")

            ax.set_title('Water Intake (Last 30 Days)', fontsize=10, color=theme()["TEXT"])
            ax.set_ylabel('Cups', fontsize=8, color=theme()["TEXT"])
            # y-limit: at least goal + 1
            ymax = max(max(cups) + 1, WATER_GOAL + 1)
            ax.set_ylim(0, ymax)
            ax.set_facecolor(theme()["CARD"])
            ax.tick_params(axis='x', colors=theme()["TEXT"], labelsize=7)
            ax.tick_params(axis='y', colors=theme()["TEXT"], labelsize=8)
            ax.legend(fontsize=7, loc='upper left', frameon=False)
            fig.autofmt_xdate(rotation=45)

            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            display_raw_history(rows)

        # --- CORE UI REFRESH ---
        def refresh_water_ui(selected_date=None):
            """Refresh chart and history; if selected_date provided, also load its count."""
            plot_water_history_chart()
            # if caller passed a selected_date string (ISO), load it into the date picker and count
            try:
                if selected_date:
                    # ensure date_entry shows this date
                    try:
                        parsed = datetime.strptime(selected_date, "%Y-%m-%d").date()
                        date_entry.set_date(parsed)
                        load_water_count(parsed)
                    except:
                        pass
            except Exception:
                pass

        def load_water_count(target_date):
            """Load cups for the given target_date (datetime.date) and update UI."""
            if not isinstance(target_date, date):
                try:
                    target_date = target_date.date()
                except:
                    target_date = date.today()

            selected_date = target_date.isoformat()
            conn = db_connect()
            c = conn.cursor()
            try:
                c.execute("SELECT cups FROM water WHERE date = ?", (selected_date,))
                result = c.fetchone()
            except Exception as e:
                print("DB error (load_water_count):", e)
                result = None
            finally:
                conn.close()

            current_cups.set(result[0] if result else 0)
            # only refresh the chart/history area (doesn't change selected date)
            plot_water_history_chart()

        def load_water_count_today():
            load_water_count(date.today())

        # --- BUTTON ACTIONS ---
        def increment_water():
            d = date_entry.get_date()
            new_val = current_cups.get() + 1
            current_cups.set(new_val)
            save_water_count(new_val, d)

        def decrement_water():
            if current_cups.get() > 0:
                d = date_entry.get_date()
                new_val = current_cups.get() - 1
                current_cups.set(new_val)
                save_water_count(new_val, d)

        # --- UI LAYOUT ---
        date_frame = tk.Frame(content, bg=theme()["CARD"])
        date_frame.pack(anchor="nw", padx=6, pady=(6, 0))
        tk.Label(date_frame, text="Select Date:", bg=theme()["CARD"], fg=theme()["TEXT"]).pack(side="left", padx=(0, 6))

        date_entry = DateEntry(
            date_frame, width=12, background='darkblue',
            foreground='white', borderwidth=2,
            date_pattern='yyyy-mm-dd', locale='en_US', selectmode='day',
            showweeknumbers=False
        )
        date_entry.set_date(date.today())
        # When user selects a date, load that date's count — increment/decrement will now affect that date
        date_entry.bind("<<DateSelected>>", lambda e: load_water_count(date_entry.get_date()))
        date_entry.pack(side="left")

        count_frame = tk.Frame(content, bg=theme()["CARD"])
        count_frame.pack(anchor="nw", padx=6, pady=(20, 10))

        tk.Button(count_frame, text="➖", font=("Segoe UI", 10, "bold"),
                command=decrement_water, bg=theme()["ACCENT"], fg=theme()["BG"],
                relief="flat", padx=10, pady=5).pack(side="left", padx=10)

        tk.Label(count_frame, textvariable=current_cups,
                font=("Segoe UI", 48, "bold"),
                bg=theme()["CARD"], fg=theme()["TEXT"]).pack(side="left")

        tk.Label(count_frame, text="cups",
                font=("Segoe UI", 16),
                bg=theme()["CARD"], fg=theme()["TEXT"]).pack(side="left", padx=10)

        tk.Button(count_frame, text="➕", font=("Segoe UI", 10, "bold"),
                command=increment_water, bg=theme()["ACCENT"], fg=theme()["BG"],
                relief="flat", padx=10, pady=5).pack(side="left", padx=10)

        # --- Chart + History ---
        tk.Label(content, text="30-Day Water Trend:", bg=theme()["CARD"], fg=theme()["TEXT"],
                font=("Segoe UI", 11, "bold")).pack(anchor="nw", padx=6, pady=(20, 2))
        chart_frame.pack(fill="x", padx=6, pady=6)

        tk.Label(content, text="Recent Entries:", bg=theme()["CARD"], fg=theme()["TEXT"],
                font=("Segoe UI", 11, "bold")).pack(anchor="nw", padx=6, pady=(10, 2))
        raw_history_list.pack(fill="x", padx=6)

        # --- PAGE LINKED REFRESH HANDLERS (exposed to the main app) ---
        pg.load_water_count_today = load_water_count_today

        def water_update_ui():
            load_water_count_today()

        pg.update_ui = water_update_ui
        pg.update_ui()
    
    # --- MEDIA LOG --- 
    from datetime import date # Assuming you have this import at the top of your main script
    import tkinter as tk
    from tkinter import ttk, messagebox

    if pn == "MediaLog":
        # Clear previous page
        for widget in pg.winfo_children():
            widget.destroy()

        t = theme()

        # --- MAIN CONTAINER SETUP: NOTEBOOK (TABBED INTERFACE) ---
        tk.Label(pg, text="📚🎬📺 Media Consumption Log", font=("Segoe UI", 18, "bold"), bg=t["BG"], fg=t["TEXT"]).pack(pady=10)
        
        # Create the Notebook (Tab Widget)
        media_notebook = ttk.Notebook(pg)
        media_notebook.pack(pady=5, padx=10, expand=True, fill="both")

        # --- 1. MOVIES TAB (Reusing Movies Page Code) ---
        movies_tab = tk.Frame(media_notebook, bg=t["BG"])
        media_notebook.add(movies_tab, text="🍿 Movies")
        
        # --- GLOBAL VARIABLES (Movies Specific) ---
        # NOTE: Using 'global' inside a function is discouraged. If these are only accessed 
        # inside this 'if pn' block, defining them at the top of this block is better.
        # Since your original code uses 'global', I will respect that structure here.
        global movie_title_entry, year_entry, runtime_entry, movie_status_combo, movie_rating_combo, movie_genre_entry, date_watched_entry
        global watchlist_frame, movie_history_frame
        
        # New global IDs for the canvas windows (required for the fix)
        global watchlist_window_id, history_window_id 
        
        MOVIE_STATUSES = ['Watchlist', 'Watched']
        MOVIE_RATINGS = ['1 Star', '2 Stars', '3 Stars', '4 Stars', '5 Stars']

        # --- FUNCTIONS (Movies) ---

        # NOTE: The add_movie, delete_movie, mark_as_watched functions remain unchanged as they are not the source of the scrolling error.

        def add_movie():
            """Add or update a movie in the database."""
            title = movie_title_entry.get().strip()
            year = year_entry.get().strip()
            runtime_str = runtime_entry.get().strip()
            status = movie_status_combo.get()
            genre = movie_genre_entry.get().strip()
            rating_str = movie_rating_combo.get()
            date_watched = date_watched_entry.get().strip()

            if not title or not status:
                messagebox.showwarning("Missing Data", "Title and Status are required.")
                return

            try:
                release_year = int(year) if year.isdigit() else None
                runtime = int(runtime_str) if runtime_str.isdigit() else None
                rating = int(rating_str.split()[0]) if rating_str and status == 'Watched' else None

                if status == 'Watched' and (not date_watched or date_watched == "YYYY-MM-DD"):
                    date_watched = date.today().isoformat()

                run_query("""
                    INSERT INTO movies (title, release_year, runtime, status, genre, rating, date_watched)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (title, release_year, runtime, status, genre, rating, date_watched))

                # Clear title and reset form
                movie_title_entry.delete(0, tk.END)
                year_entry.delete(0, tk.END)
                runtime_entry.delete(0, tk.END)
                movie_genre_entry.delete(0, tk.END)
                movie_status_combo.current(0)
                movie_rating_combo.set('')
                date_watched_entry.delete(0, tk.END)
                date_watched_entry.insert(0, "YYYY-MM-DD")

                load_watchlist()
                load_history()

            except ValueError:
                messagebox.showerror("Input Error", "Year and Runtime must be whole numbers.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add movie: {e}")

        def delete_movie(movie_id):
            """Delete a movie from Watchlist or History."""
            if messagebox.askyesno("Delete Movie", "Are you sure you want to remove this movie permanently?"):
                try:
                    run_query("DELETE FROM movies WHERE id = ?", (movie_id,))
                    load_watchlist()
                    load_history()
                except Exception as e:
                    messagebox.showerror("Error", f"Could not delete movie: {e}")

        def mark_as_watched(movie_id):
            """Mark a movie as watched and prompt for genre/rating."""
            row = run_query("SELECT title, genre, rating FROM movies WHERE id = ?", (movie_id,))
            if not row:
                messagebox.showerror("Error", "Movie not found.")
                return

            title, genre, rating = row[0]

            # Popup for updating genre and rating
            popup = tk.Toplevel(pg)
            popup.title(f"Mark '{title}' as Watched")
            popup.geometry("300x150")
            popup.grab_set()

            tk.Label(popup, text="Genre:").grid(row=0, column=0, padx=10, pady=10)
            genre_entry = tk.Entry(popup)
            genre_entry.insert(0, genre or "")
            genre_entry.grid(row=0, column=1, padx=10, pady=10)

            tk.Label(popup, text="Rating (1-5):").grid(row=1, column=0, padx=10, pady=10)
            rating_combo = ttk.Combobox(popup, values=['1', '2', '3', '4', '5'], state="readonly", width=5)
            rating_combo.set(str(rating) if rating else '')
            rating_combo.grid(row=1, column=1, padx=10, pady=10)

            def confirm():
                new_genre = genre_entry.get().strip()
                new_rating_str = rating_combo.get()
                new_rating = int(new_rating_str) if new_rating_str else None

                run_query("""
                    UPDATE movies
                    SET status = ?, genre = ?, rating = ?, date_watched = ?
                    WHERE id = ?
                """, ('Watched', new_genre, new_rating, date.today().isoformat(), movie_id))

                popup.destroy()
                load_watchlist()
                load_history()
                messagebox.showinfo("Updated", f"'{title}' marked as Watched!")

            tk.Button(popup, text="Confirm", command=confirm, bg=t["ACCENT"], fg="white").grid(row=2, column=0, columnspan=2, pady=10)

        def load_watchlist():
            """Load all movies with status 'Watchlist'."""
            for widget in watchlist_frame.winfo_children():
                widget.destroy()

            rows = run_query("SELECT id, title, release_year, runtime FROM movies WHERE status = 'Watchlist' ORDER BY title ASC")
            if not rows:
                tk.Label(watchlist_frame, text="Your Watchlist is empty! 🍿", bg=t["CARD"], fg=t["TEXT"]).pack(pady=20)
                # Need to update scroll region even if empty to ensure the canvas recognizes the size change
                watchlist_frame.update_idletasks()
                watchlist_canvas.configure(scrollregion=watchlist_canvas.bbox("all"))
                return

            for movie_id, title, release_year, runtime in rows:
                movie_row = tk.Frame(watchlist_frame, bg=t["CARD"], bd=1, relief="solid")
                movie_row.pack(fill="x", pady=5, padx=5)

                title_text = f"🎬 {title} ({release_year or 'N/A'})"
                tk.Label(movie_row, text=title_text, font=("Segoe UI", 10, "bold"), bg=t["CARD"], fg=t["TEXT"]).pack(side="left", anchor="w", padx=5, pady=2)

                if runtime:
                    tk.Label(movie_row, text=f"({runtime} min)", font=("Segoe UI", 9), bg=t["CARD"], fg="gray").pack(side="left", padx=5)

                tk.Button(movie_row, text="Mark as Watched", command=lambda mid=movie_id: mark_as_watched(mid),
                          bg=t["ACCENT"], fg="white", relief="flat").pack(side="right", padx=5)

                tk.Button(movie_row, text="✖", command=lambda mid=movie_id: delete_movie(mid),
                          bg=t["CARD"], fg="red").pack(side="right")
                          
            # FIX: Ensure scroll region is updated after content loads.
            watchlist_frame.update_idletasks()
            watchlist_canvas.configure(scrollregion=watchlist_canvas.bbox("all"))


        def load_history():
            """Load all movies with status 'Watched'."""
            for widget in movie_history_frame.winfo_children():
                widget.destroy()

            rows = run_query("""
                SELECT id, title, release_year, genre, rating, date_watched
                FROM movies
                WHERE status = 'Watched'
                ORDER BY date_watched DESC, id DESC
            """)
            if not rows:
                tk.Label(movie_history_frame, text="No movies watched yet! 🍿", bg=t["CARD"], fg=t["TEXT"]).pack(pady=20)
                # Update scroll region even if empty
                movie_history_frame.update_idletasks()
                history_canvas.configure(scrollregion=history_canvas.bbox("all"))
                return

            for movie_id, title, release_year, genre, rating, date_watched in rows:
                movie_row = tk.Frame(movie_history_frame, bg=t["CARD"], bd=1, relief="solid")
                movie_row.pack(fill="x", pady=5, padx=5)

                movie_row.grid_columnconfigure(0, weight=1)

                title_text = f"🎬 {title} ({release_year or 'N/A'})"
                tk.Label(movie_row, text=title_text, font=("Segoe UI", 10, "bold"),
                          bg=t["CARD"], fg=t["TEXT"]).grid(row=0, column=0, sticky="w", padx=5)

                star_rating = "★" * (rating or 0) + "☆" * (5 - (rating or 0))
                tk.Label(movie_row, text=star_rating, font=("Segoe UI", 12),
                          bg=t["CARD"], fg="gold").grid(row=0, column=1, padx=10, sticky="e")

                details_text = f"Genre: {genre or 'N/A'} | Watched: {date_watched or 'N/A'}"
                tk.Label(movie_row, text=details_text, font=("Segoe UI", 9),
                          bg=t["CARD"], fg=t["ACCENT"]).grid(row=1, column=0, sticky="w", padx=5)

                tk.Button(movie_row, text="✖", command=lambda mid=movie_id: delete_movie(mid),
                          relief="flat", bd=0, bg=t["CARD"], fg="red").grid(row=0, column=2, rowspan=2, padx=5, sticky="e")

                movie_row.grid_columnconfigure(1, weight=0)
                movie_row.grid_columnconfigure(2, weight=0)
                
            # FIX: Ensure scroll region is updated after content loads.
            movie_history_frame.update_idletasks()
            history_canvas.configure(scrollregion=history_canvas.bbox("all"))


        # --- UI LAYOUT (Movies Tab) ---
        tk.Label(movies_tab, text="Add New Movie Entry", font=("Segoe UI", 14, "bold"), bg=t["BG"], fg=t["TEXT"]).pack(pady=(10, 5))

        # Input frame
        input_frame = tk.Frame(movies_tab, bg=t["CARD"], padx=10, pady=10)
        input_frame.pack(fill="x", padx=10, pady=(0, 15))
        r = 0

        tk.Label(input_frame, text="Title:", bg=t["CARD"]).grid(row=r, column=0, sticky="w", padx=5)
        movie_title_entry = tk.Entry(input_frame)
        movie_title_entry.grid(row=r, column=1, sticky="ew", padx=5)

        tk.Label(input_frame, text="Year:", bg=t["CARD"]).grid(row=r, column=2, sticky="w", padx=5)
        year_entry = tk.Entry(input_frame, width=8)
        year_entry.grid(row=r, column=3, sticky="w", padx=5)

        tk.Label(input_frame, text="Runtime (min):", bg=t["CARD"]).grid(row=r, column=4, sticky="w", padx=5)
        runtime_entry = tk.Entry(input_frame, width=8)
        runtime_entry.grid(row=r, column=5, sticky="w", padx=5)
        r += 1

        tk.Label(input_frame, text="Genre:", bg=t["CARD"]).grid(row=r, column=0, sticky="w", padx=5, pady=5)
        movie_genre_entry = tk.Entry(input_frame)
        movie_genre_entry.grid(row=r, column=1, sticky="ew", padx=5, pady=5)

        tk.Label(input_frame, text="Status:", bg=t["CARD"]).grid(row=r, column=2, sticky="w", padx=5)
        movie_status_combo = ttk.Combobox(input_frame, values=MOVIE_STATUSES, state="readonly", width=10)
        movie_status_combo.current(0)
        movie_status_combo.grid(row=r, column=3, sticky="w", padx=5)

        tk.Label(input_frame, text="Rating (1-5):", bg=t["CARD"]).grid(row=r, column=4, sticky="w", padx=5)
        movie_rating_combo = ttk.Combobox(input_frame, values=MOVIE_RATINGS, state="readonly", width=8)
        movie_rating_combo.grid(row=r, column=5, sticky="w", padx=5)
        r += 1

        tk.Label(input_frame, text="Date Watched:", bg=t["CARD"]).grid(row=r, column=0, sticky="w", padx=5)
        date_watched_entry = tk.Entry(input_frame, width=15)
        date_watched_entry.insert(0, "YYYY-MM-DD")
        date_watched_entry.grid(row=r, column=1, sticky="w", padx=5, pady=5)

        tk.Button(input_frame, text="Add/Update Movie", command=add_movie,
                  bg=t["ACCENT"], fg="white").grid(row=r, column=5, padx=10, sticky="e")

        input_frame.grid_columnconfigure(1, weight=1)

        # Main content frames (Watchlist/History)
        main_content_frame = tk.Frame(movies_tab, bg=t["BG"])
        main_content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # ----------------------------------------------------
        # WATCHLIST SCROLLING FIX
        # ----------------------------------------------------
        watchlist_container = tk.Frame(main_content_frame, bg=t["CARD"], padx=10, pady=10)
        watchlist_container.pack(side="left", fill="both", expand=True, padx=(0,5))
        tk.Label(watchlist_container, text="🌟 Movie Watchlist", font=("Segoe UI", 12, "bold"), bg=t["CARD"]).pack(pady=5)

        watchlist_canvas = tk.Canvas(watchlist_container, bg=t["CARD"])
        watchlist_canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar_w = ttk.Scrollbar(watchlist_container, orient="vertical", command=watchlist_canvas.yview)
        v_scrollbar_w.pack(side="right", fill="y")
        watchlist_canvas.configure(yscrollcommand=v_scrollbar_w.set)
        
        watchlist_frame = tk.Frame(watchlist_canvas, bg=t["CARD"])
        
        # FIX 1: Remove width=1, rely on the binding below. 
        # We must capture the ID globally as it's used in the binding lambda.
        watchlist_window_id = watchlist_canvas.create_window((0,0), window=watchlist_frame, anchor="nw")
        
        # FIX 2: On canvas resize, update the inner frame's width using the stored ID.
        watchlist_canvas.bind('<Configure>', 
            lambda e: watchlist_canvas.itemconfig(watchlist_window_id, width=e.width))

        # FIX 3: Bind the frame's configure event to update the scroll region 
        # (The content will update the scroll region automatically when loaded via load_watchlist())
        watchlist_frame.bind("<Configure>", lambda e: watchlist_canvas.configure(scrollregion=watchlist_canvas.bbox("all")))

        # ----------------------------------------------------
        # HISTORY SCROLLING FIX
        # ----------------------------------------------------
        history_container = tk.Frame(main_content_frame, bg=t["CARD"], padx=10, pady=10)
        history_container.pack(side="right", fill="both", expand=True, padx=(5,0))
        tk.Label(history_container, text="📜 Movie Watch History", font=("Segoe UI", 12, "bold"), bg=t["CARD"]).pack(pady=5)

        history_canvas = tk.Canvas(history_container, bg=t["CARD"])
        history_canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar_h = ttk.Scrollbar(history_container, orient="vertical", command=history_canvas.yview)
        v_scrollbar_h.pack(side="right", fill="y")
        history_canvas.configure(yscrollcommand=v_scrollbar_h.set)
        
        movie_history_frame = tk.Frame(history_canvas, bg=t["CARD"])
        
        # FIX 1: Remove width=1, rely on the binding below.
        history_window_id = history_canvas.create_window((0,0), window=movie_history_frame, anchor="nw")
        
        # FIX 2: On canvas resize, update the inner frame's width using the stored ID.
        history_canvas.bind('<Configure>', 
            lambda e: history_canvas.itemconfig(history_window_id, width=e.width))
            
        # FIX 3: Bind the frame's configure event to update the scroll region
        movie_history_frame.bind("<Configure>", lambda e: history_canvas.configure(scrollregion=history_canvas.bbox("all")))

        # Initial load (Movies)
        load_watchlist()
        load_history()

        # --- 2. TV SHOWS TAB (Reusing TV Shows Page Code) ---
        tv_shows_tab = tk.Frame(media_notebook, bg=t["BG"])
        media_notebook.add(tv_shows_tab, text="📺 TV Shows")

        # --- GLOBAL VARIABLES (TV SHOWS SPECIFIC) ---
        global tv_show_title_entry, tv_year_entry, tv_season_entry, tv_episode_entry
        global tv_status_combo, tv_rating_combo, tv_genre_entry, tv_date_watched_entry
        global tv_watchlist_frame, tv_history_frame

        SHOW_STATUSES = ['Watchlist', 'Watched']
        SHOW_RATINGS = ['1 Star', '2 Stars', '3 Stars', '4 Stars', '5 Stars']

        # --- FUNCTIONS (TV Shows) ---
        def add_show():
            title = tv_show_title_entry.get().strip()
            year = tv_year_entry.get().strip()
            season = tv_season_entry.get().strip()
            episode = tv_episode_entry.get().strip()
            status = tv_status_combo.get()
            genre = tv_genre_entry.get().strip()
            rating_str = tv_rating_combo.get()
            date_watched = tv_date_watched_entry.get().strip()

            if not title or not status:
                messagebox.showwarning("Missing Data", "Title and Status are required.")
                return

            try:
                release_year = int(year) if year.isdigit() else None
                season_val = int(season) if season.isdigit() else None
                episode_val = int(episode) if episode.isdigit() else None
                rating = int(rating_str.split()[0]) if rating_str and status == 'Watched' else None

                if status == 'Watched' and (not date_watched or date_watched == "YYYY-MM-DD"):
                    date_watched = date.today().isoformat()

                run_query("""
                    INSERT INTO tv_shows (title, release_year, season, episode, status, genre, rating, date_watched)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (title, release_year, season_val, episode_val, status, genre, rating, date_watched))

                # Clear form
                tv_show_title_entry.delete(0, tk.END)
                tv_year_entry.delete(0, tk.END)
                tv_season_entry.delete(0, tk.END)
                tv_episode_entry.delete(0, tk.END)
                tv_status_combo.current(0)
                tv_rating_combo.set('')
                tv_genre_entry.delete(0, tk.END)
                tv_date_watched_entry.delete(0, tk.END)
                tv_date_watched_entry.insert(0, "YYYY-MM-DD")

                load_tv_watchlist()
                load_tv_history()

            except ValueError:
                messagebox.showerror("Input Error", "Year, Season, and Episode must be numbers.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add show: {e}")

        def delete_show(show_id):
            if messagebox.askyesno("Delete Show", "Are you sure you want to remove this show permanently?"):
                run_query("DELETE FROM tv_shows WHERE id = ?", (show_id,))
                load_tv_watchlist()
                load_tv_history()

        def mark_as_watched_tv(show_id):
            row = run_query("SELECT title, genre, rating FROM tv_shows WHERE id = ?", (show_id,))
            if not row:
                messagebox.showerror("Error", "Show not found.")
                return

            title, genre, rating = row[0]

            popup = tk.Toplevel(pg)
            popup.title(f"Mark '{title}' as Watched")
            popup.geometry("300x150")
            popup.grab_set()

            tk.Label(popup, text="Genre:").grid(row=0, column=0, padx=10, pady=10)
            genre_entry = tk.Entry(popup)
            genre_entry.insert(0, genre or "")
            genre_entry.grid(row=0, column=1, padx=10, pady=10)

            tk.Label(popup, text="Rating (1-5):").grid(row=1, column=0, padx=10, pady=10)
            rating_combo = ttk.Combobox(popup, values=['1','2','3','4','5'], state="readonly", width=5)
            rating_combo.set(str(rating) if rating else '')
            rating_combo.grid(row=1, column=1, padx=10, pady=10)

            def confirm():
                new_genre = genre_entry.get().strip()
                new_rating_str = rating_combo.get()
                new_rating = int(new_rating_str) if new_rating_str else None

                run_query("""
                    UPDATE tv_shows
                    SET status = ?, genre = ?, rating = ?, date_watched = ?
                    WHERE id = ?
                """, ('Watched', new_genre, new_rating, date.today().isoformat(), show_id))

                popup.destroy()
                load_tv_watchlist()
                load_tv_history()
                messagebox.showinfo("Updated", f"'{title}' marked as Watched!")

            tk.Button(popup, text="Confirm", command=confirm, bg=t["ACCENT"], fg="white").grid(row=2, column=0, columnspan=2, pady=10)

        def load_tv_watchlist():
            for widget in tv_watchlist_frame.winfo_children():
                widget.destroy()

            rows = run_query("SELECT id, title, release_year, season, episode FROM tv_shows WHERE status = 'Watchlist' ORDER BY title ASC")
            if not rows:
                tk.Label(tv_watchlist_frame, text="Your Watchlist is empty! 📺", bg=t["CARD"], fg=t["TEXT"]).pack(pady=20)
                return

            for show_id, title, release_year, season, episode in rows:
                row_frame = tk.Frame(tv_watchlist_frame, bg=t["CARD"], bd=1, relief="solid")
                row_frame.pack(fill="x", pady=5, padx=5)

                title_text = f"📺 {title} ({release_year or 'N/A'}) S{season or '?'}E{episode or '?'}"
                tk.Label(row_frame, text=title_text, font=("Segoe UI", 10, "bold"), bg=t["CARD"], fg=t["TEXT"]).pack(side="left", padx=5)

                tk.Button(row_frame, text="Mark as Watched", command=lambda sid=show_id: mark_as_watched_tv(sid),
                        bg=t["ACCENT"], fg="white", relief="flat").pack(side="right", padx=5)
                tk.Button(row_frame, text="✖", command=lambda sid=show_id: delete_show(sid),
                        bg=t["CARD"], fg="red").pack(side="right")

        def load_tv_history():
            for widget in tv_history_frame.winfo_children():
                widget.destroy()

            rows = run_query("SELECT id, title, release_year, season, episode, genre, rating, date_watched FROM tv_shows WHERE status = 'Watched' ORDER BY date_watched DESC")
            if not rows:
                tk.Label(tv_history_frame, text="No shows watched yet! 📺", bg=t["CARD"], fg=t["TEXT"]).pack(pady=20)
                return

            for show_id, title, release_year, season, episode, genre, rating, date_watched in rows:
                row_frame = tk.Frame(tv_history_frame, bg=t["CARD"], bd=1, relief="solid")
                row_frame.pack(fill="x", pady=5, padx=5)

                row_frame.grid_columnconfigure(0, weight=1)

                title_text = f"📺 {title} ({release_year or 'N/A'}) S{season or '?'}E{episode or '?'}"
                tk.Label(row_frame, text=title_text, font=("Segoe UI", 10, "bold"),
                        bg=t["CARD"], fg=t["TEXT"]).grid(row=0, column=0, sticky="w", padx=5)

                star_rating = "★" * (rating or 0) + "☆" * (5 - (rating or 0))
                tk.Label(row_frame, text=star_rating, font=("Segoe UI", 12), bg=t["CARD"], fg="gold").grid(row=0, column=1, padx=10, sticky="e")

                details_text = f"Genre: {genre or 'N/A'} | Watched: {date_watched or 'N/A'}"
                tk.Label(row_frame, text=details_text, font=("Segoe UI", 9), bg=t["CARD"], fg=t["ACCENT"]).grid(row=1, column=0, sticky="w", padx=5)

                tk.Button(row_frame, text="✖", command=lambda sid=show_id: delete_show(sid),
                        relief="flat", bd=0, bg=t["CARD"], fg="red").grid(row=0, column=2, rowspan=2, padx=5, sticky="e")

                row_frame.grid_columnconfigure(1, weight=0)
                row_frame.grid_columnconfigure(2, weight=0)

        # --- UI Layout (TV Shows Tab) ---
        tk.Label(tv_shows_tab, text="Add New TV Show Entry", font=("Segoe UI", 14, "bold"), bg=t["BG"], fg=t["TEXT"]).pack(pady=(10, 5))

        # Input Section
        input_frame = tk.Frame(tv_shows_tab, bg=t["CARD"], padx=10, pady=10)
        input_frame.pack(fill="x", padx=10, pady=(0, 15))

        r = 0
        tk.Label(input_frame, text="Title:", bg=t["CARD"]).grid(row=r, column=0, sticky="w", padx=5)
        tv_show_title_entry = tk.Entry(input_frame)
        tv_show_title_entry.grid(row=r, column=1, sticky="ew", padx=5)

        tk.Label(input_frame, text="Year:", bg=t["CARD"]).grid(row=r, column=2, sticky="w", padx=5)
        tv_year_entry = tk.Entry(input_frame, width=8)
        tv_year_entry.grid(row=r, column=3, sticky="w", padx=5)

        tk.Label(input_frame, text="Season:", bg=t["CARD"]).grid(row=r, column=4, sticky="w", padx=5)
        tv_season_entry = tk.Entry(input_frame, width=5)
        tv_season_entry.grid(row=r, column=5, sticky="w", padx=5)
        r += 1

        tk.Label(input_frame, text="Episode:", bg=t["CARD"]).grid(row=r, column=0, sticky="w", padx=5)
        tv_episode_entry = tk.Entry(input_frame, width=5)
        tv_episode_entry.grid(row=r, column=1, sticky="w", padx=5)

        tk.Label(input_frame, text="Genre:", bg=t["CARD"]).grid(row=r, column=2, sticky="w", padx=5)
        tv_genre_entry = tk.Entry(input_frame)
        tv_genre_entry.grid(row=r, column=3, sticky="ew", padx=5)

        tk.Label(input_frame, text="Status:", bg=t["CARD"]).grid(row=r, column=4, sticky="w", padx=5)
        tv_status_combo = ttk.Combobox(input_frame, values=SHOW_STATUSES, state="readonly", width=10)
        tv_status_combo.current(0)
        tv_status_combo.grid(row=r, column=5, sticky="w", padx=5)
        r += 1

        tk.Label(input_frame, text="Rating (1-5):", bg=t["CARD"]).grid(row=r, column=0, sticky="w", padx=5)
        tv_rating_combo = ttk.Combobox(input_frame, values=SHOW_RATINGS, state="readonly", width=8)
        tv_rating_combo.grid(row=r, column=1, sticky="w", padx=5)

        tk.Label(input_frame, text="Date Watched:", bg=t["CARD"]).grid(row=r, column=2, sticky="w", padx=5)
        tv_date_watched_entry = tk.Entry(input_frame, width=15)
        tv_date_watched_entry.insert(0, "YYYY-MM-DD")
        tv_date_watched_entry.grid(row=r, column=3, sticky="w", padx=5)

        tk.Button(input_frame, text="Add/Update Show", command=add_show,
                bg=t["ACCENT"], fg="white").grid(row=r, column=5, padx=10, sticky="e")

        input_frame.grid_columnconfigure(1, weight=1)

        # Main content: Watchlist & History
        main_content_frame = tk.Frame(tv_shows_tab, bg=t["BG"])
        main_content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Watchlist Scrollable Frame
        watchlist_container = tk.Frame(main_content_frame, bg=t["CARD"], padx=10, pady=10)
        watchlist_container.pack(side="left", fill="both", expand=True, padx=(0,5))
        tk.Label(watchlist_container, text="🌟 TV Show Watchlist", font=("Segoe UI", 12, "bold"), bg=t["CARD"]).pack(pady=5)

        watchlist_canvas = tk.Canvas(watchlist_container, bg=t["CARD"])
        watchlist_canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar_w = ttk.Scrollbar(watchlist_container, orient="vertical", command=watchlist_canvas.yview)
        v_scrollbar_w.pack(side="right", fill="y")
        watchlist_canvas.configure(yscrollcommand=v_scrollbar_w.set)
        tv_watchlist_frame = tk.Frame(watchlist_canvas, bg=t["CARD"])
        watchlist_canvas.create_window((0,0), window=tv_watchlist_frame, anchor="nw", width=1)
        tv_watchlist_frame.bind("<Configure>", lambda e: watchlist_canvas.configure(scrollregion=watchlist_canvas.bbox("all")))
        watchlist_canvas.bind('<Configure>', lambda e: watchlist_canvas.itemconfig(watchlist_canvas.find_withtag("all")[0], width=e.width))

        # History Scrollable Frame
        history_container = tk.Frame(main_content_frame, bg=t["CARD"], padx=10, pady=10)
        history_container.pack(side="right", fill="both", expand=True, padx=(5,0))
        tk.Label(history_container, text="📜 TV Show History", font=("Segoe UI", 12, "bold"), bg=t["CARD"]).pack(pady=5)

        history_canvas = tk.Canvas(history_container, bg=t["CARD"])
        history_canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar_h = ttk.Scrollbar(history_container, orient="vertical", command=history_canvas.yview)
        v_scrollbar_h.pack(side="right", fill="y")
        history_canvas.configure(yscrollcommand=v_scrollbar_h.set)
        tv_history_frame = tk.Frame(history_canvas, bg=t["CARD"])
        history_canvas.create_window((0,0), window=tv_history_frame, anchor="nw", width=1)
        tv_history_frame.bind("<Configure>", lambda e: history_canvas.configure(scrollregion=history_canvas.bbox("all")))
        history_canvas.bind('<Configure>', lambda e: history_canvas.itemconfig(history_canvas.find_withtag("all")[0], width=e.width))

        # --- Initial Load (TV Shows) ---
        load_tv_watchlist()
        load_tv_history()

        # --- 3. BOOKS TAB (Reusing Books Page Code) ---
        books_tab = tk.Frame(media_notebook, bg=t["BG"])
        media_notebook.add(books_tab, text="📖 Books")

        # --- GLOBAL DECLARATIONS & INITIALIZATION (Books Specific) ---
        global title_entry, author_entry, pages_entry, status_combo, rating_combo, genre_entry
        global active_books_frame, history_books_frame, start_date_entry, finish_date_entry
        
        # Static list for the status dropdown
        BOOK_STATUSES = ['To Read', 'In Progress', 'Completed']
        BOOK_RATINGS = ['1 Star', '2 Stars', '3 Stars', '4 Stars', '5 Stars']

        # --- FUNCTIONS (Books) ---
        
        def add_book():
            """Handles validation and saving the book entry to the database."""
            title = title_entry.get().strip()
            author = author_entry.get().strip()
            pages = pages_entry.get().strip()
            status = status_combo.get()
            genre = genre_entry.get().strip()
            rating_str = rating_combo.get()
            start_date = start_date_entry.get().strip()
            finish_date = finish_date_entry.get().strip()

            if not title or not status:
                messagebox.showwarning("Missing Data", "Title and Status are required.")
                return

            try:
                total_pages = int(pages) if pages else 0
                rating = int(rating_str.split()[0]) if rating_str and status == 'Completed' else None
                start_date_val = start_date if start_date and start_date != date.today().isoformat() else None # Keep as None if default today/empty
                finish_date_val = finish_date if finish_date and finish_date != "YYYY-MM-DD" else None

                # Corrected column order
                run_query("""
                    INSERT INTO books (title, author, total_pages, current_page, status, start_date, finish_date, genre, rating)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (title, author, total_pages, 0, status, start_date_val, finish_date_val, genre, rating))

                title_entry.delete(0, tk.END)
                author_entry.delete(0, tk.END)
                pages_entry.delete(0, tk.END)
                genre_entry.delete(0, tk.END)
                status_combo.set('To Read')
                rating_combo.set('')
                start_date_entry.delete(0, tk.END)
                start_date_entry.insert(0, date.today().isoformat())
                finish_date_entry.delete(0, tk.END)
                finish_date_entry.insert(0, "YYYY-MM-DD")

                load_active_books()
                load_history_books()

            except ValueError:
                messagebox.showerror("Input Error", "Total Pages must be a whole number.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add book: {e}")
        
        # NOTE: The original book code used pg.load_active_books and pg.load_history which won't work 
        # inside this combined scope unless we define it locally. We'll rename load_history to load_history_books.
        
        def update_current_page(book_id, page_entry, total_pages):
            """Updates the current_page for a book and refreshes the display."""
            try:
                new_page = int(page_entry.get().strip())
            
                if new_page < 0 or new_page > total_pages:
                    messagebox.showwarning("Invalid Page", f"Page must be between 0 and {total_pages}.")
                    return

                run_query("UPDATE books SET current_page = ? WHERE id = ?", (new_page, book_id))
            
                # If the user finished the book, prompt to update status to 'Completed'
                if new_page == total_pages:
                    if messagebox.askyesno("Book Finished?", "Congratulations! Mark this book as 'Completed' and add a rating?"):
                        messagebox.showinfo("Next Step", "Please use the input form above to change the Status to 'Completed' and add a Rating/Finish Date.")

                load_active_books()
                load_history_books() 

            except ValueError:
                messagebox.showerror("Error", "Page number must be a whole number.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update page: {e}")

        def delete_book_item(book_id):
            """Removes a book permanently from the lists."""
            if messagebox.askyesno("Delete Book", "Are you sure you want to remove this book permanently?"):
                run_query("DELETE FROM books WHERE id = ?", (book_id,)) 
                load_active_books()
                load_history_books()

        def load_active_books():
            """Fetches and displays books with status 'To Read' or 'In Progress'."""
            for widget in active_books_frame.winfo_children():
                widget.destroy()

            # Fetch items: 'To Read' (status=0) and 'In Progress' (status=1)
            # Ordered by status (In Progress first)
            rows = run_query("SELECT id, title, author, total_pages, current_page, status FROM books WHERE status IN ('To Read', 'In Progress') ORDER BY status DESC, id DESC")
        
            if not rows:
                tk.Label(active_books_frame, text="Time to start a new book! 🥳", bg=t["CARD"], fg=t["TEXT"]).pack(pady=20)
                return

            for book_id, title, author, total_pages, current_page, status in rows:
                book_row = tk.Frame(active_books_frame, bg=t["CARD"], bd=1, relief="solid")
                book_row.pack(fill="x", pady=5, padx=5)

                # Title and Author
                tk.Label(book_row, text=f"📖 {title}", font=("Segoe UI", 10, "bold"), bg=t["CARD"], fg=t["TEXT"]).pack(anchor="w", padx=5, pady=2)
                tk.Label(book_row, text=f"By: {author}", font=("Segoe UI", 9), bg=t["CARD"], fg="gray").pack(anchor="w", padx=5)

                # --- 'In Progress' Logic (Show Progress Bar and Updater) ---
                if status == 'In Progress' and total_pages > 0:
                    progress_container = tk.Frame(book_row, bg=t["CARD"])
                    progress_container.pack(fill="x", padx=5, pady=5)
                
                    progress_percent = (current_page / total_pages) * 100
                
                    # Progress Bar
                    progress_bar = ttk.Progressbar(progress_container, orient="horizontal", length=200, mode="determinate", value=progress_percent)
                    progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))
                
                    # Progress Text
                    tk.Label(progress_container, text=f"{current_page}/{total_pages} pages ({progress_percent:.0f}%)", bg=t["CARD"]).pack(side="left")

                    # Quick Page Update Input
                    update_frame = tk.Frame(book_row, bg=t["CARD"])
                    update_frame.pack(fill="x", padx=5, pady=5)
                
                    tk.Label(update_frame, text="Update Page:", bg=t["CARD"]).pack(side="left")
                    page_update_entry = tk.Entry(update_frame, width=6)
                    page_update_entry.insert(0, str(current_page))
                    page_update_entry.pack(side="left", padx=5)
                
                    # Update Button
                    tk.Button(update_frame, text="Update", 
                            command=lambda bid=book_id, pue=page_update_entry, tp=total_pages: update_current_page(bid, pue, tp), 
                            bg=t["ACCENT"], fg="white").pack(side="left", padx=(0, 10))
                    
                # --- 'To Read' Logic ---
                elif status == 'To Read':
                    tk.Label(book_row, text="Status: To Read", bg=t["CARD"], fg=t["ACCENT"]).pack(anchor="w", padx=5, pady=5)
            
                # Delete button (placed generally, not restricted to any status)
                tk.Button(book_row, text="✖", command=lambda bid=book_id: delete_book_item(bid),
                        bg=t["CARD"], fg="red").pack(side="right")


        def load_history_books():
            """Fetches and displays books with status 'Completed' (Reading History)."""
            for widget in history_books_frame.winfo_children():
                widget.destroy()

            # Fetch items: status 'Completed', ordered by finish date descending (most recent first)
            rows = run_query("SELECT id, title, author, genre, rating, finish_date FROM books WHERE status = 'Completed' ORDER BY finish_date DESC, id DESC")
        
            if not rows:
                tk.Label(history_books_frame, text="Your history is empty! Start reading! 📖", bg=t["CARD"], fg=t["TEXT"]).pack(pady=20)
                return

            # Setup Scrollable content
            history_canvas = tk.Canvas(history_books_frame, bg=t["CARD"])
            history_canvas.pack(side="left", fill="both", expand=True)
            v_scrollbar = ttk.Scrollbar(history_books_frame, orient="vertical", command=history_canvas.yview)
            v_scrollbar.pack(side="right", fill="y")
            history_canvas.configure(yscrollcommand=v_scrollbar.set)
        
            list_content_frame = tk.Frame(history_canvas, bg=t["CARD"])
            history_canvas.create_window((0, 0), window=list_content_frame, anchor="nw", width=1)
        
            def on_history_frame_configure(event):
                history_canvas.configure(scrollregion=history_canvas.bbox("all"))
            list_content_frame.bind("<Configure>", on_history_frame_configure)
            history_canvas.bind('<Configure>', lambda e: history_canvas.itemconfig(history_canvas.find_withtag("all")[0], width=e.width))


            for book_id, title, author, genre, rating, finish_date in rows:
                book_row = tk.Frame(list_content_frame, bg=t["CARD"], bd=1, relief="solid")
                book_row.pack(fill="x", pady=5, padx=5)
            
                book_row.grid_columnconfigure(0, weight=1) # Title/Author expands

                # Row 0: Title
                tk.Label(book_row, text=f"📖 {title}", font=("Segoe UI", 10, "bold"), bg=t["CARD"], fg=t["TEXT"]).grid(row=0, column=0, sticky="w", padx=5)
                # Row 1: Author
                tk.Label(book_row, text=f"By: {author}", font=("Segoe UI", 9), bg=t["CARD"], fg="gray").grid(row=1, column=0, sticky="w", padx=5)

                # Row 0, Column 1: Rating
                star_rating = "★" * (rating or 0) + "☆" * (5 - (rating or 0))
                tk.Label(book_row, text=star_rating, font=("Segoe UI", 12), bg=t["CARD"], fg="gold").grid(row=0, column=1, padx=10, sticky="e")

                # Row 1, Column 1: Genre/Date
                details_text = f"({genre or 'N/A'}) | Finished: {finish_date or 'N/A'}"
                tk.Label(book_row, text=details_text, font=("Segoe UI", 8), bg=t["CARD"], fg=t["ACCENT"]).grid(row=1, column=1, padx=10, sticky="e")
            
                # Delete Button
                delete_btn = tk.Button(book_row, text="✖", 
                                    command=lambda bid=book_id: delete_book_item(bid), 
                                    relief="flat", bd=0, bg=t["CARD"], fg="red")
                delete_btn.grid(row=0, column=2, rowspan=2, padx=5, sticky="e")
            
                book_row.grid_columnconfigure(1, weight=1) # Ensures rating is pushed right

        # --- UI LAYOUT (Books Tab) ---
        tk.Label(books_tab, text="Add New Book Entry", font=("Segoe UI", 14, "bold"), bg=t["BG"], fg=t["TEXT"]).pack(pady=(10, 5))

        # 1. Input Section (Top)
        input_frame = tk.Frame(books_tab, bg=t["CARD"], padx=10, pady=10)
        input_frame.pack(fill="x", padx=10, pady=(0, 15))

        # Using grid for structured input
        r = 0 # Row counter

        # Row 0: Title, Author
        tk.Label(input_frame, text="Title:", bg=t["CARD"]).grid(row=r, column=0, sticky="w", padx=5)
        title_entry = tk.Entry(input_frame)
        title_entry.grid(row=r, column=1, sticky="ew", padx=5)

        tk.Label(input_frame, text="Author:", bg=t["CARD"]).grid(row=r, column=2, sticky="w", padx=5)
        author_entry = tk.Entry(input_frame)
        author_entry.grid(row=r, column=3, sticky="ew", padx=5)
        r += 1

        # Row 1: Pages, Genre
        tk.Label(input_frame, text="Pages:", bg=t["CARD"]).grid(row=r, column=0, sticky="w", padx=5, pady=5)
        pages_entry = tk.Entry(input_frame, width=8)
        pages_entry.grid(row=r, column=1, sticky="w", padx=5, pady=5)

        tk.Label(input_frame, text="Genre:", bg=t["CARD"]).grid(row=r, column=2, sticky="w", padx=5, pady=5)
        genre_entry = tk.Entry(input_frame)
        genre_entry.grid(row=r, column=3, sticky="ew", padx=5, pady=5)
        r += 1

        # Row 2: Status, Rating
        tk.Label(input_frame, text="Status:", bg=t["CARD"]).grid(row=r, column=0, sticky="w", padx=5)
        status_combo = ttk.Combobox(input_frame, values=BOOK_STATUSES, state="readonly")
        status_combo.current(0) # Default to 'To Read'
        status_combo.grid(row=r, column=1, sticky="w", padx=5)

        tk.Label(input_frame, text="Rating (1-5):", bg=t["CARD"]).grid(row=r, column=2, sticky="w", padx=5)
        rating_combo = ttk.Combobox(input_frame, values=BOOK_RATINGS, state="readonly")
        rating_combo.grid(row=r, column=3, sticky="w", padx=5)
        r += 1
        
        # Row 3 : Start Date, Finish Date
        tk.Label(input_frame, text="Date Started:", bg=t["CARD"]).grid(row=r, column=0, sticky="w", padx=5, pady=5)
        start_date_entry = tk.Entry(input_frame, width=15)
        start_date_entry.insert(0, date.today().isoformat()) # Pre-fill with today's date
        start_date_entry.grid(row=r, column=1, sticky="w", padx=5, pady=5)

        tk.Label(input_frame, text="Date Finished:", bg=t["CARD"]).grid(row=r, column=2, sticky="w", padx=5, pady=5)
        finish_date_entry = tk.Entry(input_frame, width=15)
        finish_date_entry.insert(0, "YYYY-MM-DD") # Placeholder
        finish_date_entry.grid(row=r, column=3, sticky="w", padx=5, pady=5)
        
        tk.Button(input_frame, text="Add/Update Book", command=add_book, bg=t["ACCENT"], fg="white").grid(row=r, column=4, rowspan=1, padx=10, sticky="e")

        input_frame.grid_columnconfigure(1, weight=1) # Title field expands
        input_frame.grid_columnconfigure(3, weight=1) # Author field expands

        # 2. Main Content Containers (Side-by-Side)
        main_content_frame = tk.Frame(books_tab, bg=t["BG"])
        main_content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # --- Left Column: Active Reading (To Read / In Progress) ---
        active_container = tk.Frame(main_content_frame, bg=t["CARD"], padx=10, pady=10)
        active_container.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        tk.Label(active_container, text="🔥 Active Reading & To-Read List", font=("Segoe UI", 12, "bold"), bg=t["CARD"]).pack(pady=5)
        
        active_books_frame = tk.Frame(active_container, bg=t["CARD"])
        active_books_frame.pack(fill="both", expand=True) 

        # --- Right Column: Reading History (Completed) ---
        history_container = tk.Frame(main_content_frame, bg=t["CARD"], padx=10, pady=10)
        history_container.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        tk.Label(history_container, text="📜 Reading History (Completed)", font=("Segoe UI", 12, "bold"), bg=t["CARD"]).pack(pady=5)

        history_books_frame = tk.Frame(history_container, bg=t["CARD"])
        history_books_frame.pack(fill="both", expand=True)

        # --- Initial Load (Books) ---
        load_active_books()
        load_history_books()


        # --- 4. AU LOGS TAB (Reusing AU Page Code) ---
        au_tab = tk.Frame(media_notebook, bg=t["BG"])
        media_notebook.add(au_tab, text="🎧 AU Logs")

        # --- GLOBAL VARIABLES (AU Logs specific) ---
        global au_title_entry, au_author_entry, au_link_entry, au_group_entry, au_genre_entry
        global au_rating_combo, au_status_combo, au_active_frame, au_completed_frame

        AU_STATUS_OPTIONS = ['Reading', 'Completed', 'On Hold', 'Dropped', 'Plan to Read']
        AU_RATINGS = ['1 Star', '2 Stars', '3 Stars', '4 Stars', '5 Stars']

        # --- FUNCTIONS (AU Logs) ---
        def add_au_log():
            title = au_title_entry.get().strip()
            author = au_author_entry.get().strip()
            link = au_link_entry.get().strip()
            group = au_group_entry.get().strip()
            genre = au_genre_entry.get().strip()
            rating_str = au_rating_combo.get()
            status = au_status_combo.get()

            if not title or not status:
                messagebox.showwarning("Missing Data", "Title and Status are required.")
                return

            try:
                rating = int(rating_str.split()[0]) if rating_str else None

                run_query("""
                    INSERT INTO au (title, author, link, "group", genre, rating, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (title, author, link, group, genre, rating, status))

                # Clear form
                au_title_entry.delete(0, tk.END)
                au_author_entry.delete(0, tk.END)
                au_link_entry.delete(0, tk.END)
                au_group_entry.delete(0, tk.END)
                au_genre_entry.delete(0, tk.END)
                au_rating_combo.set('')
                au_status_combo.set(AU_STATUS_OPTIONS[0]) # Reset status to a default

                load_au_active()
                load_au_completed()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to add AU log: {e}")

        def delete_au_log(log_id):
            if messagebox.askyesno("Delete Log", "Are you sure you want to remove this log?"):
                run_query("DELETE FROM au WHERE id = ?", (log_id,))
                load_au_active()
                load_au_completed()

        def mark_au_completed(log_id):
            # NOTE: In a real app, this should prompt for rating/details, but for simplicity, 
            # we'll just update the status to 'Completed' for now.
            if messagebox.askyesno("Confirm Completion", "Mark this item as 'Completed'?"):
                run_query("UPDATE au SET status = 'Completed' WHERE id = ?", (log_id,))
                load_au_active()
                load_au_completed()
                messagebox.showinfo("Updated", "Marked as Completed!")


        def load_au_active():
            for widget in au_active_frame.winfo_children():
                widget.destroy()

            rows = run_query("SELECT id, title, author, link, \"group\", genre, rating, status FROM au WHERE status != 'Completed' ORDER BY title ASC")
            if not rows:
                tk.Label(au_active_frame, text="No active AU logs! 🎧", bg=t["CARD"], fg=t["TEXT"]).pack(pady=20)
                return

            for log_id, title, author, link, group, genre, rating, status in rows:
                row_frame = tk.Frame(au_active_frame, bg=t["CARD"], bd=1, relief="solid")
                row_frame.pack(fill="x", pady=5, padx=5)

                info = f"🎧 {title} by {author or 'N/A'} | Group: {group or 'N/A'} | Genre: {genre or 'N/A'}"
                if rating:
                    info += f" | {'★'*rating}{'☆'*(5-rating)}"
                info += f" | Status: {status}"

                tk.Label(row_frame, text=info, font=("Segoe UI", 10, "bold"), bg=t["CARD"], fg=t["TEXT"]).pack(side="left", padx=5)

                if status != 'Completed':
                    tk.Button(row_frame, text="Mark Completed", command=lambda lid=log_id: mark_au_completed(lid),
                            bg=t["ACCENT"], fg="white", relief="flat").pack(side="right", padx=5)
                
                tk.Button(row_frame, text="✖", command=lambda lid=log_id: delete_au_log(lid),
                        bg=t["CARD"], fg="red").pack(side="right")

        def load_au_completed():
            for widget in au_completed_frame.winfo_children():
                widget.destroy()

            rows = run_query("SELECT id, title, author, link, \"group\", genre, rating FROM au WHERE status = 'Completed' ORDER BY title ASC")
            if not rows:
                tk.Label(au_completed_frame, text="No completed AU logs! 🎉", bg=t["CARD"], fg=t["TEXT"]).pack(pady=20)
                return

            for log_id, title, author, link, group, genre, rating in rows:
                row_frame = tk.Frame(au_completed_frame, bg=t["CARD"], bd=1, relief="solid")
                row_frame.pack(fill="x", pady=5, padx=5)

                info = f"🎧 {title} by {author or 'N/A'} | Group: {group or 'N/A'} | Genre: {genre or 'N/A'}"
                rating_text = f" {'★'*rating}{'☆'*(5-rating)}" if rating else ""

                tk.Label(row_frame, text=info, font=("Segoe UI", 10, "bold"), bg=t["CARD"], fg=t["TEXT"]).pack(side="left", padx=5)
                tk.Label(row_frame, text=rating_text, font=("Segoe UI", 10, "bold"), bg=t["CARD"], fg="gold").pack(side="left", padx=5)
                
                tk.Button(row_frame, text="✖", command=lambda lid=log_id: delete_au_log(lid),
                        bg=t["CARD"], fg="red").pack(side="right")

        # --- UI Layout (AU Logs Tab) ---
        tk.Label(au_tab, text="Add New AU Entry", font=("Segoe UI", 14, "bold"), bg=t["BG"], fg=t["TEXT"]).pack(pady=(10, 5))

        # Input Section
        input_frame = tk.Frame(au_tab, bg=t["CARD"], padx=10, pady=10)
        input_frame.pack(fill="x", padx=10, pady=(0,15))

        # Row 0
        tk.Label(input_frame, text="Title:", bg=t["CARD"]).grid(row=0, column=0, sticky="w", padx=5)
        au_title_entry = tk.Entry(input_frame)
        au_title_entry.grid(row=0, column=1, sticky="ew", padx=5)

        tk.Label(input_frame, text="Author:", bg=t["CARD"]).grid(row=0, column=2, sticky="w", padx=5)
        au_author_entry = tk.Entry(input_frame)
        au_author_entry.grid(row=0, column=3, sticky="ew", padx=5)

        # Row 1
        tk.Label(input_frame, text="Link:", bg=t["CARD"]).grid(row=1, column=0, sticky="w", padx=5)
        au_link_entry = tk.Entry(input_frame)
        au_link_entry.grid(row=1, column=1, sticky="ew", padx=5)

        tk.Label(input_frame, text="Group:", bg=t["CARD"]).grid(row=1, column=2, sticky="w", padx=5)
        au_group_entry = tk.Entry(input_frame)
        au_group_entry.grid(row=1, column=3, sticky="ew", padx=5)

        # Row 2
        tk.Label(input_frame, text="Genre:", bg=t["CARD"]).grid(row=2, column=0, sticky="w", padx=5)
        au_genre_entry = tk.Entry(input_frame)
        au_genre_entry.grid(row=2, column=1, sticky="ew", padx=5)

        tk.Label(input_frame, text="Rating:", bg=t["CARD"]).grid(row=2, column=2, sticky="w", padx=5)
        au_rating_combo = ttk.Combobox(input_frame, values=AU_RATINGS, state="readonly", width=10)
        au_rating_combo.grid(row=2, column=3, sticky="w", padx=5)

        # Row 3
        tk.Label(input_frame, text="Status:", bg=t["CARD"]).grid(row=3, column=0, sticky="w", padx=5)
        au_status_combo = ttk.Combobox(input_frame, values=AU_STATUS_OPTIONS, state="readonly", width=15)
        au_status_combo.current(0)
        au_status_combo.grid(row=3, column=1, sticky="w", padx=5)

        tk.Button(input_frame, text="Add / Update Log", command=add_au_log, bg=t["ACCENT"], fg="white").grid(row=3, column=3, padx=10)

        input_frame.grid_columnconfigure(1, weight=1)
        input_frame.grid_columnconfigure(3, weight=1)

        # Main Content: Active & Completed
        main_frame = tk.Frame(au_tab, bg=t["BG"])
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Left: Active Logs
        active_container = tk.Frame(main_frame, bg=t["CARD"], padx=10, pady=10)
        active_container.pack(side="left", fill="both", expand=True, padx=(0,5))
        tk.Label(active_container, text="📖 Active AU Logs", font=("Segoe UI", 12, "bold"), bg=t["CARD"]).pack(pady=5)

        active_canvas = tk.Canvas(active_container, bg=t["CARD"])
        active_canvas.pack(side="left", fill="both", expand=True)
        v_scroll_a = ttk.Scrollbar(active_container, orient="vertical", command=active_canvas.yview)
        v_scroll_a.pack(side="right", fill="y")
        active_canvas.configure(yscrollcommand=v_scroll_a.set)
        au_active_frame = tk.Frame(active_canvas, bg=t["CARD"])
        active_canvas.create_window((0,0), window=au_active_frame, anchor="nw", width=1)
        au_active_frame.bind("<Configure>", lambda e: active_canvas.configure(scrollregion=active_canvas.bbox("all")))
        active_canvas.bind('<Configure>', lambda e: active_canvas.itemconfig(active_canvas.find_withtag("all")[0], width=e.width))

        # Right: Completed Logs
        completed_container = tk.Frame(main_frame, bg=t["CARD"], padx=10, pady=10)
        completed_container.pack(side="right", fill="both", expand=True, padx=(5,0))
        tk.Label(completed_container, text="✅ Completed AU Logs", font=("Segoe UI", 12, "bold"), bg=t["CARD"]).pack(pady=5)

        completed_canvas = tk.Canvas(completed_container, bg=t["CARD"])
        completed_canvas.pack(side="left", fill="both", expand=True)
        v_scroll_c = ttk.Scrollbar(completed_container, orient="vertical", command=completed_canvas.yview)
        v_scroll_c.pack(side="right", fill="y")
        completed_canvas.configure(yscrollcommand=v_scroll_c.set)
        au_completed_frame = tk.Frame(completed_canvas, bg=t["CARD"])
        completed_canvas.create_window((0,0), window=au_completed_frame, anchor="nw", width=1)
        au_completed_frame.bind("<Configure>", lambda e: completed_canvas.configure(scrollregion=completed_canvas.bbox("all")))
        completed_canvas.bind('<Configure>', lambda e: completed_canvas.itemconfig(completed_canvas.find_withtag("all")[0], width=e.width))

        # --- Initial Load (AU Logs) ---
        load_au_active()
        load_au_completed()
    
    # --- MOOD PAGE ---
    if pn == "Mood":
        t = theme()

        # Mapping emojis to scores
        MOOD_SCORES = {
            "😭": 1,
            "☹️": 2,
            "😐": 3,
            "🙂": 4,
            "😊": 5
        }

        # --- HELPER FUNCTIONS ---
        def load_mood_data(limit=30):
            """Fetch last `limit` mood entries from DB."""
            conn = db_connect()
            c = conn.cursor()
            rows = c.execute("SELECT date, mood_emoji FROM moods ORDER BY date DESC LIMIT ?", (limit,)).fetchall()
            conn.close()
            rows.reverse()  # oldest → newest
            return rows

        def load_mood_for_selected_date():
            """Load mood for the chosen date and update UI."""
            try:
                selected_date_iso = date_entry.get_date().isoformat()
            except Exception:
                # Fallback: use today's date if get_date() misbehaves
                selected_date_iso = date.today().isoformat()

            conn = db_connect()
            c = conn.cursor()
            row = c.execute("SELECT mood_emoji FROM moods WHERE date = ?", (selected_date_iso,)).fetchone()
            conn.close()

            if row:
                mood_var.set(row[0])
            else:
                mood_var.set("")  # Clear selection if no record

            update_mood_display()

        def plot_mood_history():
            """Plot last 30 days of moods as a line chart."""
            rows = load_mood_data(limit=30)

            # Clear previous plot
            for widget in graph_frame.winfo_children():
                widget.destroy()

            if not rows:
                tk.Label(graph_frame, text="No mood data yet!", bg=t["CARD"], fg=t["TEXT"]).pack(pady=20)
                return

            dates = [datetime.strptime(row[0], '%Y-%m-%d') for row in rows]
            scores = [MOOD_SCORES.get(row[1], 3) for row in rows]

            fig, ax = plt.subplots(figsize=(6, 3), facecolor=t["CARD"])
            ax.plot(dates, scores, marker='o', linestyle='-', color='#ff86a5')
            ax.set_title("30-Day Mood Trend", fontsize=10, color=t["TEXT"])
            ax.set_xlabel("Date", fontsize=8, color=t["TEXT"])
            ax.set_ylabel("Mood Score", fontsize=8, color=t["TEXT"])

            # Y-axis emoji labels
            y_labels = ["😭", "☹️", "😐", "🙂", "😊"]
            ax.set_yticks(list(MOOD_SCORES.values()))
            ax.set_yticklabels(y_labels, fontsize=12)
            ax.set_ylim(0.5, 5.5)

            fig.autofmt_xdate(rotation=45)
            ax.set_facecolor(t["CARD"])
            ax.tick_params(axis='x', colors=t["TEXT"], labelsize=7)
            ax.tick_params(axis='y', colors=t["TEXT"])
            ax.spines['bottom'].set_color(t["TEXT"])
            ax.spines['left'].set_color(t["TEXT"])
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

            canvas_plot = FigureCanvasTkAgg(fig, master=graph_frame)
            canvas_plot.draw()
            canvas_plot.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        def update_mood_display():
            """Highlight selected mood button + big emoji display."""
            selected_emoji = mood_var.get()
            for child in mood_row.winfo_children():
                if isinstance(child, tk.Button):
                    child.config(bg=t["ACCENT"] if child.cget("text") == selected_emoji else t["BG"])
            big_emoji_label.config(text=selected_emoji)

        def update_mood_history_text():
            """Display last 15 days of moods in the text widget."""
            rows = load_mood_data(limit=15)
            history_list.config(state="normal")
            history_list.delete("1.0", "end")
            for d, m in rows:
                history_list.insert("end", f"{d}: {m}\n")
            history_list.config(state="disabled")

        def save_mood():
            """Save or update mood for the selected date."""
            try:
                selected_date_iso = date_entry.get_date().isoformat()
            except Exception:
                selected_date_iso = date.today().isoformat()

            selected_emoji = mood_var.get()
            if not selected_emoji:
                messagebox.showwarning("Selection Required", "Please select a mood emoji before saving.")
                return

            conn = db_connect()
            c = conn.cursor()
            c.execute("SELECT id FROM moods WHERE date = ?", (selected_date_iso,))
            existing = c.fetchone()

            if existing:
                if messagebox.askyesno("Overwrite?", f"Mood for {selected_date_iso} exists. Overwrite?"):
                    c.execute("UPDATE moods SET mood_emoji = ? WHERE id = ?", (selected_emoji, existing[0]))
                    messagebox.showinfo("Updated", f"Mood updated for {selected_date_iso}.")
                else:
                    conn.close()
                    return
            else:
                c.execute("INSERT INTO moods (date, mood_emoji) VALUES (?, ?)", (selected_date_iso, selected_emoji))
                messagebox.showinfo("Saved", f"Mood saved for {selected_date_iso}.")
            conn.commit()
            conn.close()

            plot_mood_history()
            update_mood_history_text()

        # --- UI ELEMENTS ---
        tk.Label(content, text="😊 Mood Tracker", font=("Segoe UI", 16, "bold"), bg=t["BG"]).pack(pady=10)

        # Date picker
        date_frame = tk.Frame(content, bg=t["CARD"])
        date_frame.pack(anchor="nw", padx=6, pady=(6, 0))
        tk.Label(date_frame, text="Select Date:", bg=t["CARD"], fg=t["TEXT"]).pack(side="left", padx=(0, 6))

        def on_date_change(event=None):
            # Called when date selection changes; ensures UI loads correct stored mood immediately.
            load_mood_for_selected_date()

        date_entry = DateEntry(
            date_frame, width=12, background='darkblue', foreground='white',
            borderwidth=2, date_pattern='yyyy-mm-dd', locale='en_US',
            selectmode='day', showweeknumbers=False
        )
        date_entry.set_date(date.today())
        date_entry.pack(side="left")

        # Bind both common variants of the DateEntry selection event to be robust across tkcalendar versions
        date_entry.bind("<<DateSelected>>", on_date_change)
        date_entry.bind("<<DateEntrySelected>>", on_date_change)

        # Mood picker
        tk.Label(content, text="Select Mood:", bg=t["CARD"], fg=t["TEXT"], font=("Segoe UI", 12, "bold")).pack(anchor="nw", padx=6, pady=(12, 6))
        moods = ["😭", "☹️", "😐", "🙂", "😊"]
        mood_var = tk.StringVar(value="")
        mood_row = tk.Frame(content, bg=t["CARD"])
        mood_row.pack(anchor="nw", padx=6, pady=6)

        for m in moods:
            b = tk.Button(
                mood_row, text=m, font=("Segoe UI Emoji", 24),
                relief="flat", bd=0, bg=t["BG"], activebackground=t["ACCENT"],
                command=lambda mm=m: [mood_var.set(mm), update_mood_display()]
            )
            b.pack(side="left", padx=6)

        # Big emoji display
        big_emoji_label = tk.Label(content, text="", bg=t["CARD"], fg=t["TEXT"], font=("Segoe UI Emoji", 48))
        big_emoji_label.pack(anchor="nw", padx=6, pady=10)

        # Save button
        tk.Button(content, text="Save Mood", command=save_mood, bg=t["ACCENT"], fg="white").pack(anchor="e", padx=6, pady=6)

        # Chart frame
        tk.Label(content, text="30-Day Mood Trend:", bg=t["CARD"], fg=t["TEXT"], font=("Segoe UI", 11, "bold")).pack(anchor="nw", padx=6, pady=(12, 2))
        graph_frame = tk.Frame(content, bg=t["CARD"])
        graph_frame.pack(fill="both", expand=True, padx=6, pady=6)

        # History frame
        tk.Label(content, text="Mood History (Last 15 Days):", bg=t["CARD"], fg=t["TEXT"], font=("Segoe UI", 11, "bold")).pack(anchor="nw", padx=6, pady=(12, 2))
        history_frame = tk.Frame(content, bg=t["CARD"])
        history_frame.pack(fill="both", expand=True, padx=6, pady=6)
        history_list = tk.Text(history_frame, height=8, wrap="word", state="disabled")
        history_list.pack(fill="both", expand=True)

        # Initial load
        plot_mood_history()
        update_mood_history_text()
        load_mood_for_selected_date()
        
    # GROCERIES PAGE
    if pn == "Groceries":
        # --- Clear the page first ---
        for widget in pg.winfo_children():
            widget.destroy()

        # --- GLOBAL DECLARATIONS & INITIALIZATION ---
        global item_entry, quantity_entry, unit_entry, list_destination, shopping_list_frame, inventory_list_frame

        # Variable to track where to add the item (0=Shopping List, 1=Inventory)
        list_destination = tk.IntVar(value=0) # Default to Shopping List
    
        # --- PLACEHOLDER FUNCTIONS (To be filled in the next steps) ---

        def load_shopping_list():
            """Fetches and displays items needed from the 'shopping_list' table."""
            global shopping_list_frame
            t = theme()
        
            # Clear previous widgets
            for widget in shopping_list_frame.winfo_children():
                widget.destroy()

            # Fetch items: incomplete items first (purchased=0)
            rows = run_query("SELECT id, item_name, quantity, purchased FROM shopping_list ORDER BY purchased ASC, id DESC")
        
            if not rows:
                tk.Label(shopping_list_frame, text="The list is clear! 🎉", bg=t["CARD"], fg=t["TEXT"]).pack(pady=20)
                return

            for item_id, item_name, quantity, purchased in rows:
                item_row = tk.Frame(shopping_list_frame, bg=t["CARD"])
                item_row.pack(fill="x", pady=2, padx=4)

                purchased_var = tk.IntVar(value=purchased)
            
                # --- Checkbutton for Purchased Status ---
                check = tk.Checkbutton(item_row, variable=purchased_var, 
                                        text=f"{item_name} ({quantity})", 
                                        font=("Segoe UI", 10), anchor="w",
                                        bg=t["CARD"], fg=t["TEXT"], 
                                        activebackground=t["CARD"],
                                        selectcolor=t["CARD"],
                                        # Command calls the toggle function
                                        command=lambda iid=item_id, pv=purchased_var: toggle_purchased(iid, pv))
            
                # Apply visual purchased status (strikethrough)
                if purchased:
                    # Use a slightly muted color and strikethrough font
                    check.config(fg="gray", font=("Segoe UI", 10, "overstrike"))

                check.pack(side="left", fill="x", expand=True, padx=5)

                # --- Delete Button ---
                delete_btn = tk.Button(item_row, text="✖", 
                                    command=lambda iid=item_id: delete_item(iid), 
                                    relief="flat", bd=0, bg=t["CARD"], fg="red")
                delete_btn.pack(side="right", padx=5)

        # Attach function to the page object for initial load call at the bottom
        pg.load_shopping_list = load_shopping_list

        def load_inventory():
            """Fetches and displays items stocked in the 'inventory' table."""
            global inventory_list_frame
            t = theme()
        
            # Clear previous widgets
            for widget in inventory_list_frame.winfo_children():
                widget.destroy()

            # Fetch all items from inventory
            rows = run_query("SELECT id, item_name, current_quantity, unit FROM inventory ORDER BY item_name ASC")
        
            if not rows:
                tk.Label(inventory_list_frame, text="Your inventory is empty! 🤷‍♀️", bg=t["CARD"], fg=t["TEXT"]).pack(pady=20)
                return

            # Create a header row for clarity
            header_row = tk.Frame(inventory_list_frame, bg=t["CARD"])
            header_row.pack(fill="x", pady=(5, 0), padx=4)
            tk.Label(header_row, text="Item", font=("Segoe UI", 9, "bold"), bg=t["CARD"]).pack(side="left", padx=5, anchor="w")
            tk.Label(header_row, text="Quantity", font=("Segoe UI", 9, "bold"), bg=t["CARD"]).pack(side="left", padx=50, anchor="w")


            for item_id, item_name, current_quantity, unit in rows:
                item_row = tk.Frame(inventory_list_frame, bg=t["CARD"])
                item_row.pack(fill="x", pady=2, padx=4)

                # --- Item Name Label ---
                item_label = tk.Label(item_row, text=item_name, 
                                    font=("Segoe UI", 10), anchor="w",
                                    bg=t["CARD"], fg=t["TEXT"])
                item_label.pack(side="left", fill="x", expand=True, padx=5)

                # --- Quantity Label (Right-aligned) ---
                qty_text = f"{current_quantity:.0f} {unit}" if unit else f"{current_quantity:.0f}"
                qty_label = tk.Label(item_row, text=qty_text, 
                                    font=("Segoe UI", 10, "bold"), anchor="w",
                                    bg=t["CARD"], fg=t["ACCENT"])
                qty_label.pack(side="left", padx=10)


                # --- Consume/Delete Button ---
                consume_btn = tk.Button(item_row, text="Consume 🗑️", 
                                        command=lambda iid=item_id: consume_item(iid), 
                                        relief="flat", bd=0, 
                                        bg=t["BTN"], fg=t["TEXT"], 
                                        activebackground=t["BTN"])
                consume_btn.pack(side="right", padx=5)

        # Attach function to the page object for initial load call at the bottom
        pg.load_inventory = load_inventory
        
        def clear_purchased():
            """Deletes all items that have been marked as purchased from the shopping_list table."""
        
            # 1. Ask for confirmation
            if not messagebox.askyesno("Clear Purchased", "Are you sure you want to remove ALL checked-off items from the list? This action cannot be undone."):
                return
            
            try:
                # 2. Execute the DELETE query
                # We specifically target rows where purchased is 1
                run_query("DELETE FROM shopping_list WHERE purchased = 1")
            
                # 3. Inform the user and refresh the UI
                messagebox.showinfo("Success", "All purchased items have been cleared!")
                pg.load_shopping_list() # Reload the list to show the updated status
            
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear purchased items: {e}")
            
        def consume_item(item_id):
            """Removes an item permanently from the inventory table (simulates consumption)."""
            if messagebox.askyesno("Consume Item", "Marking item as consumed. Are you sure you want to remove it from inventory?"):
                run_query("DELETE FROM inventory WHERE id = ?", (item_id,)) 
                pg.load_inventory()
            
        def toggle_purchased(item_id, purchased_var):
            """Toggles the 'purchased' status of an item in the shopping_list table."""
            new_state = purchased_var.get()
            run_query("UPDATE shopping_list SET purchased = ? WHERE id = ?", (new_state, item_id)) 
            pg.load_shopping_list() # Reload to move purchased item to the bottom

        def delete_item(item_id):
            """Deletes an item permanently from the shopping_list table."""
            if messagebox.askyesno("Delete Item", "Are you sure you want to remove this item from the shopping list?"):
                run_query("DELETE FROM shopping_list WHERE id = ?", (item_id,)) 
                pg.load_shopping_list()
        
        def add_item():
            """Adds the item to either the shopping list or inventory based on the radio selection."""
            item = item_entry.get().strip()
            qty = quantity_entry.get().strip()
            unit = unit_entry.get().strip()
            destination = list_destination.get()

            if not item or not qty:
                messagebox.showwarning("Missing Data", "Please enter an item name and quantity.")
                return

            try:
                if destination == 0:
                    # Add to shopping_list (default purchased=0)
                    run_query("INSERT INTO shopping_list (item_name, quantity) VALUES (?, ?)", (item, qty))
                    load_shopping_list()
                else:
                    # Add to inventory (requires unit, assuming quantity is a number)
                    float(qty) # Attempt to convert to number for inventory tracking
                    run_query("INSERT INTO inventory (item_name, current_quantity, unit) VALUES (?, ?, ?)", (item, float(qty), unit))
                    load_inventory()

                item_entry.delete(0, tk.END)
                quantity_entry.delete(0, tk.END)
            
            except ValueError:
                messagebox.showerror("Format Error", "Inventory quantity must be a number.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add item: {e}")

        # --- UI LAYOUT START ---
    
        tk.Label(pg, text="🛒 Groceries & Inventory", font=("Segoe UI", 16, "bold"), bg=theme()["BG"]).pack(pady=10)

        # 1. Shared Input Frame (Top)
        input_frame = tk.Frame(pg, bg=theme()["CARD"], padx=10, pady=10)
        input_frame.pack(fill="x", padx=10, pady=(0, 15))
    
        # Input field for the item
        tk.Label(input_frame, text="Item:", bg=theme()["CARD"]).grid(row=0, column=0, sticky="w", padx=5)
        item_entry = tk.Entry(input_frame)
        item_entry.grid(row=1, column=0, sticky="ew", padx=5)
    
        # Input field for quantity
        tk.Label(input_frame, text="Qty:", bg=theme()["CARD"]).grid(row=0, column=1, sticky="w", padx=5)
        quantity_entry = tk.Entry(input_frame, width=10)
        quantity_entry.grid(row=1, column=1, padx=5)

        # Input field for unit (mostly for inventory)
        tk.Label(input_frame, text="Unit:", bg=theme()["CARD"]).grid(row=0, column=2, sticky="w", padx=5)
        unit_entry = tk.Entry(input_frame, width=8)
        unit_entry.insert(0, "e.g., cans") # Hint for the user
        unit_entry.grid(row=1, column=2, padx=5)

        # Radio Buttons for Destination
        radio_frame = tk.Frame(input_frame, bg=theme()["CARD"])
        radio_frame.grid(row=1, column=3, sticky="nsw", padx=10)
    
        tk.Radiobutton(radio_frame, text="Add to Shopping List", 
                        variable=list_destination, value=0, 
                        bg=theme()["CARD"],
                        selectcolor=theme()["CARD"], # 💡 FIX 3: Makes the background *behind* the circle blend in
                        activebackground=theme()["CARD"] # 💡 FIX 3: Ensures no color change on hover/click
                        ).pack(anchor="w")

        tk.Radiobutton(radio_frame, text="Add to Inventory", 
                        variable=list_destination, value=1, 
                        bg=theme()["CARD"],
                        selectcolor=theme()["CARD"], # 💡 FIX 3: Makes the background *behind* the circle blend in
                        activebackground=theme()["CARD"] # 💡 FIX 3: Ensures no color change on hover/click
                        ).pack(anchor="w")

        # Add button
        tk.Button(input_frame, text="Add Item", command=add_item, bg=theme()["ACCENT"]).grid(row=1, column=4, padx=10)
        input_frame.grid_columnconfigure(0, weight=1) # Make item entry expand

        # 2. Main Content Containers (Side-by-Side)
        main_content_frame = tk.Frame(pg, bg=theme()["BG"])
        main_content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # --- Left Column: Shopping List (NEED) ---
        shopping_container = tk.Frame(main_content_frame, bg=theme()["CARD"], padx=10, pady=10)
        shopping_container.pack(side="left", fill="both", expand=True, padx=(0, 5))
    
        tk.Label(shopping_container, text="🛒 NEED TO BUY (Shopping List)", font=("Segoe UI", 12, "bold"), bg=theme()["CARD"]).pack(pady=5)
    
        # Frame for the actual list items
        shopping_list_frame = tk.Frame(shopping_container, bg=theme()["CARD"])
        shopping_list_frame.pack(fill="both", expand=True) 

        # --- Right Column: Inventory (HAVE) ---
        inventory_container = tk.Frame(main_content_frame, bg=theme()["CARD"], padx=10, pady=10)
        inventory_container.pack(side="right", fill="both", expand=True, padx=(5, 0))
    
        tk.Label(inventory_container, text="🏠 ITEMS I HAVE (Inventory)", font=("Segoe UI", 12, "bold"), bg=theme()["CARD"]).pack(pady=5)

        # Frame for the actual inventory items
        inventory_list_frame = tk.Frame(inventory_container, bg=theme()["CARD"])
        inventory_list_frame.pack(fill="both", expand=True)

        # 3. Management Button (Clear Purchased)
        tk.Button(pg, text="Clear ALL Purchased Items", command=lambda: print("Clear Purchased Logic Here"), bg=theme()["ACCENT"], fg="white").pack(pady=10)
    
        # --- Initial Load ---
        pg.load_shopping_list = load_shopping_list
        pg.load_inventory = load_inventory
        pg.load_shopping_list()
        pg.load_inventory()
        
        
    # HYPERLINKS PAGE
    if pn == "Hyperlinks":
        import webbrowser
        from datetime import date
        import tkinter as tk
        from tkinter import messagebox

        pg.configure(bg=theme()["BG"])

        # --- CREATE TABLE IF NOT EXISTS ---
        run_query("""
            CREATE TABLE IF NOT EXISTS hyperlinks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                category TEXT,
                date_added TEXT
            )
        """)

        # --- Variables ---
        link_title_var = tk.StringVar()
        link_url_var = tk.StringVar()
        categories = ["Work", "Learning", "Reference", "Personal", "Entertainment", "Other"]
        link_category_var = tk.StringVar(value=categories[0])

        # --- Helper UI Function ---
        def styled_label(master, text, size=14, weight="bold", pady=(10, 5)):
            label = tk.Label(master, text=text, bg=theme()["BG"], fg=theme()["TEXT"],
                            font=("Segoe UI", size, weight), anchor="w")
            label.pack(fill="x", padx=15, pady=pady)
            return label

        # --- Header ---
        styled_label(pg, "🔗 Hyperlinks")

        # --- Functions ---
        def load_hyperlinks():
            """Fetch and display all saved links grouped by category."""
            rows = run_query("SELECT id, title, url, category FROM hyperlinks ORDER BY category, title")
            hyperlink_listbox.delete(0, tk.END)

            if not rows:
                hyperlink_listbox.insert(tk.END, "No links saved yet.")
                hyperlink_listbox.itemconfig(tk.END, {'fg': 'gray'})
                return

            current_category = None
            for row in rows:
                link_id, title, url, category = row
                if category != current_category:
                    hyperlink_listbox.insert(tk.END, f"--- {category.upper()} ---")
                    hyperlink_listbox.itemconfig(tk.END, {'bg': theme()["ACCENT"], 'fg': 'white'})
                    current_category = category
                hyperlink_listbox.insert(tk.END, f"  {title}: {url}")

        def add_hyperlink():
            """Save a new link to the database."""
            title = link_title_var.get().strip()
            url = link_url_var.get().strip()
            category = link_category_var.get()

            if not title or not url:
                messagebox.showwarning("Missing Data", "Please enter both a Title and a URL.")
                return

            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            try:
                run_query(
                    "INSERT INTO hyperlinks (title, url, category, date_added) VALUES (?, ?, ?, ?)",
                    (title, url, category, date.today().isoformat())
                )
                link_title_var.set("")
                link_url_var.set("")
                load_hyperlinks()
                messagebox.showinfo("Saved", f"Link '{title}' saved successfully.")
            except Exception as e:
                messagebox.showerror("Database Error", f"Could not save link:\n{e}")

        def open_link(event):
            """Open selected link in default browser."""
            try:
                index = hyperlink_listbox.curselection()[0]
                line_text = hyperlink_listbox.get(index)
                if line_text.startswith("---") or line_text.startswith("No "):
                    return
                if ":" in line_text:
                    url = line_text.split(":", 1)[1].strip()
                    webbrowser.open_new(url)
            except IndexError:
                pass
            except Exception as e:
                messagebox.showerror("Error", f"Could not open link:\n{e}")

        # --- Add Link Form Frame ---
        form_frame = tk.Frame(pg, bg=theme()["CARD"], bd=1, relief="solid", padx=10, pady=10)
        form_frame.pack(fill="x", padx=15, pady=(5, 10))

        tk.Label(form_frame, text="Title:", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=0, column=0, sticky="w", padx=5)
        tk.Entry(form_frame, textvariable=link_title_var, width=30, bg=theme()["BG"], fg=theme()["TEXT"]).grid(row=0, column=1, padx=5)

        tk.Label(form_frame, text="URL:", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=1, column=0, sticky="w", padx=5)
        tk.Entry(form_frame, textvariable=link_url_var, width=30, bg=theme()["BG"], fg=theme()["TEXT"]).grid(row=1, column=1, padx=5)

        tk.Label(form_frame, text="Category:", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=0, column=2, sticky="w", padx=5)
        category_menu = tk.OptionMenu(form_frame, link_category_var, *categories)
        category_menu.config(bg=theme()["BG"], fg=theme()["TEXT"], width=12)
        category_menu["menu"].config(bg=theme()["CARD"], fg=theme()["TEXT"])
        category_menu.grid(row=0, column=3, padx=5)

        tk.Button(form_frame, text="Save Link", command=add_hyperlink,
                bg=theme()["ACCENT"], fg="white", relief="flat", padx=10, pady=3).grid(row=1, column=3, padx=5, sticky="w")

        # --- List Display ---
        list_frame = tk.Frame(pg, bg=theme()["BG"], padx=10, pady=10)
        list_frame.pack(fill="both", expand=True, padx=15, pady=10)

        hyperlink_listbox = tk.Listbox(list_frame, height=15, bg=theme()["CARD"], fg=theme()["TEXT"],
                                    selectmode=tk.SINGLE, font=("Segoe UI", 10))
        hyperlink_listbox.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=hyperlink_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        hyperlink_listbox.config(yscrollcommand=scrollbar.set)

        hyperlink_listbox.bind("<Double-1>", open_link)

        # --- Load Data on Start ---
        load_hyperlinks()

        # --- Attach UI Update Function ---
        def hyperlink_update_ui():
            load_hyperlinks()

        pg.update_ui = hyperlink_update_ui
        
    # PERIOD TRACKER PAGE
    if pn == "Period":
        
        # --- Globalize necessary variables and current state ---
        global period_start_date_entry, period_end_date_entry, cycle_listbox, summary_text
        global current_period_id
        current_period_id = None # Tracks the period selected for editing/deleting
    
        # --- Functions (Defined first for use by buttons/bindings) ---
        
        def load_period_for_editing(event):
            """Loads selected period dates into the entry widgets and sets current_period_id."""
            global current_period_id
            try:
                # 1. Get ID from selected listbox item
                index = cycle_listbox.curselection()[0]
                listbox_text = cycle_listbox.get(index)
                
                # Format: ID|Start Date|...
                period_id_str = listbox_text.split("|", 1)[0]
                current_period_id = int(period_id_str)

                # 2. Fetch full record
                conn = db_connect()
                c = conn.cursor()
                row = c.execute("SELECT start_date, end_date FROM periods WHERE id = ?", (current_period_id,)).fetchone()
                conn.close()

                # 3. Update date entries
                if row:
                    start_date_str, end_date_str = row
                    period_start_date_entry.set_date(date.fromisoformat(start_date_str))
                    
                    if end_date_str:
                        period_end_date_entry.set_date(date.fromisoformat(end_date_str))
                    else:
                        # Default end date to start date if not logged
                        period_end_date_entry.set_date(date.fromisoformat(start_date_str))
                        
            except IndexError:
                current_period_id = None
                pass
            except Exception as e:
                messagebox.showerror("Load Error", f"Failed to load period: {e}")

        def log_or_update_period():
            """Inserts a new record or updates the selected record based on current_period_id."""
            start_date_obj = period_start_date_entry.get_date()
            end_date_obj = period_end_date_entry.get_date()
            
            start_date_str = start_date_obj.strftime("%Y-%m-%d")
            end_date_str = end_date_obj.strftime("%Y-%m-%d")
            
            global current_period_id

            if end_date_obj < start_date_obj:
                 messagebox.showwarning("Invalid Dates", "End date cannot be before start date.")
                 return

            conn = db_connect()
            c = conn.cursor()
            
            if current_period_id is None:
                # LOG NEW PERIOD
                try:
                    c.execute("INSERT INTO periods (start_date, end_date) VALUES (?, ?)", (start_date_str, end_date_str))
                    messagebox.showinfo("Success", f"New period logged.")
                except sqlite3.IntegrityError:
                    messagebox.showwarning("Duplicate", "A period start date already exists for this date.")
            else:
                # UPDATE EXISTING PERIOD
                c.execute("UPDATE periods SET start_date = ?, end_date = ? WHERE id = ?", (start_date_str, end_date_str, current_period_id))
                messagebox.showinfo("Success", f"Period ID {current_period_id} updated.")
                current_period_id = None # Clear selected ID after update
            
            conn.commit()
            conn.close()
            calculate_cycle_data()

        def delete_period():
            """Deletes the currently selected period."""
            global current_period_id
            if current_period_id is None:
                messagebox.showwarning("No Selection", "Please select a period from the list to delete.")
                return
            
            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this period record?"):
                conn = db_connect()
                c = conn.cursor()
                c.execute("DELETE FROM periods WHERE id = ?", (current_period_id,))
                conn.commit()
                conn.close()
                current_period_id = None
                calculate_cycle_data()
                messagebox.showinfo("Deleted", "Period record removed.")

        def update_summary(num_cycles, avg_cycle, avg_period, predicted_date, fertile_window):
            """Updates the prediction summary text box."""
            summary_text.config(state="normal")
            summary_text.delete("1.0", tk.END)
            
            summary_output = f"Cycles Tracked: {num_cycles}\n"
            summary_output += f"Avg. Cycle Length: {avg_cycle} days\n"
            summary_output += f"Avg. Period Length: {avg_period} days\n\n"
            
            if predicted_date:
                summary_output += "--- NEXT PREDICTION ---\n"
                summary_output += f"Predicted Start: {predicted_date.strftime('%Y-%m-%d')}\n"
                
                if fertile_window:
                    start_str = fertile_window[0].strftime('%Y-%m-%d')
                    end_str = fertile_window[1].strftime('%Y-%m-%d')
                    summary_output += f"Fertile Window:\n{start_str} to {end_str}"
            else:
                 summary_output += "\nLog at least two periods to enable full predictions."
            
            summary_text.insert("1.0", summary_output)
            summary_text.config(state="disabled")

        def calculate_cycle_data():
            """Fetches all period dates, calculates period/cycle lengths, and updates UI."""
            conn = db_connect()
            c = conn.cursor()
            rows = c.execute("SELECT id, start_date, end_date FROM periods ORDER BY start_date ASC").fetchall()
            conn.close()

            # Separate lists for calculations
            start_dates = [date.fromisoformat(row[1]) for row in rows]
            period_lengths = [] # Duration of bleeding
            cycle_lengths = [] # Start date to next Start date
            
            cycle_listbox.delete(0, tk.END)
            
            if len(rows) < 1:
                update_summary(0, 0, 0, None, None)
                return

            # Calculate and display history
            for i, row in enumerate(rows):
                period_id, start_date_str, end_date_str = row
                start_date_obj = start_dates[i]
                
                # 1. Period Length (Start to End)
                period_length_display = "?"
                if end_date_str:
                    period_length = (date.fromisoformat(end_date_str) - start_date_obj).days + 1
                    period_lengths.append(period_length)
                    period_length_display = f"{period_length} days"
                
                # 2. Cycle Length (Start to next Start)
                cycle_length_display = "N/A"
                if i < len(start_dates) - 1:
                    cycle_length = (start_dates[i+1] - start_dates[i]).days
                    cycle_lengths.append(cycle_length)
                    cycle_length_display = f"{cycle_length} days"
                
                listbox_item = f"{period_id}|{start_date_str} | Period: {period_length_display} | Cycle: {cycle_length_display}"
                cycle_listbox.insert(tk.END, listbox_item)

            # Calculate averages 
            avg_cycle = round(sum(cycle_lengths) / len(cycle_lengths)) if cycle_lengths else 0
            avg_period = round(sum(period_lengths) / len(period_lengths)) if period_lengths else 0
            
            # Prediction
            predicted_next_start = None
            predicted_fertile_window = None
            if avg_cycle > 0 and start_dates:
                last_period = start_dates[-1]
                predicted_next_start = last_period + timedelta(days=avg_cycle)
                
                # Fertile Window Prediction: Starts 17 days before the end of the average cycle, lasts about 6 days.
                # Calculation: Ovulation is ~14 days before the NEXT period start.
                ovulation_day = predicted_next_start - timedelta(days=14)
                fertile_start = ovulation_day - timedelta(days=5) 
                fertile_end = ovulation_day + timedelta(days=1)   # Fertile window is usually 6 days (5 before + day of ovulation)
                
                predicted_fertile_window = (fertile_start, fertile_end)

            update_summary(len(cycle_lengths), avg_cycle, avg_period, predicted_next_start, predicted_fertile_window)
        
        # 1. Page Header
        tk.Label(content, text="🩸 Period Tracker", 
                 font=("Segoe UI", 16, "bold"), 
                 bg=theme()["CARD"], fg=theme()["TEXT"], 
                 pady=10).pack(fill="x", padx=10, anchor="nw")
        
        # --- Main Frame for Logging and Summary ---
        main_frame = tk.Frame(content, bg=theme()["BG"])
        main_frame.pack(fill="x", padx=10, pady=10)
        
        # LOGGING SECTION (LEFT)
        log_frame = tk.Frame(main_frame, bg=theme()["CARD"], padx=10, pady=10)
        log_frame.pack(side="left", fill="y", padx=(0, 10))
        
        tk.Label(log_frame, text="Log/Edit Period Dates:", bg=theme()["CARD"], fg=theme()["TEXT"], font=("Segoe UI", 10, "bold")).pack(pady=5)
        
        # Start Date Entry Widget
        tk.Label(log_frame, text="Period Start Date:", bg=theme()["CARD"], fg=theme()["TEXT"]).pack(pady=2)
        period_start_date_entry = DateEntry(log_frame, width=12, date_pattern='yyyy-mm-dd', selectmode='day', background=theme()["ACCENT"], foreground='white')
        period_start_date_entry.set_date(date.today())
        period_start_date_entry.pack(pady=2)

        # End Date Entry Widget
        tk.Label(log_frame, text="Period End Date:", bg=theme()["CARD"], fg=theme()["TEXT"]).pack(pady=2)
        period_end_date_entry = DateEntry(log_frame, width=12, date_pattern='yyyy-mm-dd', selectmode='day', background=theme()["ACCENT"], foreground='white')
        period_end_date_entry.set_date(date.today() + timedelta(days=5))
        period_end_date_entry.pack(pady=2)
        
        # Log/Update Button
        tk.Button(log_frame, text="Log/Update Period", command=log_or_update_period, 
                  bg=theme()["ACCENT"], fg="white").pack(pady=10)
        
        # Delete Button
        tk.Button(log_frame, text="Delete Selected", command=delete_period, 
                  bg="#ffb3b3", fg="white").pack(pady=5)
        
        # CYCLE HISTORY LIST (CENTER)
        list_frame = tk.Frame(main_frame, bg=theme()["CARD"], padx=10, pady=10)
        list_frame.pack(side="left", fill="both", expand=True, padx=10)
        
        tk.Label(list_frame, text="Cycle History (Select to Edit):", bg=theme()["CARD"], fg=theme()["TEXT"], font=("Segoe UI", 10, "bold")).pack(pady=5, anchor="w")
        
        cycle_listbox = tk.Listbox(list_frame, height=10, width=50, bg=theme()["BG"], fg=theme()["TEXT"], selectmode=tk.SINGLE)
        cycle_listbox.pack(fill="both", expand=True)

        # PREDICTION SUMMARY (RIGHT)
        summary_frame = tk.Frame(main_frame, bg=theme()["CARD"], padx=10, pady=10)
        summary_frame.pack(side="left", fill="y")
        
        tk.Label(summary_frame, text="Cycle Prediction Summary:", bg=theme()["CARD"], fg=theme()["TEXT"], font=("Segoe UI", 10, "bold")).pack(pady=5)

        summary_text = tk.Text(summary_frame, wrap="word", font=("Segoe UI", 10), height=10, width=35,
                               bg=theme()["BG"], fg=theme()["TEXT"], state="disabled") 
        summary_text.pack(pady=5, padx=5)

        
        # --- Bindings and Initial Load ---
        cycle_listbox.bind("<<ListboxSelect>>", load_period_for_editing)
        calculate_cycle_data()
        
        # Attach Update Function
        def period_update_ui():
            calculate_cycle_data()
        
        pg.update_ui = period_update_ui
        pg.update_ui()
    
    # WEIGHT TRACKER PAGE
    if pn == "Weight":
        import tkinter as tk
        from tkinter import messagebox
        from tkcalendar import DateEntry
        import sqlite3
        from datetime import date
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        import matplotlib.dates as mdates

        # --- Globals ---
        global metric_date_entry, metric_weight_var, metric_fat_var, metric_muscle_var
        global metric_bmr_var, metric_skm_var, metric_bfm_var, metric_bmi_var
        global metric_whr_var, metric_vfl_var, metric_tbw_var, metric_protein_var, metric_mineral_var
        global metric_listbox, metric_summary_text, metric_chart_frame
        global current_metric_id

        current_metric_id = None

        # --- Tk Variables ---
        metric_weight_var = tk.StringVar()
        metric_fat_var = tk.StringVar()
        metric_muscle_var = tk.StringVar()
        metric_bmr_var = tk.StringVar()
        metric_skm_var = tk.StringVar()
        metric_bfm_var = tk.StringVar()
        metric_bmi_var = tk.StringVar()
        metric_whr_var = tk.StringVar()
        metric_vfl_var = tk.StringVar()
        metric_tbw_var = tk.StringVar()
        metric_protein_var = tk.StringVar()
        metric_mineral_var = tk.StringVar()

        # --- FUNCTIONS ---

        def load_metric_for_editing(event):
            """Load selected entry into input fields."""
            global current_metric_id
            try:
                index = metric_listbox.curselection()[0]
                listbox_text = metric_listbox.get(index)
                metric_id_str = listbox_text.split("|", 1)[0]
                current_metric_id = int(metric_id_str)

                conn = db_connect()
                c = conn.cursor()
                row = c.execute("SELECT * FROM metrics WHERE id = ?", (current_metric_id,)).fetchone()
                conn.close()

                if row:
                    values = row[1:]
                    metric_date_entry.set_date(date.fromisoformat(values[0]))
                    metric_weight_var.set(values[1] or "")
                    metric_fat_var.set(values[2] or "")
                    metric_muscle_var.set(values[3] or "")
                    metric_bmr_var.set(values[4] or "")
                    metric_skm_var.set(values[5] or "")
                    metric_bfm_var.set(values[6] or "")
                    metric_bmi_var.set(values[7] or "")
                    metric_whr_var.set(values[8] or "")
                    metric_vfl_var.set(values[9] or "")
                    metric_tbw_var.set(values[10] or "")
                    metric_protein_var.set(values[11] or "")
                    metric_mineral_var.set(values[12] or "")
            except Exception:
                current_metric_id = None

        def log_or_update_metric():
            """Insert new or update existing metric entry."""
            global current_metric_id
            date_str = metric_date_entry.get_date().strftime("%Y-%m-%d")

            def safe_float(val):
                try:
                    return float(val) if val.strip() else None
                except:
                    return None

            data = [
                date_str,
                safe_float(metric_weight_var.get()),
                safe_float(metric_fat_var.get()),
                safe_float(metric_muscle_var.get()),
                safe_float(metric_bmr_var.get()),
                safe_float(metric_skm_var.get()),
                safe_float(metric_bfm_var.get()),
                safe_float(metric_bmi_var.get()),
                safe_float(metric_whr_var.get()),
                safe_float(metric_vfl_var.get()),
                safe_float(metric_tbw_var.get()),
                safe_float(metric_protein_var.get()),
                safe_float(metric_mineral_var.get())
            ]

            conn = db_connect()
            c = conn.cursor()

            if current_metric_id is None:
                # Insert
                c.execute("""
                    INSERT INTO metrics (
                        date, weight, body_fat_percent, muscle_mass, basal_metabolic_rate,
                        skeletal_muscle_mass, body_fat_mass, bmi, waist_hip_ratio,
                        visceral_fat_level, total_body_water, protein, mineral
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, data)
                messagebox.showinfo("Success", f"New metric logged for {date_str}.")
            else:
                # Update
                c.execute("""
                    UPDATE metrics SET
                        date = ?, weight = ?, body_fat_percent = ?, muscle_mass = ?,
                        basal_metabolic_rate = ?, skeletal_muscle_mass = ?, body_fat_mass = ?,
                        bmi = ?, waist_hip_ratio = ?, visceral_fat_level = ?,
                        total_body_water = ?, protein = ?, mineral = ?
                    WHERE id = ?
                """, data + [current_metric_id])
                messagebox.showinfo("Success", f"Updated metric for {date_str}.")
                current_metric_id = None

            conn.commit()
            conn.close()
            clear_fields()
            load_data_and_update_ui()

        def delete_metric():
            global current_metric_id
            if not current_metric_id:
                messagebox.showwarning("No Selection", "Select an entry to delete.")
                return
            if messagebox.askyesno("Confirm Delete", "Delete this metric entry?"):
                conn = db_connect()
                c = conn.cursor()
                c.execute("DELETE FROM metrics WHERE id = ?", (current_metric_id,))
                conn.commit()
                conn.close()
                current_metric_id = None
                load_data_and_update_ui()
                messagebox.showinfo("Deleted", "Metric entry removed.")

        def clear_fields():
            metric_weight_var.set("")
            metric_fat_var.set("")
            metric_muscle_var.set("")
            metric_bmr_var.set("")
            metric_skm_var.set("")
            metric_bfm_var.set("")
            metric_bmi_var.set("")
            metric_whr_var.set("")
            metric_vfl_var.set("")
            metric_tbw_var.set("")
            metric_protein_var.set("")
            metric_mineral_var.set("")

        def draw_chart(dates, weights, body_fats):
            for widget in metric_chart_frame.winfo_children():
                widget.destroy()

            if not dates or not weights:
                tk.Label(metric_chart_frame, text="No chart data yet. Log at least one weight entry.",
                        bg=theme()["CARD"], fg=theme()["TEXT"]).pack(expand=True, fill="both")
                return

            fig = Figure(figsize=(5, 3), dpi=100)
            ax1 = fig.add_subplot(111)

            ax1.set_facecolor(theme()["CARD"])
            fig.patch.set_facecolor(theme()["CARD"])
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax1.tick_params(axis='x', rotation=30, colors=theme()["TEXT"])
            ax1.tick_params(axis='y', colors=theme()["TEXT"])
            ax1.grid(True, linestyle='--', alpha=0.6)

            # Plot weight
            ax1.plot(dates, weights, color=theme()["ACCENT"], marker='o', label='Weight (kg)', linestyle='-')
            ax1.set_ylabel('Weight (kg)', color=theme()["TEXT"])
            ax1.legend(loc='upper left', frameon=False)

            # Plot body fat %
            valid_bf = [(d, bf) for d, bf in zip(dates, body_fats) if bf is not None]
            if valid_bf:
                bf_dates, bf_vals = zip(*valid_bf)
                ax2 = ax1.twinx()
                ax2.plot(bf_dates, bf_vals, color='orange', marker='x', label='Body Fat (%)', linestyle='--')
                ax2.set_ylabel('Body Fat (%)', color=theme()["TEXT"])
                ax2.legend(loc='upper right', frameon=False)

            canvas = FigureCanvasTkAgg(fig, master=metric_chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

        def update_summary_display(dates, weights, body_fats, muscles, bf_masses):
            metric_summary_text.config(state="normal")
            metric_summary_text.delete("1.0", tk.END)

            if not weights:
                metric_summary_text.insert("1.0", "No data logged yet.")
            else:
                start = weights[0]
                end = weights[-1]
                diff = end - start
                muscle = muscles[-1] if muscles else "N/A"
                bf_mass = bf_masses[-1] if bf_masses else "N/A"
                summary = (
                    f"Latest Weight: {end:.1f} kg\n"
                    f"Muscle Mass: {muscle if muscle != 'N/A' else 'N/A'} kg\n"
                    f"Body Fat Mass: {bf_mass if bf_mass != 'N/A' else 'N/A'} kg\n"
                    f"Change: {diff:.1f} kg ({'Loss' if diff < 0 else 'Gain'})"
                )
                metric_summary_text.insert("1.0", summary)
            metric_summary_text.config(state="disabled")

        def load_data_and_update_ui():
            conn = db_connect()
            c = conn.cursor()
            rows = c.execute("SELECT id, date, weight, body_fat_percent, muscle_mass, body_fat_mass FROM metrics ORDER BY date ASC").fetchall()
            conn.close()

            metric_listbox.delete(0, tk.END)
            dates, weights, body_fats, muscles, bf_masses = [], [], [], [], []

            for row in rows:
                mid, d, w, bf, m, bfm = row
                display = f"{mid}|{d} - W: {w if w else 'N/A'} kg, BF: {bf if bf else 'N/A'}%"
                metric_listbox.insert(tk.END, display)
                try:
                    if w is not None:
                        dates.append(date.fromisoformat(d))
                        weights.append(float(w))
                        body_fats.append(float(bf) if bf is not None else None)
                        muscles.append(m)
                        bf_masses.append(bfm)
                except:
                    continue

            update_summary_display(dates, weights, body_fats, muscles, bf_masses)
            draw_chart(dates, weights, body_fats)

        # --- UI ---
        tk.Label(content, text="⚖️ Weight & Body Metrics",
                font=("Segoe UI", 16, "bold"),
                bg=theme()["CARD"], fg=theme()["TEXT"],
                pady=10).pack(fill="x", padx=10, anchor="nw")

        main_frame = tk.Frame(content, bg=theme()["BG"])
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left Panel
        left_panel = tk.Frame(main_frame, bg=theme()["CARD"], padx=10, pady=10)
        left_panel.pack(side="left", fill="y", padx=(0, 10))

        tk.Label(left_panel, text="Log New Measurement:", bg=theme()["CARD"], fg=theme()["TEXT"], font=("Segoe UI", 10, "bold")).pack(pady=5)

        form_canvas = tk.Canvas(left_panel, bg=theme()["CARD"], height=400, highlightthickness=0)
        form_canvas.pack(fill="y", expand=True)
        form_frame = tk.Frame(form_canvas, bg=theme()["CARD"])
        form_canvas.create_window((0, 0), window=form_frame, anchor="nw")
        form_frame.bind("<Configure>", lambda e: form_canvas.configure(scrollregion=form_canvas.bbox("all")))

        # Date Entry
        tk.Label(form_frame, text="Date:", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=0, column=0, sticky="w")
        metric_date_entry = DateEntry(form_frame, width=12, date_pattern='yyyy-mm-dd')
        metric_date_entry.set_date(date.today())
        metric_date_entry.grid(row=0, column=1, padx=5, pady=2)

        fields = [
            ("Weight (kg):", metric_weight_var),
            ("Body Fat (%):", metric_fat_var),
            ("Muscle (kg):", metric_muscle_var),
            ("BMR:", metric_bmr_var),
            ("SKM (kg):", metric_skm_var),
            ("BFM (kg):", metric_bfm_var),
            ("BMI:", metric_bmi_var),
            ("WHR:", metric_whr_var),
            ("VFL:", metric_vfl_var),
            ("TBW:", metric_tbw_var),
            ("Protein:", metric_protein_var),
            ("Mineral:", metric_mineral_var),
        ]

        for i, (label, var) in enumerate(fields, start=1):
            tk.Label(form_frame, text=label, bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=i, column=0, sticky="w", pady=2)
            tk.Entry(form_frame, textvariable=var, width=15, bg=theme()["BG"], fg=theme()["TEXT"]).grid(row=i, column=1, padx=5, pady=2)

        tk.Button(left_panel, text="Log/Update Entry", command=log_or_update_metric, bg=theme()["ACCENT"], fg="white").pack(pady=10)
        tk.Button(left_panel, text="Delete Selected Entry", command=delete_metric, bg="#ecadad", fg="white").pack(pady=5)

        tk.Label(left_panel, text="History (Select to Edit):", bg=theme()["CARD"], fg=theme()["TEXT"], font=("Segoe UI", 10, "bold")).pack(pady=(15, 5))
        metric_listbox = tk.Listbox(left_panel, height=10, width=40, bg=theme()["BG"], fg=theme()["TEXT"], selectmode=tk.SINGLE)
        metric_listbox.pack(pady=5, padx=5, fill="x")

        # Right Panel
        right_panel = tk.Frame(main_frame, bg=theme()["BG"], padx=10, pady=10)
        right_panel.pack(side="right", fill="both", expand=True)

        tk.Label(right_panel, text="Progress Chart (Weight & Body Fat %)", bg=theme()["BG"], fg=theme()["TEXT"], font=("Segoe UI", 10, "bold")).pack(pady=5, anchor="nw")
        metric_chart_frame = tk.Frame(right_panel, bg=theme()["CARD"], height=250)
        metric_chart_frame.pack(fill="x", expand=False, pady=5)

        tk.Label(right_panel, text="Summary Metrics:", bg=theme()["BG"], fg=theme()["TEXT"], font=("Segoe UI", 10, "bold")).pack(pady=(15, 5), anchor="nw")
        metric_summary_text = tk.Text(right_panel, wrap="word", font=("Segoe UI", 10), height=5, width=40, bg=theme()["CARD"], fg=theme()["TEXT"], state="disabled")
        metric_summary_text.pack(fill="x", expand=False, padx=5)

        # Bindings + Load
        metric_listbox.bind("<<ListboxSelect>>", load_metric_for_editing)

        def metric_update_ui():
            load_data_and_update_ui()

        pg.update_ui = metric_update_ui
        pg.update_ui()
        
    # Calories Page
    if pn == "Calories":
        import tkinter as tk
        from tkinter import ttk, messagebox, simpledialog
        from datetime import date, datetime, timedelta
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        import matplotlib.dates as mdates

        # --- Clear previous page ---
        for widget in pg.winfo_children():
            widget.destroy()

        # --- GLOBAL VARIABLES ---
        global food_entry, cal_entry, cal_entry_frame, cal_summary_frame, cal_summary_history_frame, cal_chart_container, current_cal_date
        current_cal_date = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))

        # --- Ensure table exists ---
        run_query("""
        CREATE TABLE IF NOT EXISTS calorie_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            food TEXT NOT NULL,
            calories INTEGER NOT NULL
        )
        """)

        # --- Page Title ---
        tk.Label(pg, text="🍎 Calorie Tracker", font=("Segoe UI", 16, "bold"), bg=theme()["BG"]).pack(pady=10)

        # --- UTILITY FUNCTIONS ---
        def get_calorie_trend():
            rows = run_query("SELECT date, SUM(calories) FROM calorie_log GROUP BY date ORDER BY date ASC")
            return rows if rows else []

        def load_calorie_summary(target_date):
            """Load daily entries into the summary frame."""
            global cal_summary_frame
            for widget in cal_summary_frame.winfo_children():
                widget.destroy()

            rows = run_query("SELECT id, food, calories FROM calorie_log WHERE date = ?", (target_date,))
            total = 0

            if rows:
                for rid, food, cal in rows:
                    entry_frame = tk.Frame(cal_summary_frame, bg=theme()["BG"])
                    entry_frame.pack(fill="x", padx=15, pady=2)

                    # Food + Calorie Label
                    tk.Label(entry_frame, text=f"{food}: {cal} kcal", bg=theme()["BG"], fg=theme()["TEXT"]).pack(side="left")

                    # Edit Button
                    tk.Button(
                        entry_frame, text="✏️", bg=theme()["BTN"], command=lambda r=rid: edit_calorie_entry(r, target_date),
                        relief="flat", padx=6
                    ).pack(side="right", padx=2)

                    # Delete Button
                    tk.Button(
                        entry_frame, text="🗑️", bg=theme()["BTN"], command=lambda r=rid: delete_calorie_entry(r, target_date),
                        relief="flat", padx=6
                    ).pack(side="right")

                    total += cal

                tk.Label(cal_summary_frame, text=f"Total: {total:.0f} kcal", font=("Segoe UI", 12, "bold"),
                        bg=theme()["BG"], fg=theme()["TEXT"]).pack(pady=5)
            else:
                tk.Label(cal_summary_frame, text=f"No entries for {target_date}", bg=theme()["BG"]).pack(pady=5)

        def plot_calorie_trend():
            """Plot trend chart of daily totals."""
            global cal_chart_container
            for widget in cal_chart_container.winfo_children():
                widget.destroy()

            trend = get_calorie_trend()
            if not trend:
                tk.Label(cal_chart_container, text="No calorie history yet.", bg=theme()["BG"], fg="gray").pack(pady=10)
                return

            dates = [datetime.strptime(row[0], "%Y-%m-%d") for row in trend]
            values = [row[1] for row in trend]

            fig = Figure(figsize=(5, 2.5), dpi=100)
            ax = fig.add_subplot(111)

            # Pastel pink styling
            fig.patch.set_facecolor("#fdeef4")
            ax.set_facecolor("#fffafc")
            ax.plot(dates, values, color="#ff8fa3", linewidth=2, marker="o", markersize=6)
            ax.fill_between(dates, values, color="#ffd9e1", alpha=0.3)

            ax.set_title("Calorie Trend", fontsize=11, fontweight="bold")
            ax.set_ylabel("kcal", fontsize=9)
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
            ax.tick_params(axis='x', rotation=45, labelsize=8)
            ax.tick_params(axis='y', labelsize=8)

            if len(dates) == 1:
                ax.set_xlim(dates[0] - timedelta(days=1), dates[0] + timedelta(days=1))

            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=cal_chart_container)
            canvas.draw()
            canvas.get_tk_widget().pack(pady=10, fill="both", expand=True)

        def add_calorie_entry():
            """Add a new calorie entry for today."""
            food = food_entry.get().strip()
            cal_value = cal_entry.get().strip()
            today_str = date.today().strftime("%Y-%m-%d")

            if not food or not cal_value:
                messagebox.showwarning("Input Error", "Please fill out all fields.")
                return

            try:
                run_query("INSERT INTO calorie_log (date, food, calories) VALUES (?, ?, ?)",
                        (today_str, food, float(cal_value)))
                food_entry.delete(0, tk.END)
                cal_entry.delete(0, tk.END)
                load_calorie_summary(current_cal_date.get())
                plot_calorie_trend()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save entry: {e}")

        def edit_calorie_entry(entry_id, target_date):
            """Edit selected calorie entry."""
            row = run_query("SELECT food, calories FROM calorie_log WHERE id = ?", (entry_id,))
            if not row:
                messagebox.showerror("Error", "Entry not found.")
                return

            food, cal = row[0]
            new_food = simpledialog.askstring("Edit Food", "Food name:", initialvalue=food)
            if new_food is None:
                return

            new_calories = simpledialog.askinteger("Edit Calories", "Calories:", initialvalue=cal)
            if new_calories is None:
                return

            run_query("UPDATE calorie_log SET food = ?, calories = ? WHERE id = ?", (new_food, new_calories, entry_id))
            load_calorie_summary(target_date)
            plot_calorie_trend()

        def delete_calorie_entry(entry_id, target_date):
            """Delete selected calorie entry."""
            if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this entry?"):
                return

            run_query("DELETE FROM calorie_log WHERE id = ?", (entry_id,))
            load_calorie_summary(target_date)
            plot_calorie_trend()

        # --- UI LAYOUT ---
        cal_entry_frame = tk.Frame(pg, bg=theme()["BG"])
        cal_entry_frame.pack(side="left", fill="y", padx=10, pady=10)

        cal_summary_history_frame = tk.Frame(pg, bg=theme()["BG"], padx=15, pady=15)
        cal_summary_history_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Entry widgets
        tk.Label(cal_entry_frame, text="Food:", bg=theme()["BG"]).grid(row=0, column=0, padx=5, pady=5)
        food_entry = tk.Entry(cal_entry_frame, width=25)
        food_entry.grid(row=0, column=1, padx=5)

        tk.Label(cal_entry_frame, text="Calories:", bg=theme()["BG"]).grid(row=1, column=0, padx=5)
        cal_entry = tk.Entry(cal_entry_frame, width=10)
        cal_entry.grid(row=1, column=1, padx=5)

        tk.Button(cal_entry_frame, text="Add", command=add_calorie_entry, bg=theme()["ACCENT"]).grid(row=0, column=2, rowspan=2, padx=10)

        # Date selector
        date_selector_frame = tk.Frame(cal_summary_history_frame, bg=theme()["BG"])
        date_selector_frame.pack(fill="x", pady=(0, 5))

        tk.Label(date_selector_frame, text="Select Date:", bg=theme()["BG"], fg=theme()["TEXT"]).pack(side="left", padx=5)
        cal_date_view_entry = ttk.Entry(date_selector_frame, textvariable=current_cal_date, width=12)
        cal_date_view_entry.pack(side="left", padx=5)

        tk.Button(date_selector_frame, text="View", command=lambda: load_calorie_summary(current_cal_date.get()),
                bg=theme()["BTN"], fg=theme()["TEXT"], padx=5, pady=0).pack(side="left", padx=5)

        # Summary & chart
        tk.Label(cal_summary_history_frame, text="Daily Calorie Summary:", font=("Segoe UI", 12, "bold"),
                bg=theme()["BG"], fg=theme()["TEXT"]).pack(anchor="nw")

        cal_summary_frame = tk.Frame(cal_summary_history_frame, bg=theme()["BG"])
        cal_summary_frame.pack(fill="x")

        tk.Label(cal_summary_history_frame, text="Calorie Trend (History):", font=("Segoe UI", 12, "bold"),
                bg=theme()["BG"], fg=theme()["TEXT"]).pack(anchor="nw", pady=(15, 5))

        cal_chart_container = tk.Frame(cal_summary_history_frame, bg=theme()["BG"])
        cal_chart_container.pack(fill="both", expand=True)

        # --- Initial load ---
        load_calorie_summary(current_cal_date.get())
        plot_calorie_trend()

        # --- UI update hook ---
        def calories_update_ui():
            load_calorie_summary(current_cal_date.get())
            plot_calorie_trend()

        pg.update_ui = calories_update_ui
        
    # Goals Page    
    if pn == "Goals":
        
        # --- Globalize necessary variables ---
        global goal_title_var, goal_category_var, goal_date_entry, goal_listbox, goal_detail_text
        global current_goal_id
        current_goal_id = None # Tracks the goal currently selected
        
        # 1. Page Header
        tk.Label(content, text="🎯 Goals & Planning", 
                 font=("Segoe UI", 16, "bold"), 
                 bg=theme()["CARD"], fg=theme()["TEXT"], 
                 pady=10).pack(fill="x", padx=10, anchor="nw")
        
        # --- Main Content Frame (Side-by-Side Layout) ---
        main_frame = tk.Frame(content, bg=theme()["BG"])
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ----------------------------------------------------
        # LEFT PANEL: List and Add Form
        # ----------------------------------------------------
        
        left_panel = tk.Frame(main_frame, bg=theme()["CARD"], padx=10, pady=10)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        
        # --- Variables ---
        goal_title_var = tk.StringVar()
        categories = ["Career", "Health", "Financial", "Skill", "Personal", "Other"]
        goal_category_var = tk.StringVar(value=categories[0])
        
        # --- Listbox (Existing Goals) ---
        tk.Label(left_panel, text="Goal List:", bg=theme()["CARD"], fg=theme()["TEXT"], font=("Segoe UI", 10, "bold")).pack(pady=(0, 5))
        
        goal_listbox = tk.Listbox(left_panel, height=15, width=40, bg=theme()["BG"], fg=theme()["TEXT"], selectmode=tk.SINGLE)
        goal_listbox.pack(pady=(0, 10))
        
        # --- Add Goal Form Frame ---
        form_frame = tk.Frame(left_panel, bg=theme()["CARD"])
        form_frame.pack(pady=10, padx=5, fill="x")

        # Title
        tk.Label(form_frame, text="Title:", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=0, column=0, sticky="w", pady=2)
        tk.Entry(form_frame, textvariable=goal_title_var, width=25, bg=theme()["BG"], fg=theme()["TEXT"]).grid(row=0, column=1, padx=5, pady=2)
        
        # Category
        tk.Label(form_frame, text="Category:", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=1, column=0, sticky="w", pady=2)
        category_menu = tk.OptionMenu(form_frame, goal_category_var, *categories)
        category_menu.config(bg=theme()["BG"], fg=theme()["TEXT"], width=10)
        category_menu.grid(row=1, column=1, padx=5, pady=2)
        
        # Target Date
        tk.Label(form_frame, text="Target Date:", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=2, column=0, sticky="w", pady=2)
        goal_date_entry = DateEntry(form_frame, width=12, date_pattern='yyyy-mm-dd', selectmode='day', background=theme()["ACCENT"], foreground='white')
        goal_date_entry.set_date(date.today() + timedelta(days=30))
        goal_date_entry.grid(row=2, column=1, padx=5, pady=2, sticky="w")
        
        # Add Button (Function defined below)
        tk.Button(form_frame, text="Add Goal", command=lambda: add_new_goal(), 
                  bg=theme()["ACCENT"], fg="white").grid(row=3, column=0, columnspan=2, pady=10)
        
        # ----------------------------------------------------
        # RIGHT PANEL: Detail View and Tracking
        # ----------------------------------------------------
        
        right_panel = tk.Frame(main_frame, bg=theme()["BG"], padx=10, pady=10)
        right_panel.pack(side="right", fill="both", expand=True)

        tk.Label(right_panel, text="Goal Details & Progress:", bg=theme()["BG"], fg=theme()["TEXT"], font=("Segoe UI", 10, "bold")).pack(pady=(0, 5), anchor="w")
        
        # Detail Text Area (Displays description, progress, status, editable for description)
        goal_detail_text = tk.Text(right_panel, wrap="word", font=("Segoe UI", 10), height=15,
                                   bg=theme()["CARD"], fg=theme()["TEXT"], insertbackground=theme()["TEXT"],
                                   state="disabled") 
        goal_detail_text.pack(fill="x", expand=False) # Not expanding vertically so we can see tracking below
        
        # --- Tracking Frame ---
        tracking_frame = tk.Frame(right_panel, bg=theme()["BG"], pady=10)
        tracking_frame.pack(fill="x")
        
        tk.Label(tracking_frame, text="Update Progress (Value/Target):", bg=theme()["BG"], fg=theme()["TEXT"]).grid(row=0, column=0, sticky="w")
        
        # Progress Tracking Entry
        progress_value_var = tk.StringVar()
        progress_target_var = tk.StringVar()
        
        tk.Entry(tracking_frame, textvariable=progress_value_var, width=10, bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=0, column=1, padx=5)
        tk.Label(tracking_frame, text="/", bg=theme()["BG"], fg=theme()["TEXT"]).grid(row=0, column=2)
        tk.Entry(tracking_frame, textvariable=progress_target_var, width=10, bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=0, column=3, padx=5)
        
        # Update Button
        tk.Button(tracking_frame, text="Update Progress", command=lambda: update_goal_tracking(),
                  bg=theme()["ACCENT"], fg="white").grid(row=0, column=4, padx=10)

        # Status Buttons Frame
        status_frame = tk.Frame(right_panel, bg=theme()["BG"], pady=5)
        status_frame.pack(fill="x")

        tk.Button(status_frame, text="Mark Complete", command=lambda: update_goal_status('Completed'), 
                  bg="#3c9f5f", fg="white").pack(side="left", padx=5)
        
        tk.Button(status_frame, text="Mark Abandoned", command=lambda: update_goal_status('Abandoned'), 
                  bg="#e85f5f", fg="white").pack(side="left", padx=5)
        
        tk.Button(status_frame, text="Edit Description", command=lambda: goal_detail_text.config(state="normal"), 
                  bg=theme()["ACCENT"], fg="white").pack(side="right", padx=5)
        
        tk.Button(status_frame, text="Save Description", command=lambda: save_goal_description(), 
                  bg=theme()["ACCENT"], fg="white").pack(side="right", padx=5)
        
        
        # --- Functions ---
        
        def load_goals():
            """Loads goals into the listbox, highlighting by status."""
            conn = db_connect()
            c = conn.cursor()
            # Order: Active goals first, then by target date
            rows = c.execute("SELECT id, title, status FROM goals ORDER BY status DESC, target_date ASC").fetchall()
            conn.close()

            goal_listbox.delete(0, tk.END)
            for goal_id, title, status in rows:
                goal_listbox.insert(tk.END, f"{goal_id}|{status}|{title}") 
                
                # Apply color based on status
                if status == 'Completed':
                    goal_listbox.itemconfig(tk.END, {'bg': '#d4edda', 'fg': '#155724'}) # Light Green
                elif status == 'Abandoned':
                    goal_listbox.itemconfig(tk.END, {'bg': '#f8d7da', 'fg': '#721c24'}) # Light Red
                elif status == 'Active':
                    goal_listbox.itemconfig(tk.END, {'bg': theme()["CARD"], 'fg': theme()["TEXT"]})

        def display_goal_details(event):
            """Loads all goal details for the selected goal."""
            global current_goal_id
            
            try:
                index = goal_listbox.curselection()[0]
                listbox_text = goal_listbox.get(index)
                
                parts = listbox_text.split("|", 2)
                goal_id = int(parts[0])
                current_goal_id = goal_id
                
                conn = db_connect()
                c = conn.cursor()
                row = c.execute("SELECT title, description, category, target_date, current_progress, target_value, status FROM goals WHERE id = ?", (goal_id,)).fetchone()
                conn.close()

                if row:
                    title, description, category, target_date, current_progress, target_value, status = row
                    
                    # Calculate percentage progress
                    progress_percent = (current_progress / target_value) * 100 if target_value else 0
                    
                    # Format output
                    output = f"--- GOAL: {title.upper()} ---\n"
                    output += f"Category: {category}\n"
                    output += f"Target Date: {target_date}\n"
                    output += f"Status: {status}\n"
                    output += f"Progress: {current_progress} / {target_value} ({progress_percent:.0f}%)\n\n"
                    output += "--- DESCRIPTION ---\n"
                    output += description or "No description provided."

                    goal_detail_text.config(state="normal")
                    goal_detail_text.delete("1.0", tk.END)
                    goal_detail_text.insert("1.0", output)
                    goal_detail_text.config(state="disabled")
                    
                    # Update progress entry fields for easy editing
                    progress_value_var.set(str(current_progress))
                    progress_target_var.set(str(target_value))

            except IndexError:
                pass

        def add_new_goal():
            """Saves the minimal goal details from the form and updates the list."""
            title = goal_title_var.get().strip()
            category = goal_category_var.get()
            target_date = goal_date_entry.get_date().strftime("%Y-%m-%d")

            if not title:
                messagebox.showwarning("Missing Title", "Please enter a title for the new goal.")
                return

            conn = db_connect()
            c = conn.cursor()
            c.execute("INSERT INTO goals (title, description, category, target_date) VALUES (?, ?, ?, ?)", 
                      (title, "Describe your goal here...", category, target_date))
            conn.commit()
            conn.close()
            
            goal_title_var.set("")
            load_goals()
            messagebox.showinfo("Goal Added", f"Goal '{title}' added! Select it to add a description and progress target.")
        
        def save_goal_description():
            """Saves the editable description field."""
            global current_goal_id
            if current_goal_id is None:
                messagebox.showwarning("Error", "Please select a goal first.")
                return
            
            # Get the current text, removing the header part before '--- DESCRIPTION ---'
            full_text = goal_detail_text.get("1.0", tk.END)
            desc_marker = "--- DESCRIPTION ---\n"
            desc_start = full_text.find(desc_marker)
            
            if desc_start != -1:
                description = full_text[desc_start + len(desc_marker):].strip()
            else:
                description = full_text.strip()
            
            conn = db_connect()
            c = conn.cursor()
            c.execute("UPDATE goals SET description = ? WHERE id = ?", (description, current_goal_id))
            conn.commit()
            conn.close()
            
            goal_detail_text.config(state="disabled")
            display_goal_details(None)
            messagebox.showinfo("Saved", "Description updated.")

        def update_goal_tracking():
            """Updates current progress and target value."""
            global current_goal_id
            if current_goal_id is None:
                messagebox.showwarning("Error", "Please select a goal first.")
                return

            try:
                progress = float(progress_value_var.get())
                target = float(progress_target_var.get())
                
                conn = db_connect()
                c = conn.cursor()
                c.execute("UPDATE goals SET current_progress = ?, target_value = ? WHERE id = ?", (progress, target, current_goal_id))
                conn.commit()
                conn.close()
                
                display_goal_details(None)
                load_goals() # Reload list to reflect potential completion status change
                messagebox.showinfo("Progress Saved", "Goal progress updated.")
                
            except ValueError:
                messagebox.showerror("Invalid Input", "Progress and Target must be numbers.")

        def update_goal_status(new_status):
            """Updates the status of the current goal."""
            global current_goal_id
            if current_goal_id is None:
                messagebox.showwarning("Error", "Please select a goal first.")
                return

            conn = db_connect()
            c = conn.cursor()
            c.execute("UPDATE goals SET status = ? WHERE id = ?", (new_status, current_goal_id))
            conn.commit()
            conn.close()
            
            display_goal_details(None)
            load_goals() 
            messagebox.showinfo("Status Updated", f"Goal marked as {new_status}.")


        # --- Bindings and Initial Load ---
        goal_listbox.bind("<<ListboxSelect>>", display_goal_details)
        load_goals()
        
        # Attach Update Function
        def goals_update_ui():
            load_goals()
        
        pg.update_ui = goals_update_ui
        pg.update_ui()
        
    # FINANCE PAGE
    if pn == "Finance":
        import tkinter as tk
        from tkinter import ttk, messagebox
        from datetime import datetime
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        pg.configure(bg=theme()["BG"])

        # --- Create tables if not exist ---
        run_query("""
            CREATE TABLE IF NOT EXISTS category_budget (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                budget REAL NOT NULL
            )
        """)
        run_query("""
            CREATE TABLE IF NOT EXISTS spending_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                entry_date TEXT NOT NULL
            )
        """)

        # --- Styled label helper ---
        def styled_label(master, text, size=12, weight="bold", pady=(10, 5)):
            return tk.Label(master, text=text, bg=theme()["BG"], fg=theme()["TEXT"],
                            font=("Segoe UI", size, weight), anchor="w")

        # --- CATEGORY MANAGEMENT ---
        styled_label(pg, "💵 Budget Categories").pack(pady=(10, 5), anchor="w", padx=15)

        cat_frame = tk.Frame(pg, bg=theme()["CARD"], bd=1, relief="solid")
        cat_frame.pack(padx=15, pady=5, fill="x")

        tk.Label(cat_frame, text="Category:", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=0, column=0, padx=5, pady=8, sticky="w")
        budget_cat_entry = ttk.Entry(cat_frame, width=20)
        budget_cat_entry.grid(row=0, column=1, padx=5, pady=8)

        tk.Label(cat_frame, text="Budget (₩):", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=0, column=2, padx=5, pady=8, sticky="w")
        budget_amount_entry = ttk.Entry(cat_frame, width=10)
        budget_amount_entry.grid(row=0, column=3, padx=5, pady=8)

        def add_category():
            name = budget_cat_entry.get().strip()
            amount = budget_amount_entry.get().strip()
            if not name or not amount:
                messagebox.showwarning("Input Error", "Please fill out all fields.")
                return
            try:
                run_query("INSERT INTO category_budget (name, budget) VALUES (?, ?)", (name, float(amount)))
                budget_cat_entry.delete(0, tk.END)
                budget_amount_entry.delete(0, tk.END)
                update_category_dropdown()
                load_spending()
            except Exception as e:
                messagebox.showerror("Database Error", f"Could not add category:\n{e}")

        def delete_category():
            category = spend_cat_var.get()
            if not category:
                messagebox.showwarning("Input Error", "Please select a category to delete.")
                return

            confirm = messagebox.askyesno("Confirm Delete", f"Delete category '{category}'?")
            if not confirm:
                return

            try:
                run_query("DELETE FROM category_budget WHERE name = ?", (category,))
                spend_cat_var.set("")
                update_category_dropdown()
                load_spending()
                messagebox.showinfo("Success", f"Category '{category}' deleted.")
            except Exception as e:
                messagebox.showerror("Database Error", f"Could not delete category:\n{e}")

        tk.Button(cat_frame, text="Add Category", bg=theme()["BTN"], activebackground=theme()["BTN_HOVER"],
                relief="flat", command=add_category).grid(row=0, column=4, padx=10, pady=8)
        tk.Button(cat_frame, text="Delete Category", bg=theme()["BTN"], activebackground=theme()["BTN_HOVER"],
                relief="flat", command=delete_category).grid(row=0, column=5, padx=10, pady=8)

        # --- SPENDING LOG ---
        styled_label(pg, "🧾 Spending Log").pack(pady=(15, 5), anchor="w", padx=15)

        spend_frame = tk.Frame(pg, bg=theme()["CARD"], bd=1, relief="solid")
        spend_frame.pack(padx=15, pady=5, fill="x")

        tk.Label(spend_frame, text="Item:", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=0, column=0, padx=5, pady=8)
        spend_item_entry = ttk.Entry(spend_frame, width=20)
        spend_item_entry.grid(row=0, column=1, padx=5, pady=8)

        tk.Label(spend_frame, text="Category:", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=0, column=2, padx=5, pady=8)
        spend_cat_var = tk.StringVar()
        spend_cat_menu = ttk.OptionMenu(spend_frame, spend_cat_var, "")
        spend_cat_menu.grid(row=0, column=3, padx=5, pady=8)

        tk.Label(spend_frame, text="Amount (₩):", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=0, column=4, padx=5, pady=8)
        spend_amount_entry = ttk.Entry(spend_frame, width=10)
        spend_amount_entry.grid(row=0, column=5, padx=5, pady=8)

        def add_spending():
            item = spend_item_entry.get().strip()
            category = spend_cat_var.get()
            amount = spend_amount_entry.get().strip()
            date = datetime.now().strftime("%Y-%m-%d")

            if not item or not category or not amount:
                messagebox.showwarning("Input Error", "Please fill out all fields.")
                return

            try:
                run_query("INSERT INTO spending_log (item, category, amount, entry_date) VALUES (?, ?, ?, ?)",
                        (item, category, float(amount), date))
                spend_item_entry.delete(0, tk.END)
                spend_amount_entry.delete(0, tk.END)
                load_spending()
                update_spending_chart()
            except Exception as e:
                messagebox.showerror("Database Error", f"Could not add spending:\n{e}")

        tk.Button(spend_frame, text="Add Spending", bg=theme()["BTN"], activebackground=theme()["BTN_HOVER"],
                relief="flat", command=add_spending).grid(row=0, column=6, padx=10, pady=8)

        # --- SPENDING CHART ---
        styled_label(pg, "📊 Spending by Category").pack(pady=(15, 5), anchor="w", padx=15)

        chart_frame = tk.Frame(pg, bg=theme()["CARD"], bd=1, relief="solid")
        chart_frame.pack(padx=15, pady=5, fill="both", expand=False)

        def update_spending_chart():
            for widget in chart_frame.winfo_children():
                widget.destroy()

            rows = run_query("""
                SELECT category, SUM(amount) FROM spending_log GROUP BY category ORDER BY SUM(amount) DESC
            """)
            if not rows:
                tk.Label(chart_frame, text="No spending data yet.", bg=theme()["CARD"], fg="gray").pack(pady=10)
                return

            categories = [r[0] for r in rows]
            totals = [r[1] for r in rows]

            fig = Figure(figsize=(5, 2.5))
            ax = fig.add_subplot(111)
            ax.bar(categories, totals, color=theme()["ACCENT"])
            ax.set_title("Spending by Category", fontsize=10)
            ax.tick_params(axis='x', rotation=30)
            ax.set_ylabel("₩")
            ax.grid(axis='y', linestyle='--', alpha=0.6)

            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

        # --- SPENDING LIST ---
        styled_label(pg, "🗂️ Recent Transactions").pack(pady=(15, 5), anchor="w", padx=15)

        list_frame = tk.Frame(pg, bg=theme()["CARD"], bd=1, relief="solid")
        list_frame.pack(padx=15, pady=5, fill="both", expand=True)

        def load_spending():
            for widget in list_frame.winfo_children():
                widget.destroy()

            rows = run_query("SELECT id, item, category, amount, entry_date FROM spending_log ORDER BY entry_date DESC")
            if not rows:
                tk.Label(list_frame, text="No spending entries yet.", bg=theme()["CARD"], fg="gray").pack(pady=10)
                return

            for r in rows:
                text = f"{r[4]} — {r[1]} ({r[2]}) : ₩{r[3]:,.0f}"
                tk.Label(list_frame, text=text, bg=theme()["CARD"], fg=theme()["TEXT"],
                        anchor="w", justify="left", font=("Segoe UI", 10)).pack(fill="x", padx=15, pady=2)

        # --- INIT ---
        def update_category_dropdown():
            categories = [r[0] for r in run_query("SELECT name FROM category_budget ORDER BY name ASC")] or []
            spend_cat_var.set("")
            spend_cat_menu['menu'].delete(0, 'end')
            for cat in categories:
                spend_cat_menu['menu'].add_command(label=cat, command=lambda v=cat: spend_cat_var.set(v))
            if categories:
                spend_cat_var.set(categories[0])

        update_category_dropdown()
        load_spending()
        update_spending_chart()
        
    # DIET PAGE - Daily Weight Tracker
    if pn == "Diet":
        # --- Clear the page first ---
        for widget in pg.winfo_children():
            widget.destroy()

        # --- Unique Global Variables ---
        global diet_weight_entry, diet_weight_date_entry, diet_weight_frame

        # --- Database Table ---
        run_query("""
            CREATE TABLE IF NOT EXISTS diet_weight_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                weight REAL NOT NULL
            )
        """)

        # --- Functions ---
        def add_diet_weight():
            date_val = diet_weight_date_entry.get()
            try:
                weight_val = float(diet_weight_entry.get())
            except ValueError:
                messagebox.showerror("Input Error", "Please enter a valid weight number.")
                return

            if not date_val:
                messagebox.showwarning("Missing Date", "Please enter a date.")
                return

            run_query("INSERT INTO diet_weight_log (date, weight) VALUES (?, ?)", (date_val, weight_val))
            diet_weight_entry.delete(0, tk.END)
            load_diet_weight_log()

        def delete_diet_weight(entry_id):
            if messagebox.askyesno("Delete Entry", "Are you sure you want to delete this weight entry?"):
                run_query("DELETE FROM diet_weight_log WHERE id = ?", (entry_id,))
                load_diet_weight_log()

        def load_diet_weight_log():
            # Clear previous rows
            for widget in diet_weight_frame.winfo_children():
                widget.destroy()

            rows = run_query("SELECT id, date, weight FROM diet_weight_log ORDER BY date DESC")
            if not rows:
                tk.Label(diet_weight_frame, text="No weight entries yet!").pack(pady=10)
                return

            for entry_id, date_val, weight_val in rows:
                row = tk.Frame(diet_weight_frame, bd=1, relief="solid", padx=5, pady=3)
                row.pack(fill="x", pady=2)
                tk.Label(row, text=f"{date_val}: {weight_val} kg", font=("Segoe UI", 10)).pack(side="left")
                tk.Button(row, text="Delete", width=8, command=lambda eid=entry_id: delete_diet_weight(eid)).pack(side="right", padx=5)

        # --- UI Layout ---
        tk.Label(pg, text="⚖️ Daily Weight Tracker", font=("Segoe UI", 16, "bold")).pack(pady=10)

        # Input Frame
        input_frame = tk.Frame(pg, bd=1, relief="solid", padx=10, pady=10)
        input_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(input_frame, text="Date:").grid(row=0, column=0, sticky="w")
        diet_weight_date_entry = tk.Entry(input_frame)
        diet_weight_date_entry.insert(0, date.today().isoformat())
        diet_weight_date_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(input_frame, text="Weight (kg):").grid(row=0, column=2, sticky="w")
        diet_weight_entry = tk.Entry(input_frame, width=10)
        diet_weight_entry.grid(row=0, column=3, padx=5, pady=5)

        tk.Button(input_frame, text="Add Entry", command=add_diet_weight, bg=theme()['ACCENT']).grid(row=0, column=4, padx=10)

        # Weight Log Frame (scrollable)
        weight_container = tk.Frame(pg)
        weight_container.pack(fill="both", expand=True, padx=10, pady=5)
        weight_canvas = tk.Canvas(weight_container)
        weight_canvas.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(weight_container, orient="vertical", command=weight_canvas.yview)
        scrollbar.pack(side="right", fill="y")
        weight_canvas.configure(yscrollcommand=scrollbar.set)
        diet_weight_frame = tk.Frame(weight_canvas)
        weight_canvas.create_window((0,0), window=diet_weight_frame, anchor="nw")
        diet_weight_frame.bind("<Configure>", lambda e: weight_canvas.configure(scrollregion=weight_canvas.bbox("all")))

        # --- Initial Load ---
        load_diet_weight_log()
        
    # ----------------- TAROT PAGE -----------------
    if pn == "Tarot":
        from tkinter import scrolledtext
        from tkcalendar import DateEntry
        from datetime import date

        # --- Decks & Reading Types ---
        DECKS = [
            "Citadel Fantasy Oracle",
            "Cosmic Insight Oracle",
            "Modern Lenormand",
            "Rider Waite Tarot",
            "Rosebell Oracle"
        ]
        READING_TYPES = ["Love", "Career", "General", "Daily", "Custom"]

        # --- Helpers ---
        def add_reading():
            r_name = reading_name_entry.get().strip()
            deck = deck_combo.get().strip()
            spread = spread_entry.get().strip()
            reading_date = date_entry.get_date().isoformat()
            cards_txt = cards_entry.get().strip()
            interp = interpretation_text.get("1.0", "end-1c").strip()

            if not r_name:
                messagebox.showwarning("Missing field", "Please enter a reading name.")
                return

            # Insert into existing TAROT table (no DB schema change)
            run_query("""
                INSERT INTO TAROT (reading_name, category, spread, date, cards, interpretation, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (r_name, deck, spread, reading_date, cards_txt, interp, ""))

            # clear inputs
            reading_name_entry.delete(0, "end")
            spread_entry.delete(0, "end")
            cards_entry.delete(0, "end")
            interpretation_text.delete("1.0", "end")
            date_entry.set_date(date.today())
            load_active_readings()

        def delete_reading(rid):
            if messagebox.askyesno("Delete", "Delete this reading?"):
                run_query("DELETE FROM TAROT WHERE id = ?", (rid,))
                load_active_readings()

        def show_interpretation(rid):
            rows = run_query("SELECT reading_name, category, spread, date, cards, interpretation FROM TAROT WHERE id = ?", (rid,))
            if not rows:
                messagebox.showerror("Not found", "Reading not found.")
                return
            row = rows[0]
            rname, deck, spread, rdate, cards_txt, interp = row

            win = tk.Toplevel(content)
            win.title(f"{rname} — {deck} ({rdate})")
            win.geometry("640x480")
            win.configure(bg=theme()["CARD"])
            frm = tk.Frame(win, bg=theme()["CARD"], padx=12, pady=12)
            frm.pack(fill="both", expand=True)

            tk.Label(frm, text=f"{rname} — {deck}", font=("Segoe UI", 12, "bold"),
                    bg=theme()["CARD"], fg=theme()["TEXT"]).pack(anchor="w")
            tk.Label(frm, text=f"Date: {rdate}", bg=theme()["CARD"], fg=theme()["TEXT"]).pack(anchor="w")
            tk.Label(frm, text=f"Spread: {spread}", bg=theme()["CARD"], fg=theme()["TEXT"]).pack(anchor="w", pady=(0,6))
            tk.Label(frm, text=f"Cards: {cards_txt or '(none)'}", bg=theme()["CARD"], fg=theme()["TEXT"]).pack(anchor="w", pady=(0,8))

            tk.Label(frm, text="Interpretation:", bg=theme()["CARD"], fg=theme()["TEXT"]).pack(anchor="w")
            viewer = scrolledtext.ScrolledText(frm, wrap=tk.WORD, height=16, bg=theme()["BG"], fg=theme()["TEXT"])
            viewer.insert("1.0", interp or "(No interpretation saved)")
            viewer.config(state="disabled")
            viewer.pack(fill="both", expand=True, pady=(6,8))

            tk.Button(frm, text="Close", command=win.destroy, bg=theme()["BTN"], activebackground=theme()["BTN_HOVER"], relief="flat").pack(anchor="e", pady=(6,0))

        def load_active_readings():
            # clear list
            for w in tarot_active_frame.winfo_children():
                w.destroy()

            rows = run_query("SELECT id, reading_name, category, spread, date, cards FROM TAROT ORDER BY date DESC, id DESC")
            if not rows:
                tk.Label(tarot_active_frame, text="No readings logged yet.", bg=theme()["CARD"], fg=theme()["TEXT"], font=("Segoe UI", 10, "italic")).pack(pady=18)
                return

            for rid, rname, deck, spread, rdate, cards_txt in rows:
                row_fr = tk.Frame(tarot_active_frame, bg=theme()["CARD"], bd=1, relief="solid", padx=8, pady=6)
                row_fr.pack(fill="x", pady=4, padx=6)

                left = tk.Frame(row_fr, bg=theme()["CARD"])
                left.pack(side="left", fill="both", expand=True)
                tk.Label(left, text=f"[{rdate}] {rname}", font=("Segoe UI", 10, "bold"), bg=theme()["CARD"], fg=theme()["TEXT"]).pack(anchor="w")
                tk.Label(left, text=f"{deck} — {spread or '(no spread)'}", font=("Segoe UI", 9), bg=theme()["CARD"], fg=theme()["TEXT"]).pack(anchor="w")
                if cards_txt:
                    tk.Label(left, text=f"Cards: {cards_txt}", font=("Segoe UI", 9), bg=theme()["CARD"], fg=theme()["TEXT"]).pack(anchor="w")

                btns = tk.Frame(row_fr, bg=theme()["CARD"])
                btns.pack(side="right", anchor="e")
                tk.Button(btns, text="View Details", command=lambda rid=rid: show_interpretation(rid), bg=theme()["BTN"], activebackground=theme()["BTN_HOVER"], relief="flat").pack(side="left", padx=4)
                tk.Button(btns, text="Delete", command=lambda rid=rid: delete_reading(rid), bg=theme()["BTN_HOVER"], relief="flat").pack(side="left", padx=4)

        # ---------- Page UI ----------
        # Header
        tk.Label(content, text="🔮 Tarot Readings", font=("Segoe UI", 16, "bold"), bg=theme()["CARD"], fg=theme()["TEXT"]).pack(anchor="nw", pady=10, padx=10)

        # Input area (card)
        input_card = tk.Frame(content, bg=theme()["BG"], bd=1, relief="solid", padx=10, pady=10)
        input_card.pack(fill="x", padx=10, pady=(4,8))

        # Row 1: Deck, Reading Name, Date
        r1 = tk.Frame(input_card, bg=theme()["BG"])
        r1.pack(fill="x", pady=(0,6))
        tk.Label(r1, text="Deck:", bg=theme()["BG"], fg=theme()["TEXT"]).grid(row=0, column=0, sticky="w")
        deck_combo = ttk.Combobox(r1, values=DECKS, state="readonly", width=26)
        deck_combo.set(DECKS[0])
        deck_combo.grid(row=0, column=1, padx=8, sticky="w")

        tk.Label(r1, text="Reading Name:", bg=theme()["BG"], fg=theme()["TEXT"]).grid(row=0, column=2, sticky="w", padx=(18,0))
        reading_name_entry = tk.Entry(r1, width=26)
        reading_name_entry.insert(0, "Daily Guidance")
        reading_name_entry.grid(row=0, column=3, padx=8, sticky="w")

        tk.Label(r1, text="Date:", bg=theme()["BG"], fg=theme()["TEXT"]).grid(row=0, column=4, sticky="w", padx=(18,0))
        date_entry = DateEntry(r1, width=12, date_pattern='yyyy-mm-dd')
        date_entry.set_date(date.today())
        date_entry.grid(row=0, column=5, padx=8, sticky="w")

        # Row 2: Spread (free text) and Cards
        r2 = tk.Frame(input_card, bg=theme()["BG"])
        r2.pack(fill="x", pady=(0,6))
        tk.Label(r2, text="Spread:", bg=theme()["BG"], fg=theme()["TEXT"]).grid(row=0, column=0, sticky="w")
        spread_entry = tk.Entry(r2, width=36)
        spread_entry.grid(row=0, column=1, padx=8, sticky="w")
        tk.Label(r2, text="Cards (comma separated):", bg=theme()["BG"], fg=theme()["TEXT"]).grid(row=0, column=2, sticky="w", padx=(18,0))
        cards_entry = tk.Entry(r2, width=36)
        cards_entry.grid(row=0, column=3, padx=8, sticky="w")

        # Row 3: Interpretation (LARGE)
        tk.Label(input_card, text="Interpretation:", bg=theme()["BG"], fg=theme()["TEXT"]).pack(anchor="w")
        interpretation_text = tk.Text(input_card, height=10, wrap=tk.WORD, bg=theme()["CARD"], fg=theme()["TEXT"])
        interpretation_text.pack(fill="both", expand=False, pady=(6,8))

        # Add button
        btn_row = tk.Frame(input_card, bg=theme()["BG"])
        btn_row.pack(fill="x")
        tk.Button(btn_row, text="Add Reading", command=add_reading, bg=theme()["ACCENT"], fg=theme()["TEXT"], relief="flat").pack(anchor="e")

        # Active readings list (scrollable)
        tarot_active_container = tk.Frame(content, bg=theme()["CARD"])
        tarot_active_container.pack(fill="both", expand=True, padx=10, pady=(6,10))

        tk.Label(tarot_active_container, text="Recent Readings", font=("Segoe UI", 12, "bold"), bg=theme()["CARD"], fg=theme()["TEXT"]).pack(anchor="nw", padx=6, pady=(6,0))
        active_canvas = tk.Canvas(tarot_active_container, bg=theme()["CARD"], highlightthickness=0)
        active_canvas.pack(side="left", fill="both", expand=True)
        scrollb = ttk.Scrollbar(tarot_active_container, orient="vertical", command=active_canvas.yview)
        scrollb.pack(side="right", fill="y")
        active_canvas.configure(yscrollcommand=scrollb.set)

        tarot_active_frame = tk.Frame(active_canvas, bg=theme()["CARD"])
        active_canvas.create_window((0,0), window=tarot_active_frame, anchor="nw")
        tarot_active_frame.bind("<Configure>", lambda e: active_canvas.configure(scrollregion=active_canvas.bbox("all")))

        # Initial load
        load_active_readings()
    
    # Wishlist Page
    if pn == "Wishlist":
        # Clear previous page
        for widget in pg.winfo_children():
            widget.destroy()

        # --- GLOBAL VARIABLES (Wishlist Specific) ---
        global wish_item_entry, wish_category_entry, wish_price_entry, wish_priority_combo, wish_watchlist_frame, wish_history_frame

        PRIORITIES = ['High', 'Medium', 'Low']
        t = theme()  # your theme function

        # --- FUNCTIONS ---
        def add_wish_item():
            name = wish_item_entry.get().strip()
            category = wish_category_entry.get().strip()
            price_str = wish_price_entry.get().strip()
            priority = wish_priority_combo.get()

            if not name:
                messagebox.showwarning("Missing Data", "Item Name is required.")
                return

            try:
                price = float(price_str) if price_str else None

                run_query("""
                    INSERT INTO wishlist (name, category, price, priority, status, date_added)
                    VALUES (?, ?, ?, ?, 'Wishlist', ?)
                """, (name, category, price, priority, date.today().isoformat()))

                # Clear form
                wish_item_entry.delete(0, tk.END)
                wish_category_entry.delete(0, tk.END)
                wish_price_entry.delete(0, tk.END)
                wish_priority_combo.set('')

                load_wishlist()
                load_wish_history()

            except ValueError:
                messagebox.showerror("Input Error", "Price must be a number.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add item: {e}")

        def delete_wish_item(item_id):
            if messagebox.askyesno("Delete Item", "Are you sure you want to remove this item permanently?"):
                run_query("DELETE FROM wishlist WHERE id = ?", (item_id,))
                load_wishlist()
                load_wish_history()

        def mark_as_purchased(item_id):
            run_query("UPDATE wishlist SET status = ?, date_purchased = ? WHERE id = ?",
                    ('Purchased', date.today().isoformat(), item_id))
            load_wishlist()
            load_wish_history()
            messagebox.showinfo("Updated", "Item marked as Purchased!")
            
        def undo_purchased(item_id):
            run_query("UPDATE wishlist SET status = 'Wishlist', date_purchased = NULL WHERE id = ?", (item_id,))
            load_wishlist()
            load_wish_history()
            messagebox.showinfo("Undo Purchased", "Item moved back to Wishlist!")

        def load_wishlist():
            for widget in wish_watchlist_frame.winfo_children():
                widget.destroy()

            rows = run_query("SELECT id, name, category, price, priority FROM wishlist WHERE status = 'Wishlist' ORDER BY priority ASC, name ASC")
            if not rows:
                tk.Label(wish_watchlist_frame, text="Your Wishlist is empty! 🎁", bg=t["CARD"], fg=t["TEXT"]).pack(pady=20)
                return

            for item_id, name, category, price, priority in rows:
                row_frame = tk.Frame(wish_watchlist_frame, bg=t["CARD"], bd=1, relief="solid")
                row_frame.pack(fill="x", pady=5, padx=5)

                info = f"{name} ({category or 'N/A'})"
                if price:
                    info += f" - ${price:.2f}"
                if priority:
                    info += f" [{priority}]"

                tk.Label(row_frame, text=info, font=("Segoe UI", 10, "bold"), bg=t["CARD"], fg=t["TEXT"]).pack(side="left", padx=5)

                tk.Button(row_frame, text="Mark as Purchased", command=lambda iid=item_id: mark_as_purchased(iid),
                        bg=t["ACCENT"], fg="white", relief="flat").pack(side="right", padx=5)
                tk.Button(row_frame, text="✖", command=lambda iid=item_id: delete_wish_item(iid),
                        bg=t["CARD"], fg="red").pack(side="right")

        def load_wish_history():
            for widget in wish_history_frame.winfo_children():
                widget.destroy()

            rows = run_query("SELECT id, name, category, price, date_purchased FROM wishlist WHERE status = 'Purchased' ORDER BY date_purchased DESC")
            if not rows:
                tk.Label(wish_history_frame, text="No items purchased yet! 🎁", bg=t["CARD"], fg=t["TEXT"]).pack(pady=20)
                return

            for item_id, name, category, price, date_purchased in rows:
                row_frame = tk.Frame(wish_history_frame, bg=t["CARD"], bd=1, relief="solid")
                row_frame.pack(fill="x", pady=5, padx=5)

                info = f"{name} ({category or 'N/A'})"
                if price:
                    info += f" - ${price:.2f}"
                    info += f" | Purchased: {date_purchased or 'N/A'}"

                    tk.Label(row_frame, text=info, font=("Segoe UI", 10, "bold"), bg=t["CARD"], fg=t["TEXT"]).pack(side="left", padx=5)

                    tk.Button(row_frame, text="✖", command=lambda iid=item_id: delete_wish_item(iid),
                        bg=t["CARD"], fg="red").pack(side="right")
                    
                    tk.Button(row_frame, text="↩ Undo", command=lambda iid=item_id: undo_purchased(iid),
                        bg=t["ACCENT"], fg="white", relief="flat").pack(side="right", padx=5)

        # --- UI Layout ---
        tk.Label(pg, text="🎁 Wishlist", font=("Segoe UI", 16, "bold"), bg=t["BG"]).pack(pady=10)

        # Input Section
        input_frame = tk.Frame(pg, bg=t["CARD"], padx=10, pady=10)
        input_frame.pack(fill="x", padx=10, pady=(0,15))

        r = 0
        tk.Label(input_frame, text="Item Name:", bg=t["CARD"]).grid(row=r, column=0, sticky="w", padx=5)
        wish_item_entry = tk.Entry(input_frame)
        wish_item_entry.grid(row=r, column=1, sticky="ew", padx=5)

        tk.Label(input_frame, text="Category:", bg=t["CARD"]).grid(row=r, column=2, sticky="w", padx=5)
        wish_category_entry = tk.Entry(input_frame)
        wish_category_entry.grid(row=r, column=3, sticky="ew", padx=5)
        r += 1

        tk.Label(input_frame, text="Price:", bg=t["CARD"]).grid(row=r, column=0, sticky="w", padx=5)
        wish_price_entry = tk.Entry(input_frame)
        wish_price_entry.grid(row=r, column=1, sticky="w", padx=5)

        tk.Label(input_frame, text="Priority:", bg=t["CARD"]).grid(row=r, column=2, sticky="w", padx=5)
        wish_priority_combo = ttk.Combobox(input_frame, values=PRIORITIES, state="readonly", width=10)
        wish_priority_combo.grid(row=r, column=3, sticky="w", padx=5)

        tk.Button(input_frame, text="Add Item", command=add_wish_item, bg=t["ACCENT"], fg="white").grid(row=r, column=4, padx=10)

        input_frame.grid_columnconfigure(1, weight=1)
        input_frame.grid_columnconfigure(3, weight=1)

        # Main Content: Wishlist & History
        main_frame = tk.Frame(pg, bg=t["BG"])
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Left: Wishlist
        wish_container = tk.Frame(main_frame, bg=t["CARD"], padx=10, pady=10)
        wish_container.pack(side="left", fill="both", expand=True, padx=(0,5))
        tk.Label(wish_container, text="🌟 Wishlist Items", font=("Segoe UI", 12, "bold"), bg=t["CARD"]).pack(pady=5)

        wish_canvas = tk.Canvas(wish_container, bg=t["CARD"])
        wish_canvas.pack(side="left", fill="both", expand=True)
        v_scroll_w = ttk.Scrollbar(wish_container, orient="vertical", command=wish_canvas.yview)
        v_scroll_w.pack(side="right", fill="y")
        wish_canvas.configure(yscrollcommand=v_scroll_w.set)
        wish_watchlist_frame = tk.Frame(wish_canvas, bg=t["CARD"])
        wish_canvas.create_window((0,0), window=wish_watchlist_frame, anchor="nw")
        wish_watchlist_frame.bind("<Configure>", lambda e: wish_canvas.configure(scrollregion=wish_canvas.bbox("all")))

        # Right: Purchased History
        history_container = tk.Frame(main_frame, bg=t["CARD"], padx=10, pady=10)
        history_container.pack(side="right", fill="both", expand=True, padx=(5,0))
        tk.Label(history_container, text="📜 Purchased Items", font=("Segoe UI", 12, "bold"), bg=t["CARD"]).pack(pady=5)

        history_canvas = tk.Canvas(history_container, bg=t["CARD"])
        history_canvas.pack(side="left", fill="both", expand=True)
        v_scroll_h = ttk.Scrollbar(history_container, orient="vertical", command=history_canvas.yview)
        v_scroll_h.pack(side="right", fill="y")
        history_canvas.configure(yscrollcommand=v_scroll_h.set)
        wish_history_frame = tk.Frame(history_canvas, bg=t["CARD"])
        history_canvas.create_window((0,0), window=wish_history_frame, anchor="nw")
        wish_history_frame.bind("<Configure>", lambda e: history_canvas.configure(scrollregion=history_canvas.bbox("all")))

        # --- Initial Load ---
        load_wishlist()
        load_wish_history()
        
    # Recipes Page
    if pn == "Recipes":
        
        # --- CRITICAL FIX: Globalize necessary variables ---
        global recipe_title_var, recipe_time_var, recipe_listbox, recipe_detail_text, current_recipe_id
        
        # 1. Page Header
        tk.Label(content, text="🍳 Recipes", 
                 font=("Segoe UI", 16, "bold"), 
                 bg=theme()["CARD"], fg=theme()["TEXT"], 
                 pady=10).pack(fill="x", padx=10, anchor="nw")
        
        # --- Main Content Frame (Side-by-Side Layout) ---
        main_frame = tk.Frame(content, bg=theme()["BG"])
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ----------------------------------------------------
        # LEFT PANEL: List and Add Form
        # ----------------------------------------------------
        
        left_panel = tk.Frame(main_frame, bg=theme()["CARD"], padx=10, pady=10)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        
        # --- Variables ---
        recipe_title_var = tk.StringVar()
        recipe_time_var = tk.StringVar() # e.g., "30 min"

        # --- Listbox (Existing Recipes) ---
        tk.Label(left_panel, text="Saved Recipes:", bg=theme()["CARD"], fg=theme()["TEXT"], font=("Segoe UI", 10, "bold")).pack(pady=(0, 5))
        
        recipe_listbox = tk.Listbox(left_panel, height=15, width=40, bg=theme()["BG"], fg=theme()["TEXT"], selectmode=tk.SINGLE)
        recipe_listbox.pack(pady=(0, 10))
        
        # --- Add Recipe Form ---
        form_frame = tk.Frame(left_panel, bg=theme()["CARD"])
        form_frame.pack(pady=10)
        
        tk.Label(form_frame, text="New Recipe Title:", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=0, column=0, sticky="w")
        tk.Entry(form_frame, textvariable=recipe_title_var, width=25, bg=theme()["BG"], fg=theme()["TEXT"]).grid(row=0, column=1, padx=5)
        
        tk.Label(form_frame, text="Prep Time:", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=1, column=0, sticky="w")
        tk.Entry(form_frame, textvariable=recipe_time_var, width=10, bg=theme()["BG"], fg=theme()["TEXT"]).grid(row=1, column=1, padx=5, sticky="w")
        
        # --- Ingredient and Instruction Input (These will appear after clicking 'Add') ---
        # We will use simple placeholders for now. The main input will happen in the detail view.

        # --- Functions ---
        
        # Global variable to store the ID of the recipe currently being edited/viewed
        current_recipe_id = None
        
        def load_recipe_titles():
            """Loads titles into the listbox."""
            conn = db_connect()
            c = conn.cursor()
            # Fetch ID and Title
            rows = c.execute("SELECT id, title FROM recipes ORDER BY title").fetchall()
            conn.close()

            recipe_listbox.delete(0, tk.END)
            for recipe_id, title in rows:
                # Store the ID in the listbox itself, hidden in the display text
                recipe_listbox.insert(tk.END, f"{recipe_id}|{title}") 

        def display_recipe_details(event):
            """Loads ingredients and instructions for the selected recipe."""
            global current_recipe_id
            
            try:
                # Get the index of the selected item
                index = recipe_listbox.curselection()[0]
                # Extract the hidden ID and Title from the listbox item
                listbox_text = recipe_listbox.get(index)
                
                recipe_id, title = listbox_text.split("|", 1)
                recipe_id = int(recipe_id)
                current_recipe_id = recipe_id
                
                conn = db_connect()
                c = conn.cursor()
                row = c.execute("SELECT prep_time, ingredients, instructions FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
                conn.close()

                if row:
                    prep_time, ingredients, instructions = row
                    
                    # Format the output for the detail text widget
                    output = f"--- 🥘 {title.upper()} ---\n"
                    output += f"Prep Time: {prep_time or 'N/A'}\n\n"
                    output += "--- INGREDIENTS ---\n"
                    output += f"{ingredients}\n\n"
                    output += "--- INSTRUCTIONS ---\n"
                    output += f"{instructions}"

                    recipe_detail_text.config(state="normal")
                    recipe_detail_text.delete("1.0", tk.END)
                    recipe_detail_text.insert("1.0", output)
                    recipe_detail_text.config(state="disabled")
                
            except IndexError:
                # No item selected
                pass
            except Exception as e:
                # Handle potential splitting error if data is malformed
                recipe_detail_text.config(state="normal")
                recipe_detail_text.insert(tk.END, f"\nError loading recipe: {e}")
                recipe_detail_text.config(state="disabled")


        def add_new_recipe_prompt():
            """Creates an empty template in the detail view for a new recipe entry."""
            global current_recipe_id
            
            title = recipe_title_var.get().strip()
            time = recipe_time_var.get().strip()

            if not title:
                messagebox.showwarning("Missing Title", "Please enter a title for the new recipe.")
                return
            
            # Save a minimal entry to get a database ID
            conn = db_connect()
            c = conn.cursor()
            c.execute("INSERT INTO recipes (title, prep_time, ingredients, instructions) VALUES (?, ?, ?, ?)", 
                      (title, time, "List ingredients here...", "List instructions here..."))
            conn.commit()
            
            # Get the ID of the new entry
            new_id = c.lastrowid
            conn.close()
            current_recipe_id = new_id

            # Clear entry fields
            recipe_title_var.set("")
            recipe_time_var.set("")

            # Load and select the new recipe in the list
            load_recipe_titles()
            # Select the newly added item (not trivial without search, so we skip selection for now)
            
            # Display an editable template in the detail view
            recipe_detail_text.config(state="normal")
            recipe_detail_text.delete("1.0", tk.END)
            recipe_detail_text.insert("1.0", f"--- ✏️ EDITING: {title.upper()} ---\n")
            recipe_detail_text.insert(tk.END, f"Prep Time: {time}\n\n")
            recipe_detail_text.insert(tk.END, "--- INGREDIENTS ---\n[Type ingredients here]\n\n")
            recipe_detail_text.insert(tk.END, "--- INSTRUCTIONS ---\n[Type instructions here]")
            # Keep it ENABLED for editing
            messagebox.showinfo("Ready to Edit", "Recipe created. Please type ingredients/instructions in the right panel and click 'Save Changes'.")
        
        def save_recipe_changes():
            """Parses the detail text and updates the current recipe in the database."""
            global current_recipe_id
            
            if current_recipe_id is None:
                messagebox.showwarning("No Recipe Selected", "Please select or add a recipe first.")
                return

            full_text = recipe_detail_text.get("1.0", tk.END).strip()
            
            # --- Simple Parsing Logic ---
            try:
                # Find the sections
                ingredients_start = full_text.find("--- INGREDIENTS ---")
                instructions_start = full_text.find("--- INSTRUCTIONS ---")
                
                # Extract sections based on markers
                if ingredients_start != -1 and instructions_start != -1:
                    ingredients = full_text[ingredients_start + len("--- INGREDIENTS ---"):instructions_start].strip()
                    instructions = full_text[instructions_start + len("--- INSTRUCTIONS ---"):].strip()
                else:
                    messagebox.showerror("Error", "Could not find '--- INGREDIENTS ---' or '--- INSTRUCTIONS ---' markers.")
                    return
                
                # Extract Prep Time (Simple version: look for the first line after title)
                prep_time_line = full_text.split('\n')[1]
                prep_time_value = prep_time_line.split(':', 1)[1].strip() if 'Prep Time:' in prep_time_line else ""

            except Exception as e:
                messagebox.showerror("Parsing Error", f"Failed to parse text. Ensure markers are correct. Error: {e}")
                return
            # --- End Parsing Logic ---

            conn = db_connect()
            c = conn.cursor()
            c.execute("UPDATE recipes SET prep_time = ?, ingredients = ?, instructions = ? WHERE id = ?",
                      (prep_time_value, ingredients, instructions, current_recipe_id))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Saved", "Recipe details updated successfully.")
            # Reload display to show the final read-only version
            display_recipe_details(None) 
        
        
        # Buttons for adding new recipes
        tk.Button(form_frame, text="Add New Recipe", command=add_new_recipe_prompt, 
                  bg=theme()["ACCENT"], fg="white").grid(row=2, column=0, columnspan=2, pady=5)
        
        # ----------------------------------------------------
        # RIGHT PANEL: Detail View and Save Button
        # ----------------------------------------------------
        
        right_panel = tk.Frame(main_frame, bg=theme()["BG"])
        right_panel.pack(side="right", fill="both", expand=True)

        tk.Label(right_panel, text="Recipe Details:", bg=theme()["BG"], fg=theme()["TEXT"], font=("Segoe UI", 10, "bold")).pack(pady=(0, 5), anchor="w")
        
        # Detail Text Area
        recipe_detail_text = tk.Text(right_panel, wrap="word", font=("Segoe UI", 10), height=25,
                                      bg=theme()["CARD"], fg=theme()["TEXT"], insertbackground=theme()["TEXT"],
                                      state="disabled") # Starts disabled/read-only
        recipe_detail_text.pack(fill="both", expand=True)
        
        action_button_frame = tk.Frame(right_panel, bg=theme()["BG"]) # <--- CRITICAL: DEFINE THE FRAME HERE
        action_button_frame.pack(pady=(5, 0))
        
        def enable_editing():
            if current_recipe_id is not None:
                recipe_detail_text.config(state="normal")
                messagebox.showinfo("Editing Mode", "The recipe details are now editable. Click 'Save Changes' when finished.")
            else:
                messagebox.showwarning("No Recipe", "Please select a recipe from the list first.")

        tk.Button(action_button_frame, text="Edit Recipe", command=enable_editing, 
                  bg=theme()["ACCENT"], fg="white").pack(side="left", padx=5) 
        
        # Detail Save Button
        tk.Button(right_panel, text="Save Changes", command=save_recipe_changes, 
                  bg=theme()["ACCENT"], fg="white").pack(pady=(5, 0))


        # --- Bindings and Initial Load ---
        recipe_listbox.bind("<<ListboxSelect>>", display_recipe_details)
        load_recipe_titles()
        
        # Attach Update Function
        def recipe_update_ui():
            load_recipe_titles()
        
        pg.update_ui = recipe_update_ui
        pg.update_ui()
        
    # HABITS PAGE
    if pn == "Habits":
        import tkinter as tk
        from tkinter import ttk, messagebox, simpledialog
        import calendar
        from datetime import datetime
        import json
        import uuid

        t = theme()  # use your existing theme dict

        # --- Global month state ---
        global habit_month, habit_year
        try:
            habit_month
        except NameError:
            habit_month = datetime.now().month
            habit_year = datetime.now().year

        # --- Clear previous widgets ---
        for widget in pg.winfo_children():
            widget.destroy()
        pg.configure(bg=t["BG"])

        # --- DB helper ---
        def run_habit_query(query, params=(), fetchone=False):
            import sqlite3
            conn = sqlite3.connect("mochi.db")
            c = conn.cursor()
            try:
                c.execute(query, params)
                if query.strip().upper().startswith("SELECT"):
                    result = c.fetchone() if fetchone else c.fetchall()
                    conn.close()
                    return result
                conn.commit()
            except Exception as e:
                conn.close()
                messagebox.showerror("DB Error", str(e))
            conn.close()

        # --- Add habit ---
        def add_habit():
            name = habit_name_entry.get().strip()
            if not name:
                messagebox.showwarning("Input Error", "Enter habit name.")
                return
            hid = str(uuid.uuid4())
            run_habit_query("INSERT INTO habits_tbl (habit_id, habit_name) VALUES (?, ?)", (hid, name))
            habit_name_entry.delete(0, tk.END)
            load_habits()

        # --- Edit habit ---
        def edit_habit(hid):
            row = run_habit_query("SELECT habit_name FROM habits_tbl WHERE habit_id=?", (hid,), fetchone=True)
            if not row:
                return
            old_name = row[0]
            new_name = simpledialog.askstring("Edit Habit", "Habit Name:", initialvalue=old_name, parent=pg)
            if new_name:
                run_habit_query("UPDATE habits_tbl SET habit_name=? WHERE habit_id=?", (new_name, hid))
                load_habits()

        # --- Delete habit ---
        def delete_habit(hid):
            if messagebox.askyesno("Delete Habit", "Are you sure?"):
                run_habit_query("DELETE FROM habits_tbl WHERE habit_id=?", (hid,))
                load_habits()

        # --- Month navigation ---
        def prev_month():
            global habit_month, habit_year
            habit_month -= 1
            if habit_month < 1:
                habit_month = 12
                habit_year -= 1
            month_var.set(calendar.month_name[habit_month])
            year_var.set(habit_year)
            load_habits()

        def next_month():
            global habit_month, habit_year
            habit_month += 1
            if habit_month > 12:
                habit_month = 1
                habit_year += 1
            month_var.set(calendar.month_name[habit_month])
            year_var.set(habit_year)
            load_habits()

        # --- Load habits into UI ---
        def load_habits():
            for widget in habit_inner.winfo_children():
                widget.destroy()

            rows = run_habit_query("SELECT habit_id, habit_name, habit_completions FROM habits_tbl ORDER BY habit_name ASC")
            if not rows:
                tk.Label(habit_inner, text="No habits yet.", bg=t["CARD"], fg="gray").grid(row=0, column=0, padx=5, pady=5)
                return

            # Calendar header
            tk.Label(habit_inner, text="Habit", bg=t["CARD"], fg=t["TEXT"], font=("Segoe UI", 10, "bold"), width=20, anchor="w").grid(row=0, column=0)
            tk.Label(habit_inner, text="Edit", bg=t["CARD"], fg=t["TEXT"], font=("Segoe UI", 10, "bold"), width=4).grid(row=0, column=1)
            days_in_month = calendar.monthrange(habit_year, habit_month)[1]
            for d in range(1, days_in_month + 1):
                tk.Label(habit_inner, text=str(d), bg=t["CARD"], fg=t["TEXT"], font=("Segoe UI", 8), width=2).grid(row=0, column=d+1)

            for r, (hid, hname, completions_json) in enumerate(rows, start=1):
                completions = json.loads(completions_json) if completions_json else {}
                tk.Label(habit_inner, text=hname, bg=t["CARD"], fg=t["TEXT"], font=("Segoe UI", 10), width=20, anchor="w").grid(row=r, column=0, sticky="w")
                tk.Button(habit_inner, text="Edit", bg=t["BTN"], activebackground=t["BTN_HOVER"], relief="flat", command=lambda h=hid: edit_habit(h)).grid(row=r, column=1, sticky="w")
                for d in range(1, days_in_month+1):
                    day_str = f"{habit_year}-{habit_month:02d}-{d:02d}"
                    var = tk.IntVar(value=completions.get(day_str, 0))
                    def toggle(day=day_str, h=hid, v=var):
                        row = run_habit_query("SELECT habit_completions FROM habits_tbl WHERE habit_id=?", (h,), fetchone=True)
                        current = json.loads(row[0]) if row and row[0] else {}
                        current[day] = v.get()
                        run_habit_query("UPDATE habits_tbl SET habit_completions=? WHERE habit_id=?", (json.dumps(current), h))
                    tk.Checkbutton(habit_inner, variable=var, command=toggle, bg=t["CARD"], width=2).grid(row=r, column=d+1, padx=1)

        # --- Top frame ---
        top_frame = tk.Frame(pg, bg=t["CARD"])
        top_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(top_frame, text="📋 Habits Tracker", font=("Segoe UI", 16, "bold"), bg=t["CARD"], fg=t["TEXT"]).pack(anchor="w")
        habit_name_entry = ttk.Entry(top_frame, width=25)
        habit_name_entry.pack(side="left", padx=(0,5), pady=5)
        tk.Button(top_frame, text="Add Habit", bg=t["BTN"], activebackground=t["BTN_HOVER"], relief="flat", command=add_habit).pack(side="left", padx=5, pady=5)

        # --- Month navigation ---
        nav_frame = tk.Frame(pg, bg=t["CARD"])
        nav_frame.pack(fill="x", padx=10, pady=(0,5))
        month_var = tk.StringVar(value=calendar.month_name[habit_month])
        year_var = tk.IntVar(value=habit_year)
        tk.Button(nav_frame, text="<", command=prev_month, bg=t["BTN"], relief="flat").pack(side="left", padx=5)
        tk.Label(nav_frame, textvariable=month_var, bg=t["CARD"], fg=t["TEXT"], font=("Segoe UI", 12, "bold")).pack(side="left")
        tk.Label(nav_frame, textvariable=year_var, bg=t["CARD"], fg=t["TEXT"], font=("Segoe UI", 12, "bold")).pack(side="left", padx=5)
        tk.Button(nav_frame, text=">", command=next_month, bg=t["BTN"], relief="flat").pack(side="left", padx=5)

        # --- Habit log canvas ---
        habit_canvas_frame = tk.Frame(pg, bg=t["CARD"])
        habit_canvas_frame.pack(fill="both", expand=True, padx=10, pady=5)
        habit_canvas = tk.Canvas(habit_canvas_frame, bg=t["CARD"])
        habit_canvas.pack(side="top", fill="both", expand=True)
        h_scroll = ttk.Scrollbar(habit_canvas_frame, orient="horizontal", command=habit_canvas.xview)
        h_scroll.pack(side="bottom", fill="x")
        habit_canvas.configure(xscrollcommand=h_scroll.set)
        habit_inner = tk.Frame(habit_canvas, bg=t["CARD"])
        habit_canvas.create_window((0,0), window=habit_inner, anchor="nw")
        habit_inner.bind("<Configure>", lambda e: habit_canvas.configure(scrollregion=habit_canvas.bbox("all")))

        # --- Initial load ---
        load_habits()
    
    # BRAINDUMP PAGE
    if pn == "Braindump":

        global braindump_text_widget, braindump_date_entry, braindump_listbox

        tk.Label(content, text="🧠 Braindump",
                font=("Segoe UI", 16, "bold"),
                bg=theme()["CARD"], fg=theme()["TEXT"],
                pady=10).pack(fill="x", padx=10, anchor="nw")

        # --- Main Frame ---
        main_frame = tk.Frame(content, bg=theme()["CARD"])
        main_frame.pack(fill="both", expand=True, padx=10, pady=(5,10))

        # --- Left Panel: Past Logs ---
        left_frame = tk.Frame(main_frame, bg=theme()["CARD"], width=200)
        left_frame.pack(side="left", fill="y", padx=(0,10))
        tk.Label(left_frame, text="📜 Past Braindumps", bg=theme()["CARD"],
                fg=theme()["TEXT"], font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0,5))

        braindump_listbox = tk.Listbox(left_frame, bg=theme()["CARD"], fg=theme()["TEXT"], width=25)
        braindump_listbox.pack(fill="y", expand=True)

        # Scrollbar for Listbox
        lb_scroll = tk.Scrollbar(left_frame, orient=tk.VERTICAL, command=braindump_listbox.yview)
        lb_scroll.pack(side="right", fill="y")
        braindump_listbox.config(yscrollcommand=lb_scroll.set)

        # --- Delete Button ---
        def delete_braindump():
            sel = braindump_listbox.curselection()
            if not sel:
                return
            date_str = braindump_listbox.get(sel[0])
            confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the braindump for {date_str}?")
            if confirm:
                conn = db_connect()
                c = conn.cursor()
                c.execute("DELETE FROM braindumps WHERE date=?", (date_str,))
                conn.commit()
                conn.close()
                refresh_braindump_list()
                braindump_text_widget.delete("1.0", tk.END)
                messagebox.showinfo("Deleted", f"Braindump for {date_str} has been deleted.")

        tk.Button(left_frame, text="Delete Selected", command=delete_braindump,
                bg=theme()["BTN"], fg="black").pack(pady=5, fill="x")
        
        # Scrollbar for Listbox
        lb_scroll = tk.Scrollbar(left_frame, orient=tk.VERTICAL, command=braindump_listbox.yview)
        lb_scroll.pack(side="right", fill="y")
        braindump_listbox.config(yscrollcommand=lb_scroll.set)

        # --- Right Panel: Text Area ---
        right_frame = tk.Frame(main_frame, bg=theme()["CARD"])
        right_frame.pack(side="right", fill="both", expand=True)

        # Date Selector
        date_frame = tk.Frame(right_frame, bg=theme()["CARD"])
        date_frame.pack(fill="x", pady=(0,5))
        tk.Label(date_frame, text="Viewing Date:", bg=theme()["CARD"], fg=theme()["TEXT"]).pack(side="left", padx=(0,5))
        braindump_date_entry = DateEntry(date_frame, width=12, date_pattern='yyyy-mm-dd', selectmode='day')
        braindump_date_entry.set_date(date.today())
        braindump_date_entry.pack(side="left")

        # Text area
        text_frame = tk.Frame(right_frame, bg=theme()["CARD"])
        text_frame.pack(fill="both", expand=True)
        scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL)
        braindump_text_widget = tk.Text(text_frame, wrap="word", font=("Segoe UI",10),
                                        bg=theme()["BG"], fg=theme()["TEXT"], insertbackground=theme()["TEXT"],
                                        yscrollcommand=scrollbar.set)
        scrollbar.config(command=braindump_text_widget.yview)
        scrollbar.pack(side="right", fill="y")
        braindump_text_widget.pack(side="left", fill="both", expand=True)

        # Save button
        tk.Button(right_frame, text="Save Braindump",
                command=lambda: save_braindump(braindump_date_entry.get_date()),
                bg=theme()["ACCENT"], fg="white", font=("Segoe UI",11,"bold")).pack(pady=5)

        # --- Functions ---
        def save_braindump(target_date):
            content_to_save = braindump_text_widget.get("1.0", tk.END).strip()
            date_iso = target_date.strftime("%Y-%m-%d")
            conn = db_connect()
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO braindumps (date, content) VALUES (?, ?)", (date_iso, content_to_save))
            conn.commit()
            conn.close()
            refresh_braindump_list()
            messagebox.showinfo("Saved", f"Braindump saved for {date_iso}.")

        def load_braindump(event=None):
            selected_date = braindump_date_entry.get_date()
            date_iso = selected_date.strftime("%Y-%m-%d")
            conn = db_connect()
            c = conn.cursor()
            row = c.execute("SELECT content FROM braindumps WHERE date = ?", (date_iso,)).fetchone()
            conn.close()
            braindump_text_widget.delete("1.0", tk.END)
            if row:
                braindump_text_widget.insert("1.0", row[0])
            else:
                braindump_text_widget.insert("1.0", f"Start your braindump for {date_iso} here...")

        def refresh_braindump_list():
            braindump_listbox.delete(0, tk.END)
            conn = db_connect()
            c = conn.cursor()
            rows = c.execute("SELECT date FROM braindumps ORDER BY date DESC").fetchall()
            conn.close()
            for r in rows:
                braindump_listbox.insert(tk.END, r[0])

        def load_selected_braindump(event):
            sel = braindump_listbox.curselection()
            if sel:
                date_str = braindump_listbox.get(sel[0])
                braindump_date_entry.set_date(datetime.strptime(date_str, "%Y-%m-%d"))
                load_braindump()

        # --- Bindings ---
        braindump_date_entry.bind("<<DateSelected>>", load_braindump)
        braindump_listbox.bind("<<ListboxSelect>>", load_selected_braindump)

        # --- Initial Load ---
        refresh_braindump_list()
        load_braindump()

        # Blank page update function
        def braindump_update_ui():
            refresh_braindump_list()
            load_braindump()
        pg.update_ui = braindump_update_ui
        
    # CALENDAR PAGE 
    if pn == "Calendar":
        # Ensure imports are at the top of your script: from tkcalendar import Calendar, DateEntry
        from tkcalendar import Calendar 
        global event_map, event_title_var, event_time_var, event_date_entry, status_label_var, event_listbox, calendar_widget
        
        # --- Form Variables ---
        event_title_var = tk.StringVar()
        event_time_var = tk.StringVar(value="1800") 
        status_label_var = tk.StringVar(value="Ready to add an event.")

        # --- 1. Top Frame (Form and Status) ---
        top_frame = tk.Frame(content, bg=theme()["CARD"])
        top_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(top_frame, text="📅 Add Event", 
                 font=("Segoe UI", 12, "bold"), 
                 bg=theme()["CARD"], fg=theme()["TEXT"]).pack(anchor="w", padx=5, pady=(5,0))
        
        # Container for the form elements
        form_frame = tk.Frame(top_frame, bg=theme()["CARD"])
        form_frame.pack(fill="x", padx=10, pady=5)
        
        # Title
        tk.Label(form_frame, text="Title:", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=0, column=0, sticky="w", padx=5)
        tk.Entry(form_frame, textvariable=event_title_var, width=25, bg=theme()["BG"], fg=theme()["TEXT"]).grid(row=0, column=1, padx=5)

        # Date Picker 
        tk.Label(form_frame, text="Date:", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=0, column=2, sticky="w", padx=5)
        event_date_entry = DateEntry(form_frame, width=10, date_pattern='yyyy-mm-dd', selectmode='day')
        event_date_entry.set_date(date.today()) 
        event_date_entry.grid(row=0, column=3, sticky="w", padx=5)
        
        # Time 
        tk.Label(form_frame, text="Time (HHMM):", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=0, column=4, sticky="w", padx=5)
        tk.Entry(form_frame, textvariable=event_time_var, width=6, bg=theme()["BG"], fg=theme()["TEXT"]).grid(row=0, column=5, sticky="w", padx=5)
        
        # Status Message
        tk.Label(top_frame, textvariable=status_label_var, font=("Segoe UI", 9),
                 bg=theme()["CARD"], fg=theme()["ACCENT"]).pack(anchor="w", padx=5, pady=(0, 5))

        # --- 2. Calendar and List Frame ---
        bottom_frame = tk.Frame(content, bg=theme()["BG"])
        bottom_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # 3. Calendar Widget (Left Side)
        calendar_widget = Calendar(bottom_frame, selectmode='day', 
                                      year=date.today().year, month=date.today().month, 
                                      day=date.today().day,
                                      # Use existing colors for required styling
                                      background=theme()["ACCENT"],      # Color for navigation bar
                                      foreground='white',
                                      normalbackground=theme()["BG"], 
                                      selectbackground=theme()["ACCENT"], # CRITICAL FIX: Use ACCENT instead of PRIMARY
                                      bordercolor=theme()["CARD"],        # CRITICAL FIX: Use CARD instead of PRIMARY
                                      headersbackground=theme()["CARD"])
        calendar_widget.pack(side="left", fill="y", padx=(0, 10))
        
        # 4. Event List (Right Side)
        event_list_frame = tk.Frame(bottom_frame, bg=theme()["BG"])
        event_list_frame.pack(side="right", fill="both", expand=True)

        tk.Label(event_list_frame, text="Events for Selected Day:", font=("Segoe UI", 10, "bold"),
                 bg=theme()["BG"], fg=theme()["TEXT"]).pack(anchor="w")

        event_listbox = tk.Text(event_list_frame, height=10, state="disabled", 
                                   bg=theme()["CARD"], fg=theme()["TEXT"], wrap="word")
        event_listbox.pack(fill="both", expand=True)
        
        # --- Core Functions ---
        
        def load_events(target_date):
            """Loads and displays events for the selected date."""
            selected_date_iso = target_date.strftime("%Y-%m-%d")
            
            # Reset the event map every time we load new data
            global event_map # Access the global map
            event_map = {}
            
            conn = db_connect()
            c = conn.cursor()
            # CRITICAL CHANGE: Fetch the 'id' as the first column
            rows = c.execute("SELECT id, title, event_time FROM events WHERE event_date = ? ORDER BY event_time ASC", 
                             (selected_date_iso,)).fetchall()
            conn.close()

            event_listbox.config(state="normal")
            event_listbox.delete("1.0", tk.END)
            
            if rows:
                event_listbox.insert(tk.END, f"--- {selected_date_iso} ---\n\n")
                
                for i, (event_id, title, time) in enumerate(rows): # Unpack the ID
                    display_time = f"{time[:2]}:{time[2:]}" if time and len(time) == 4 else ""
                    
                    line_text = f"• {display_time:<6} {title}\n"
                    event_listbox.insert(tk.END, line_text)
                    
                    # Map the current line number to the database ID
                    # Line numbers in Text widgets are 'line.char' (e.g., '3.0')
                    # The event list starts after the header (usually line 3)
                    # We store the unique ID using a key based on the row index 'i'
                    event_map[i] = event_id 

            else:
                event_listbox.insert(tk.END, f"No events scheduled for {selected_date_iso}.\n")

            event_listbox.config(state="disabled")
        
        def delete_event_by_click(event):
            """Identifies the event line clicked and deletes the corresponding entry."""
            global event_map
            
            # The Text widget is disabled, so we re-enable to get the index, then re-disable
            event_listbox.config(state="normal")
            
            # Get the line index where the user double-clicked
            try:
                # Get the 'line.0' index where the click occurred
                index_line = event_listbox.index(f"@{event.x},{event.y}")
                line_number = int(float(index_line))
            except:
                event_listbox.config(state="disabled")
                return
            
            event_listbox.config(state="disabled")
            
            # Event rows start on line 3 (after the header and blank line)
            # The row index 'i' in event_map is zero-based (0, 1, 2, ...)
            listbox_row_index = line_number - 3 

            if listbox_row_index in event_map:
                event_id = event_map[listbox_row_index]
                
                # Confirmation before deletion
                if messagebox.askyesno("Delete Event", f"Are you sure you want to delete this event (ID: {event_id})?"):
                    conn = db_connect()
                    c = conn.cursor()
                    c.execute("DELETE FROM events WHERE id = ?", (event_id,))
                    conn.commit()
                    conn.close()
                    
                    # Refresh the list for the selected day
                    selected_date = calendar_widget.selection_get()
                    load_events(selected_date)
                    status_label_var.set("Event deleted successfully.")
            else:
                status_label_var.set("Click a valid event line to delete.")
        
        def add_calendar_event(title_var, date_entry, time_var):
            """Gathers form data and saves the event locally."""
            title = event_title_var.get().strip()
            time_str = event_time_var.get().strip()
            date_obj = event_date_entry.get_date()
            
            if not title:
                status_label_var.set("Error: Title is required.")
                return
            if not time_str or len(time_str) != 4 or not time_str.isdigit():
                status_label_var.set("Error: Time must be HHMM (24h).")
                return

            date_iso = date_obj.strftime("%Y-%m-%d")
            
            # Save to database
            conn = db_connect()
            c = conn.cursor()
            c.execute("INSERT INTO events (title, event_date, event_time) VALUES (?, ?, ?)", 
                      (title, date_iso, time_str))
            
            conn.commit()
            conn.close()
            
            # Update UI
            pg.event_title_var.set("")
            pg.status_label_var.set(f"'{title}' scheduled for {date_iso} at {time_str[:2]}:{time_str[2:]}.")
            
            # Refresh the list for the newly added event
            load_events(date_obj)

        # Submission Button (UPDATED COMMAND)
        tk.Button(form_frame, text="Save Event", 
                  # CRITICAL FIX: The lambda uses the new global names
                  command=lambda: add_calendar_event(event_title_var, event_date_entry, event_time_var), 
                  bg=theme()["ACCENT"], fg="white", font=("Segoe UI", 10, "bold")).grid(row=0, column=6, padx=10, sticky="w")
        # Binding the Calendar Widget: Load events whenever a date is selected
        calendar_widget.bind("<<CalendarSelected>>", lambda event: load_events(calendar_widget.selection_get()))
        # CRITICAL BINDING: Double-click to delete
        event_listbox.bind("<Double-1>", delete_event_by_click)

        # Initial Load: Show events for today
        load_events(date.today())

        # Attach Blank Update Function for stability
        def placeholder_update_ui():
            pass 
        pg.update_ui = placeholder_update_ui
        pg.update_ui()
    
    # NOTES PAGE
    if pn == "Notes":
        import sqlite3
        import uuid
        import tkinter as tk
        from tkinter import ttk, messagebox, simpledialog
        from tkinter import scrolledtext
        from datetime import datetime

        t = theme()  # your theme dict

        # --- Helpers ---
        NOTES_DB_PATH = "mochi.db"

        def get_notes_conn():
            conn = sqlite3.connect(NOTES_DB_PATH)
            return conn, conn.cursor()

        def uid():
            return str(uuid.uuid4())

        # --- Ensure tables exist (init_db should also include this but safe to ensure here) ---
        conn, cur = get_notes_conn()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS notes_folders (
                folder_uid TEXT PRIMARY KEY,
                parent_uid TEXT,
                folder_name TEXT NOT NULL,
                created_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS notes_items (
                note_uid TEXT PRIMARY KEY,
                folder_uid TEXT,
                note_title TEXT NOT NULL,
                note_content TEXT,
                created_at TEXT
            )
        """)
        conn.commit()
        conn.close()

        # --- Clear page ---
        for w in pg.winfo_children():
            w.destroy()
        pg.configure(bg=t["BG"])

        # --- Main Paned layout: left = folders tree, right = notes list/editor controls ---
        paned = ttk.Panedwindow(pg, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True, padx=10, pady=8)

        left_frame = tk.Frame(paned, bg=t["BG"])
        right_frame = tk.Frame(paned, bg=t["BG"])
        paned.add(left_frame, weight=1)
        paned.add(right_frame, weight=3)

        # --- Left: Folder controls and Treeview ---
        left_top = tk.Frame(left_frame, bg=t["BG"])
        left_top.pack(fill="x", pady=(0,6))

        # Entry + Add top-level folder
        folder_name_entry = ttk.Entry(left_top, width=24)
        folder_name_entry.pack(side="left", padx=(0,6))
        def add_top_folder():
            name = folder_name_entry.get().strip()
            if not name:
                messagebox.showwarning("Input Error", "Folder name required.")
                return
            conn, cur = get_notes_conn()
            cur.execute("INSERT INTO notes_folders (folder_uid, parent_uid, folder_name, created_at) VALUES (?, ?, ?, ?)",
                        (uid(), None, name, datetime.now().isoformat()))
            conn.commit(); conn.close()
            folder_name_entry.delete(0, tk.END)
            rebuild_tree()

        tk.Button(left_top, text="Add Folder", bg=t["BTN"], activebackground=t["BTN_HOVER"],
                relief="flat", command=add_top_folder).pack(side="left", padx=(0,6))

        # Treeview
        tree_frame = tk.Frame(left_frame, bg=t["CARD"], bd=0)
        tree_frame.pack(fill="both", expand=True)
        folder_tree = ttk.Treeview(tree_frame, show="tree")
        folder_tree.pack(side="left", fill="both", expand=True)
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=folder_tree.yview)
        tree_scroll.pack(side="right", fill="y")
        folder_tree.configure(yscrollcommand=tree_scroll.set)

        # Folder action buttons
        left_bot = tk.Frame(left_frame, bg=t["BG"])
        left_bot.pack(fill="x", pady=(6,0))
        def add_subfolder():
            sel = folder_tree.selection()
            if not sel:
                messagebox.showwarning("Select Folder", "Select a parent folder first.")
                return
            parent = sel[0]
            name = simpledialog.askstring("New Subfolder", "Subfolder name:", parent=pg)
            if not name:
                return
            conn, cur = get_notes_conn()
            cur.execute("INSERT INTO notes_folders (folder_uid, parent_uid, folder_name, created_at) VALUES (?, ?, ?, ?)",
                        (uid(), parent, name, datetime.now().isoformat()))
            conn.commit(); conn.close()
            rebuild_tree()
            folder_tree.selection_set(parent)  # keep parent selected

        def rename_folder():
            sel = folder_tree.selection()
            if not sel:
                messagebox.showwarning("Select Folder", "Select a folder to rename.")
                return
            fid = sel[0]
            conn, cur = get_notes_conn()
            cur.execute("SELECT folder_name FROM notes_folders WHERE folder_uid=?", (fid,))
            row = cur.fetchone()
            conn.close()
            current = row[0] if row else ""
            new = simpledialog.askstring("Rename Folder", "New name:", initialvalue=current, parent=pg)
            if new and new.strip():
                conn, cur = get_notes_conn()
                cur.execute("UPDATE notes_folders SET folder_name=? WHERE folder_uid=?", (new.strip(), fid))
                conn.commit(); conn.close()
                rebuild_tree()
                folder_tree.selection_set(fid)

        def delete_folder_action():
            sel = folder_tree.selection()
            if not sel:
                messagebox.showwarning("Select Folder", "Select a folder to delete.")
                return
            fid = sel[0]
            if not messagebox.askyesno("Delete Folder", "Delete folder and all subfolders & notes?"):
                return
            # recursive delete
            def delete_folder_recursive(fuid):
                conn, cur = get_notes_conn()
                # delete notes in folder
                cur.execute("DELETE FROM notes_items WHERE folder_uid=?", (fuid,))
                # find subfolders
                cur.execute("SELECT folder_uid FROM notes_folders WHERE parent_uid=?", (fuid,))
                subs = cur.fetchall()
                for s in subs:
                    delete_folder_recursive(s[0])
                cur.execute("DELETE FROM notes_folders WHERE folder_uid=?", (fuid,))
                conn.commit(); conn.close()
            delete_folder_recursive(fid)
            rebuild_tree()

        tk.Button(left_bot, text="+Subfolder", bg=t["BTN"], relief="flat", command=add_subfolder).pack(side="left", padx=6)
        tk.Button(left_bot, text="Rename", bg=t["BTN"], relief="flat", command=rename_folder).pack(side="left", padx=6)
        tk.Button(left_bot, text="Delete", bg="#E57373", fg="white", relief="flat", command=delete_folder_action).pack(side="left", padx=6)

        # --- Right: Notes list and controls ---
        right_top = tk.Frame(right_frame, bg=t["BG"])
        right_top.pack(fill="x", pady=(0,6))
        notes_title_label = tk.Label(right_top, text="Notes", font=("Segoe UI", 13, "bold"), bg=t["BG"], fg=t["TEXT"])
        notes_title_label.pack(anchor="w", padx=6)

        right_controls = tk.Frame(right_frame, bg=t["BG"])
        right_controls.pack(fill="x", pady=(0,6))
        note_title_add_entry = ttk.Entry(right_controls, width=36)
        note_title_add_entry.pack(side="left", padx=(6,6))

        def add_note_action():
            sel = folder_tree.selection()
            if not sel:
                messagebox.showwarning("Select Folder", "Select a folder to add a note into.")
                return
            folder_id = sel[0]
            title = note_title_add_entry.get().strip()
            if not title:
                messagebox.showwarning("Input Error", "Note title cannot be empty.")
                return
            conn, cur = get_notes_conn()
            cur.execute("INSERT INTO notes_items (note_uid, folder_uid, note_title, note_content, created_at) VALUES (?, ?, ?, ?, ?)",
                        (uid(), folder_id, title, "", datetime.now().isoformat()))
            conn.commit(); conn.close()
            note_title_add_entry.delete(0, tk.END)
            load_notes_for_folder(folder_id)

        tk.Button(right_controls, text="Add Note", bg=t["BTN"], relief="flat", command=add_note_action).pack(side="left", padx=(0,8))
        tk.Button(right_controls, text="Edit Note", bg=t["BTN"], relief="flat", command=lambda: edit_selected_note()).pack(side="left", padx=6)
        tk.Button(right_controls, text="Delete Note", bg="#E57373", fg="white", relief="flat", command=lambda: delete_selected_note()).pack(side="left", padx=6)

        # Notes list (single column)
        notes_list_frame = tk.Frame(right_frame, bg=t["CARD"], bd=0)
        notes_list_frame.pack(fill="both", expand=True, padx=6, pady=(4,6))
        notes_tree = ttk.Treeview(notes_list_frame, columns=("title", "date"), show="headings", selectmode="browse")
        notes_tree.heading("title", text="Title")
        notes_tree.heading("date", text="Created")
        notes_tree.column("title", width=400)
        notes_tree.column("date", width=110)
        notes_tree.pack(side="left", fill="both", expand=True)
        notes_scroll = ttk.Scrollbar(notes_list_frame, orient="vertical", command=notes_tree.yview)
        notes_scroll.pack(side="right", fill="y")
        notes_tree.configure(yscrollcommand=notes_scroll.set)

        # --- Core functions: build tree and load notes ---
        def build_tree(parent_tree_parent=""):
            """Insert top-level folders into the tree, recursively."""
            folder_tree.delete(*folder_tree.get_children())
            conn, cur = get_notes_conn()
            cur.execute("SELECT folder_uid, folder_name FROM notes_folders WHERE parent_uid IS NULL ORDER BY folder_name COLLATE NOCASE")
            tops = cur.fetchall()
            # insert recursive helper
            def insert_children(sql_parent, tree_parent):
                cur.execute("SELECT folder_uid, folder_name FROM notes_folders WHERE parent_uid=? ORDER BY folder_name COLLATE NOCASE", (sql_parent,))
                children = cur.fetchall()
                for cid, cname in children:
                    folder_tree.insert(tree_parent, "end", iid=cid, text=cname, open=False)
                    insert_children(cid, cid)
            for fid, fname in tops:
                folder_tree.insert("", "end", iid=fid, text=fname, open=False)
                insert_children(fid, fid)
            conn.close()

        def rebuild_tree():
            build_tree()
            notes_tree.delete(*notes_tree.get_children())
            notes_title_label.config(text="Notes")

        def load_notes_for_folder(folder_id):
            notes_tree.delete(*notes_tree.get_children())
            conn, cur = get_notes_conn()
            cur.execute("SELECT note_uid, note_title, created_at FROM notes_items WHERE folder_uid=? ORDER BY created_at DESC", (folder_id,))
            rows = cur.fetchall()
            conn.close()
            for nid, nt, created in rows:
                notes_tree.insert("", "end", iid=nid, values=(nt, created if created else ""))
            # update right-hand title
            folder_name = folder_tree.item(folder_id, "text")
            notes_title_label.config(text=f"Notes — {folder_name}")

        # Bind folder selection to load notes
        def on_folder_select(event):
            sel = folder_tree.selection()
            if not sel:
                return
            fid = sel[0]
            load_notes_for_folder(fid)

        folder_tree.bind("<<TreeviewSelect>>", on_folder_select)

        # --- Note edit/delete helpers ---
        def get_selected_note_id():
            sel = notes_tree.selection()
            return sel[0] if sel else None

        def edit_selected_note():
            nid = get_selected_note_id()
            if not nid:
                messagebox.showwarning("Select Note", "Select a note to edit.")
                return
            conn, cur = get_notes_conn()
            cur.execute("SELECT note_title, note_content, folder_uid FROM notes_items WHERE note_uid=?", (nid,))
            row = cur.fetchone()
            conn.close()
            if not row:
                messagebox.showerror("Not found", "Note not found in DB.")
                return
            title_val, content_val, folder_id = row
            edit_win = tk.Toplevel(pg)
            edit_win.title("Edit Note")
            edit_win.geometry("720x560")
            edit_win.transient(pg)
            edit_win.configure(bg=t["BG"])
            tk.Label(edit_win, text="Title:", bg=t["BG"], fg=t["TEXT"]).pack(anchor="w", padx=10, pady=(10,0))
            title_var = tk.StringVar(value=title_val)
            title_entry_e = ttk.Entry(edit_win, textvariable=title_var, width=80)
            title_entry_e.pack(padx=10, pady=6)
            tk.Label(edit_win, text="Content:", bg=t["BG"], fg=t["TEXT"]).pack(anchor="w", padx=10, pady=(6,0))
            content_text = scrolledtext.ScrolledText(edit_win, wrap=tk.WORD)
            content_text.pack(fill="both", expand=True, padx=10, pady=8)
            content_text.insert("1.0", content_val or "")

            def save_note_edit():
                new_title = title_var.get().strip()
                new_content = content_text.get("1.0", tk.END).rstrip("\n")
                if not new_title:
                    messagebox.showwarning("Input Error", "Title required.", parent=edit_win)
                    return
                conn, cur = get_notes_conn()
                cur.execute("UPDATE notes_items SET note_title=?, note_content=? WHERE note_uid=?", (new_title, new_content, nid))
                conn.commit(); conn.close()
                edit_win.destroy()
                load_notes_for_folder(folder_id)

            tk.Button(edit_win, text="Save", bg=t["BTN"], relief="flat", command=save_note_edit).pack(pady=8)

        def delete_selected_note():
            nid = get_selected_note_id()
            if not nid:
                messagebox.showwarning("Select Note", "Select a note to delete.")
                return
            if not messagebox.askyesno("Delete Note", "Delete this note?"):
                return
            conn, cur = get_notes_conn()
            # find folder to reload after deletion
            cur.execute("SELECT folder_uid FROM notes_items WHERE note_uid=?", (nid,))
            row = cur.fetchone()
            folder_id = row[0] if row else None
            cur.execute("DELETE FROM notes_items WHERE note_uid=?", (nid,))
            conn.commit(); conn.close()
            if folder_id:
                load_notes_for_folder(folder_id)
            else:
                rebuild_tree()

        # --- initial build ---
        rebuild_tree()
        
    # SLEEP TRACKER PAGE
    if pn == "Sleep":
        for widget in pg.winfo_children():
            widget.destroy()

        global sleep_date_entry, sleep_bed_entry, sleep_wake_entry
        global sleep_duration_label, sleep_listbox, sleep_chart_frame
        global selected_sleep_id

        from datetime import datetime, timedelta, date
        import matplotlib.dates as mdates
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        selected_sleep_id = None  # track selected entry

        # --- DATABASE UTILITY ---
        def run_sleep_query(query, params=()):
            try:
                conn = sqlite3.connect("mochi.db")
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                results = cursor.fetchall()
                conn.close()
                return results
            except Exception as e:
                print("DB error:", e)
                return []

        # --- CALCULATE SLEEP DURATION ---
        def calc_sleep_duration(wake_date_str, bed_time_str, wake_time_str):
            wake_dt = datetime.strptime(f"{wake_date_str} {wake_time_str}", "%Y-%m-%d %H:%M")
            bed_dt = datetime.strptime(f"{wake_date_str} {bed_time_str}", "%Y-%m-%d %H:%M")
            if bed_dt > wake_dt:
                bed_dt -= timedelta(days=1)
            duration_min = (wake_dt - bed_dt).total_seconds() / 60
            if duration_min <= 0:
                raise ValueError("Wake time must be later than bed time or next day.")
            return duration_min

        # --- LOG NEW SLEEP ENTRY ---
        def log_sleep_entry():
            try:
                duration_min = calc_sleep_duration(
                    sleep_date_entry.get(),
                    sleep_bed_entry.get(),
                    sleep_wake_entry.get()
                )
                run_sleep_query(
                    "INSERT INTO user_sleep_log (sleep_date, bed_time, wake_time, duration_minutes) VALUES (?, ?, ?, ?)",
                    (sleep_date_entry.get(), sleep_bed_entry.get(), sleep_wake_entry.get(), duration_min)
                )
                messagebox.showinfo("Success", f"Logged {duration_min/60:.2f} hours of sleep!")
                clear_inputs()
                load_sleep_summary()
                load_sleep_list()
                plot_sleep_trend()
            except ValueError as e:
                messagebox.showerror("Error", str(e))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save entry: {e}")

        # --- UPDATE EXISTING ENTRY ---
        def update_sleep_entry():
            global selected_sleep_id
            if not selected_sleep_id:
                messagebox.showwarning("No Selection", "Please select a sleep log to edit.")
                return
            try:
                duration_min = calc_sleep_duration(
                    sleep_date_entry.get(),
                    sleep_bed_entry.get(),
                    sleep_wake_entry.get()
                )
                run_sleep_query(
                    "UPDATE user_sleep_log SET sleep_date=?, bed_time=?, wake_time=?, duration_minutes=? WHERE sleep_id=?",
                    (sleep_date_entry.get(), sleep_bed_entry.get(), sleep_wake_entry.get(), duration_min, selected_sleep_id)
                )
                messagebox.showinfo("Updated", "Sleep log updated successfully.")
                selected_sleep_id = None
                clear_inputs()
                load_sleep_summary()
                load_sleep_list()
                plot_sleep_trend()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update entry: {e}")

        # --- DELETE SLEEP ENTRY ---
        def delete_sleep_entry():
            global selected_sleep_id
            if not selected_sleep_id:
                messagebox.showwarning("No Selection", "Please select a sleep log to delete.")
                return
            confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this sleep entry?")
            if confirm:
                try:
                    run_sleep_query("DELETE FROM user_sleep_log WHERE sleep_id=?", (selected_sleep_id,))
                    messagebox.showinfo("Deleted", "Sleep entry deleted successfully.")
                    selected_sleep_id = None
                    clear_inputs()
                    load_sleep_summary()
                    load_sleep_list()
                    plot_sleep_trend()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete entry: {e}")

        # --- CLEAR INPUTS ---
        def clear_inputs():
            sleep_date_entry.delete(0, tk.END)
            sleep_date_entry.insert(0, date.today().strftime("%Y-%m-%d"))
            sleep_bed_entry.delete(0, tk.END)
            sleep_wake_entry.delete(0, tk.END)

        # --- LOAD LATEST SUMMARY ---
        def load_sleep_summary():
            rows = run_sleep_query("SELECT sleep_date, duration_minutes FROM user_sleep_log ORDER BY sleep_id DESC LIMIT 1")
            if rows:
                dur_min = rows[0][1]
                hours = int(dur_min // 60)
                mins = int(dur_min % 60)
                sleep_duration_label.config(text=f"{hours}h {mins}m")
            else:
                sleep_duration_label.config(text="No data yet.")

        # --- LOAD SLEEP LIST ---
        def load_sleep_list():
            sleep_listbox.delete(0, tk.END)
            rows = run_sleep_query("SELECT sleep_id, sleep_date, bed_time, wake_time, duration_minutes FROM user_sleep_log ORDER BY sleep_date DESC")
            if not rows:
                sleep_listbox.insert(tk.END, "No sleep data yet.")
                return
            for r in rows:
                sid, sdate, bed, wake, dur = r
                h, m = int(dur // 60), int(dur % 60)
                sleep_listbox.insert(tk.END, f"#{sid} | {sdate} | {bed}-{wake} ({h}h {m}m)")

        # --- SELECT ENTRY ---
        def on_select_sleep(event):
            global selected_sleep_id
            try:
                selection = sleep_listbox.get(sleep_listbox.curselection())
                if not selection.startswith("#"):
                    return
                sid = int(selection.split("|")[0].replace("#", "").strip())
                row = run_sleep_query("SELECT sleep_id, sleep_date, bed_time, wake_time FROM user_sleep_log WHERE sleep_id=?", (sid,))
                if row:
                    selected_sleep_id = sid
                    sleep_date_entry.delete(0, tk.END)
                    sleep_date_entry.insert(0, row[0][1])
                    sleep_bed_entry.delete(0, tk.END)
                    sleep_bed_entry.insert(0, row[0][2])
                    sleep_wake_entry.delete(0, tk.END)
                    sleep_wake_entry.insert(0, row[0][3])
            except Exception as e:
                print("Selection error:", e)

        # --- PLOT TREND ---
        def plot_sleep_trend():
            for widget in sleep_chart_frame.winfo_children():
                widget.destroy()
            trend = run_sleep_query("SELECT sleep_date, duration_minutes FROM user_sleep_log ORDER BY sleep_id ASC")
            if not trend:
                return
            dates, hours = [], []
            for r in trend:
                try:
                    dt = datetime.strptime(r[0], "%Y-%m-%d")
                    dates.append(dt)
                    hours.append(r[1] / 60)
                except Exception as e:
                    print("Skipping invalid date", e)

            fig = Figure(figsize=(4, 2.5), dpi=100)
            ax = fig.add_subplot(111)
            fig.patch.set_facecolor(theme()["BG"])
            ax.set_facecolor("white")
            ax.plot(dates, hours, marker='o', color=theme()["ACCENT"])
            ax.fill_between(dates, hours, color=theme()["ACCENT"], alpha=0.2)
            ax.set_title("Sleep Trend (Hours)", fontsize=11, fontweight="bold")
            ax.set_ylabel("Hours", fontsize=9)
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
            fig.autofmt_xdate(rotation=45)
            ax.set_ylim(bottom=0)
            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=sleep_chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

        # --- UI ---
        tk.Label(pg, text="💤 Sleep Tracker", font=("Segoe UI", 16, "bold"), bg=theme()["BG"]).pack(pady=10)

        input_frame = tk.Frame(pg, bg=theme()["BG"])
        input_frame.pack(side="left", padx=10, pady=10, fill="y")

        tk.Label(input_frame, text="Wake Date (YYYY-MM-DD):", bg=theme()["BG"]).grid(row=0, column=0, sticky="w")
        sleep_date_entry = ttk.Entry(input_frame, width=15)
        sleep_date_entry.grid(row=0, column=1, padx=5, pady=5)
        sleep_date_entry.insert(0, date.today().strftime("%Y-%m-%d"))

        tk.Label(input_frame, text="Bed Time (HH:MM):", bg=theme()["BG"]).grid(row=1, column=0, sticky="w")
        sleep_bed_entry = tk.Entry(input_frame, width=8)
        sleep_bed_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(input_frame, text="Wake Time (HH:MM):", bg=theme()["BG"]).grid(row=2, column=0, sticky="w")
        sleep_wake_entry = tk.Entry(input_frame, width=8)
        sleep_wake_entry.grid(row=2, column=1, padx=5, pady=5)

        tk.Button(input_frame, text="Log Sleep", command=log_sleep_entry, bg=theme()["ACCENT"], fg="white").grid(row=3, column=0, columnspan=2, pady=5)
        tk.Button(input_frame, text="Update Sleep", command=update_sleep_entry, bg=theme()["BTN"], fg="black").grid(row=4, column=0, columnspan=2, pady=5)
        tk.Button(input_frame, text="🗑 Delete Sleep", command=delete_sleep_entry, bg="#ff6b6b", fg="white").grid(row=5, column=0, columnspan=2, pady=5)

        # Sleep List
        sleep_list_frame = tk.Frame(pg, bg=theme()["BG"])
        sleep_list_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        tk.Label(sleep_list_frame, text="📝 Sleep Logs", font=("Segoe UI", 11, "bold"), bg=theme()["BG"]).pack(anchor="w")
        sleep_listbox = tk.Listbox(sleep_list_frame, height=12, bg=theme()["CARD"], fg=theme()["TEXT"], font=("Segoe UI", 10))
        sleep_listbox.pack(fill="both", expand=True)
        sleep_listbox.bind("<<ListboxSelect>>", on_select_sleep)

        # Summary & Chart
        summary_frame = tk.Frame(pg, bg=theme()["BG"])
        summary_frame.pack(side="right", padx=10, pady=10, fill="both", expand=True)

        tk.Label(summary_frame, text="✨ Last Session", font=("Segoe UI", 12, "bold"), bg=theme()["BG"]).pack(pady=5)
        sleep_duration_label = tk.Label(summary_frame, text="0h 0m", font=("Segoe UI", 24, "bold"), bg=theme()["BG"])
        sleep_duration_label.pack(pady=10)

        tk.Label(summary_frame, text="📈 Sleep Trend", font=("Segoe UI", 12, "bold"), bg=theme()["BG"]).pack(pady=(10, 5))
        sleep_chart_frame = tk.Frame(summary_frame, bg=theme()["BG"])
        sleep_chart_frame.pack(fill="both", expand=True)

        # INITIAL LOAD
        load_sleep_summary()
        load_sleep_list()
        plot_sleep_trend()
        
    # FILES PAGE
    if pn == "Files":
        import tkinter as tk
        from tkinter import filedialog, messagebox, simpledialog
        import shutil, os, webbrowser, sqlite3, uuid
        from datetime import datetime

        t = theme()

        # --- DB FUNCTIONS ---
        def get_files_connection():
            conn = sqlite3.connect("mochi.db")
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS study_imported_files (
                    import_uid TEXT PRIMARY KEY,
                    file_name TEXT NOT NULL,
                    file_type TEXT,
                    stored_path TEXT NOT NULL,
                    date_imported TEXT NOT NULL
                )
            """)
            conn.commit()
            return conn, cursor

        # --- PAGE RESET ---
        for widget in pg.winfo_children():
            widget.destroy()
        pg.configure(bg=t["BG"])

        # --- HEADER ---
        header_frame = tk.Frame(pg, bg=t["BG"])
        header_frame.pack(fill="x", pady=(10, 5), padx=10)
        tk.Label(header_frame, text="📂 Files", font=("Segoe UI", 16, "bold"), bg=t["CARD"], fg=t["TEXT"]).pack(anchor="w")

        # --- LIST CONTAINER ---
        list_frame = tk.Frame(pg, bg=t["CARD"], bd=1, relief="solid")
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        canvas = tk.Canvas(list_frame, bg=t["CARD"], highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        inner_frame = tk.Frame(canvas, bg=t["CARD"])
        canvas.create_window((0, 0), window=inner_frame, anchor="nw")

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        inner_frame.bind("<Configure>", on_frame_configure)

        # --- FILE OPERATIONS ---
        def open_file(path):
            try:
                abs_path = os.path.abspath(path)
                webbrowser.open(abs_path)
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file:\n{e}")

        def delete_file(uid, stored_path):
            if not messagebox.askyesno("Confirm Delete", "Delete this file?"):
                return
            try:
                if os.path.exists(stored_path):
                    os.remove(stored_path)
                conn, cursor = get_files_connection()
                cursor.execute("DELETE FROM study_imported_files WHERE import_uid=?", (uid,))
                conn.commit()
                conn.close()
                load_files()
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete file:\n{e}")

        def rename_file(uid, old_name, stored_path):
            new_name = simpledialog.askstring("Rename File", "Enter new name:", initialvalue=old_name)
            if not new_name or new_name.strip() == "":
                return
            new_name = new_name.strip()
            try:
                conn, cursor = get_files_connection()
                cursor.execute("UPDATE study_imported_files SET file_name=? WHERE import_uid=?", (new_name, uid))
                conn.commit()
                conn.close()
                load_files()
            except Exception as e:
                messagebox.showerror("Error", f"Could not rename file:\n{e}")

        # --- LOAD FILES ---
        def load_files(search_term=""):
            for w in inner_frame.winfo_children():
                w.destroy()

            conn, cursor = get_files_connection()
            if search_term:
                cursor.execute("""
                    SELECT import_uid, file_name, file_type, stored_path, date_imported
                    FROM study_imported_files
                    WHERE file_name LIKE ?
                    ORDER BY date_imported DESC
                """, (f"%{search_term}%",))
            else:
                cursor.execute("""
                    SELECT import_uid, file_name, file_type, stored_path, date_imported
                    FROM study_imported_files
                    ORDER BY date_imported DESC
                """)
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                tk.Label(inner_frame, text="No files found.", bg=t["CARD"], fg=t["TEXT_LIGHT"],
                        font=("Segoe UI", 10, "italic")).pack(pady=10)
                return

            for uid, name, ftype, path, date in rows:
                item = tk.Frame(inner_frame, bg=t["CARD"], pady=5)
                item.pack(fill="x", padx=10, pady=3)

                name_label = tk.Label(item, text=name, bg=t["CARD"], fg=t["TEXT"], font=("Segoe UI", 10, "bold"))
                name_label.pack(anchor="w")

                tk.Label(item, text=f"{ftype or ''} • Imported on {date.split('T')[0]}", bg=t["CARD"], fg=t["TEXT_LIGHT"],
                        font=("Segoe UI", 8)).pack(anchor="w")

                btns = tk.Frame(item, bg=t["CARD"])
                btns.pack(anchor="e", pady=2)
                tk.Button(btns, text="Open", bg=t["BTN"], activebackground=t["BTN_HOVER"], relief="flat",
                        command=lambda p=path: open_file(p)).pack(side="left", padx=3)
                tk.Button(btns, text="Rename", bg=t["ACCENT"], relief="flat",
                        command=lambda u=uid, n=name, p=path: rename_file(u, n, p)).pack(side="left", padx=3)
                tk.Button(btns, text="Delete", bg="#E57373", fg="white", relief="flat",
                        command=lambda u=uid, p=path: delete_file(u, p)).pack(side="left", padx=3)

            inner_frame.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))

        # --- TOOLBAR (AFTER load_files DEFINED) ---
        toolbar = tk.Frame(pg, bg=t["BG"])
        toolbar.pack(fill="x", padx=10, pady=(5, 10))

        search_var = tk.StringVar()

        def on_search(*args):
            load_files(search_var.get().strip())

        search_var.trace("w", on_search)

        search_entry = tk.Entry(toolbar, textvariable=search_var, bg=t["CARD"], fg=t["TEXT"], relief="flat",
                                font=("Segoe UI", 10))
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5), ipady=3)
        search_entry.insert(0, "Search files...")

        def clear_search(event):
            if search_entry.get() == "Search files...":
                search_entry.delete(0, "end")

        def restore_search(event):
            if not search_entry.get():
                search_entry.insert(0, "Search files...")

        search_entry.bind("<FocusIn>", clear_search)
        search_entry.bind("<FocusOut>", restore_search)

        def import_file():
            file_path = filedialog.askopenfilename(title="Select File")
            if not file_path:
                return

            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_name)[1]
            import_uid = str(uuid.uuid4())

            local_folder = "imported_files"
            os.makedirs(local_folder, exist_ok=True)
            stored_path = os.path.join(local_folder, f"{import_uid}{file_ext}")

            try:
                shutil.copy2(file_path, stored_path)
                conn, cursor = get_files_connection()
                cursor.execute("""
                    INSERT INTO study_imported_files (import_uid, file_name, file_type, stored_path, date_imported)
                    VALUES (?, ?, ?, ?, ?)
                """, (import_uid, file_name, file_ext, stored_path, datetime.now().isoformat()))
                conn.commit()
                conn.close()
                load_files()
            except Exception as e:
                messagebox.showerror("Import Error", f"Could not import file:\n{e}")

        tk.Button(toolbar, text="Import", bg=t["BTN"], activebackground=t["BTN_HOVER"], relief="flat",
                command=import_file).pack(side="left", padx=5)

        # --- INITIAL LOAD ---
        load_files()

    # FLASHCARD PAGE
    if pn == "Flashcard":
        import tkinter as tk
        from tkinter import ttk, messagebox, simpledialog
        from tkinter import scrolledtext
        import sqlite3
        import uuid
        import random
        import os
        from datetime import datetime

        t = theme()  # use your app theme (must be present)

        DB_PATH = "mochi.db"

        # -------------------------
        # DB helper
        # -------------------------
        def get_flash_conn():
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            # Decks table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS study_flashcard_decks (
                    deck_uid TEXT PRIMARY KEY,
                    deck_name TEXT NOT NULL,
                    created_at TEXT
                )
            """)
            # Cards table with status column ('new', 'known', 'review')
            cur.execute("""
                CREATE TABLE IF NOT EXISTS study_flashcards (
                    card_uid TEXT PRIMARY KEY,
                    deck_uid TEXT NOT NULL,
                    front_text TEXT NOT NULL,
                    back_text TEXT NOT NULL,
                    status TEXT DEFAULT 'new',
                    created_at TEXT,
                    FOREIGN KEY(deck_uid) REFERENCES study_flashcard_decks(deck_uid)
                )
            """)
            conn.commit()
            return conn, cur

        def new_uid():
            return str(uuid.uuid4())

        # -------------------------
        # Reset page
        # -------------------------
        for w in pg.winfo_children():
            w.destroy()
        pg.configure(bg=t["BG"])

        # Title
        tk.Label(pg, text="Flashcards", font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=12, pady=(10,6))

        paned = ttk.Panedwindow(pg, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True, padx=10, pady=8)

        left_frame = tk.Frame(paned, bg=t["BG"])
        right_frame = tk.Frame(paned, bg=t["BG"])
        paned.add(left_frame, weight=1)
        paned.add(right_frame, weight=3)

        # -------------------------
        # Left: Deck list + controls
        # -------------------------
        left_top = tk.Frame(left_frame, bg=t["BG"])
        left_top.pack(fill="x", padx=6, pady=(0,6))

        deck_new_entry = ttk.Entry(left_top, width=20)
        deck_new_entry.pack(side="left", padx=(0,6))

        def add_deck():
            name = deck_new_entry.get().strip()
            if not name:
                messagebox.showwarning("Input Error", "Deck name required.")
                return
            conn, cur = get_flash_conn()
            cur.execute("INSERT INTO study_flashcard_decks (deck_uid, deck_name, created_at) VALUES (?, ?, ?)",
                        (new_uid(), name, datetime.now().isoformat()))
            conn.commit(); conn.close()
            deck_new_entry.delete(0, tk.END)
            load_decks()

        tk.Button(left_top, text="New Deck", bg=t["BTN"], activebackground=t["BTN_HOVER"], relief="flat", command=add_deck).pack(side="left")

        deck_list_frame = tk.Frame(left_frame, bg=t["CARD"], bd=1, relief="solid")
        deck_list_frame.pack(fill="both", expand=True, padx=6, pady=(4,6))

        deck_listbox = tk.Listbox(deck_list_frame, activestyle="none", bd=0, highlightthickness=0)
        deck_listbox.pack(side="left", fill="both", expand=True)
        deck_scroll = ttk.Scrollbar(deck_list_frame, orient="vertical", command=deck_listbox.yview)
        deck_scroll.pack(side="right", fill="y")
        deck_listbox.configure(yscrollcommand=deck_scroll.set)

        left_bot = tk.Frame(left_frame, bg=t["BG"])
        left_bot.pack(fill="x", padx=6, pady=(4,0))

        def rename_deck():
            sel = deck_listbox.curselection()
            if not sel:
                messagebox.showwarning("Select Deck", "Choose a deck to rename.")
                return
            idx = sel[0]
            deck_id = deck_ids[idx]
            conn, cur = get_flash_conn()
            cur.execute("SELECT deck_name FROM study_flashcard_decks WHERE deck_uid=?", (deck_id,))
            row = cur.fetchone()
            conn.close()
            current = row[0] if row else ""
            new = simpledialog.askstring("Rename Deck", "New name:", initialvalue=current, parent=pg)
            if new:
                conn, cur = get_flash_conn()
                cur.execute("UPDATE study_flashcard_decks SET deck_name=? WHERE deck_uid=?", (new.strip(), deck_id))
                conn.commit(); conn.close()
                load_decks()
                deck_listbox.selection_set(idx)

        def delete_deck():
            sel = deck_listbox.curselection()
            if not sel:
                messagebox.showwarning("Select Deck", "Choose a deck to delete.")
                return
            idx = sel[0]
            deck_id = deck_ids[idx]
            if not messagebox.askyesno("Delete Deck", "Delete deck and all its cards?"):
                return
            conn, cur = get_flash_conn()
            cur.execute("DELETE FROM study_flashcards WHERE deck_uid=?", (deck_id,))
            cur.execute("DELETE FROM study_flashcard_decks WHERE deck_uid=?", (deck_id,))
            conn.commit(); conn.close()
            load_decks()
            clear_cards_view()

        tk.Button(left_bot, text="Rename", bg=t["BTN"], relief="flat", command=rename_deck).pack(side="left", padx=6)
        tk.Button(left_bot, text="Delete", bg="#E57373", fg="white", relief="flat", command=delete_deck).pack(side="left", padx=6)

        # -------------------------
        # Right: Cards view + controls
        # -------------------------
        right_top = tk.Frame(right_frame, bg=t["BG"])
        right_top.pack(fill="x", pady=(0,6))

        deck_title_label = tk.Label(right_top, text="Select a deck →", font=("Segoe UI", 13, "bold"), bg=t["BG"], fg=t["TEXT"])
        deck_title_label.pack(side="left", anchor="w", padx=6)

        right_controls = tk.Frame(right_top, bg=t["BG"])
        right_controls.pack(side="right", anchor="e", padx=6)

        # status filter: All / New / Review / Known
        status_filter_var = tk.StringVar(value="All")
        status_options = ["All", "new", "review", "known"]
        status_menu = ttk.Combobox(right_controls, values=status_options, state="readonly", width=8, textvariable=status_filter_var)
        status_menu.pack(side="right", padx=(6,0))
        status_menu.current(0)

        tk.Label(right_controls, text="Filter:", bg=t["BG"], fg=t["TEXT"]).pack(side="right", padx=(0,4))

        def on_filter_change(e=None):
            sel = deck_listbox.curselection()
            if sel:
                load_cards_for_deck(deck_ids[sel[0]])

        status_menu.bind("<<ComboboxSelected>>", on_filter_change)

        # Add Card & Study buttons
        def add_card():
            sel = deck_listbox.curselection()
            if not sel:
                messagebox.showwarning("Select Deck", "Choose a deck to add a card into.")
                return
            deck_id = deck_ids[sel[0]]
            add_win = tk.Toplevel(pg)
            add_win.title("Add Card")
            add_win.geometry("600x380")
            add_win.transient(pg)

            tk.Label(add_win, text="Front:", bg=t["BG"]).pack(anchor="w", padx=8, pady=(8,0))
            front_txt = scrolledtext.ScrolledText(add_win, height=6, wrap=tk.WORD)
            front_txt.pack(fill="x", padx=8, pady=6)

            tk.Label(add_win, text="Back:", bg=t["BG"]).pack(anchor="w", padx=8, pady=(6,0))
            back_txt = scrolledtext.ScrolledText(add_win, height=8, wrap=tk.WORD)
            back_txt.pack(fill="both", expand=True, padx=8, pady=6)

            def save_card():
                front = front_txt.get("1.0", tk.END).strip()
                back = back_txt.get("1.0", tk.END).strip()
                if not front or not back:
                    messagebox.showwarning("Input Error", "Both front and back are required.", parent=add_win)
                    return
                conn, cur = get_flash_conn()
                cur.execute("INSERT INTO study_flashcards (card_uid, deck_uid, front_text, back_text, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                            (new_uid(), deck_id, front, back, "new", datetime.now().isoformat()))
                conn.commit(); conn.close()
                add_win.destroy()
                load_cards_for_deck(deck_id)

            tk.Button(add_win, text="Save Card", bg=t["BTN"], relief="flat", command=save_card).pack(pady=6)

        def start_study(review_only=False):
            sel = deck_listbox.curselection()
            if not sel:
                messagebox.showwarning("Select Deck", "Choose a deck to study.")
                return
            deck_id = deck_ids[sel[0]]

            conn, cur = get_flash_conn()
            if review_only:
                cur.execute("SELECT card_uid, front_text, back_text, status FROM study_flashcards WHERE deck_uid=? AND status IN ('review','new')", (deck_id,))
            else:
                cur.execute("SELECT card_uid, front_text, back_text, status FROM study_flashcards WHERE deck_uid=?", (deck_id,))
            rows = cur.fetchall()
            conn.close()
            if not rows:
                messagebox.showinfo("No Cards", "This deck has no cards to study.")
                return

            # Prepare cards; we'll weight review cards slightly higher if review_only is False
            cards = [{"id": r[0], "front": r[1], "back": r[2], "status": r[3]} for r in rows]
            # If not review_only, we shuffle but bias review cards by duplicating them once
            pool = []
            for c in cards:
                pool.append(c)
                if c["status"] == "review":
                    pool.append(c)  # review cards appear more often
            random.shuffle(pool)

            # Study popup
            study_win = tk.Toplevel(pg)
            study_win.title(f"Study — {deck_listbox.get(sel[0])}")
            study_win.geometry("720x520")
            study_win.transient(pg)

            study_frame = tk.Frame(study_win, bg=t["BG"])
            study_frame.pack(fill="both", expand=True, padx=12, pady=12)

            idx_var = tk.IntVar(value=0)
            flipped = tk.BooleanVar(value=False)

            card_area = tk.Frame(study_frame, bg=t["CARD"], bd=1, relief="solid")
            card_area.pack(fill="both", expand=True, padx=10, pady=(6,10))

            content_label = tk.Label(card_area, text="", font=("Segoe UI", 14), bg=t["CARD"], fg=t["TEXT"], wraplength=640, justify="left")
            content_label.pack(fill="both", expand=True, padx=12, pady=12)

            def refresh_card():
                i = idx_var.get()
                if i < 0: i = 0
                if i >= len(pool): i = len(pool)-1
                card = pool[i]
                if not flipped.get():
                    content_label.config(text=card["front"])
                else:
                    content_label.config(text=card["back"])
                progress_label.config(text=f"Card {i+1} / {len(pool)}")
                # show status on title
                study_win.title(f"Study — {deck_listbox.get(sel[0])}  ({card.get('status','')})")

            def flip_card(event=None):
                flipped.set(not flipped.get())
                refresh_card()

            def next_card():
                if idx_var.get() < len(pool)-1:
                    idx_var.set(idx_var.get()+1)
                    flipped.set(False)
                    refresh_card()

            def prev_card():
                if idx_var.get() > 0:
                    idx_var.set(idx_var.get()-1)
                    flipped.set(False)
                    refresh_card()

            # Mark functions
            def mark_known():
                i = idx_var.get()
                card = pool[i]
                conn, cur = get_flash_conn()
                cur.execute("UPDATE study_flashcards SET status=? WHERE card_uid=?", ("known", card["id"]))
                conn.commit(); conn.close()
                card["status"] = "known"
                refresh_card()

            def mark_review():
                i = idx_var.get()
                card = pool[i]
                conn, cur = get_flash_conn()
                cur.execute("UPDATE study_flashcards SET status=? WHERE card_uid=?", ("review", card["id"]))
                conn.commit(); conn.close()
                card["status"] = "review"
                refresh_card()

            content_label.bind("<Button-1>", flip_card)

            ctrl_frame = tk.Frame(study_frame, bg=t["BG"])
            ctrl_frame.pack(fill="x", pady=6)
            tk.Button(ctrl_frame, text="Previous", bg=t["BTN"], relief="flat", command=prev_card).pack(side="left", padx=6)
            tk.Button(ctrl_frame, text="Flip", bg=t["BTN"], relief="flat", command=flip_card).pack(side="left", padx=6)
            tk.Button(ctrl_frame, text="Next", bg=t["BTN"], relief="flat", command=next_card).pack(side="left", padx=6)

            tk.Button(ctrl_frame, text="✅ Known", bg=t["BTN"], fg="white", relief="flat", command=mark_known).pack(side="right", padx=6)
            tk.Button(ctrl_frame, text="🔁 Review Later", bg=t["BTN"], relief="flat", command=mark_review).pack(side="right", padx=6)

            progress_label = tk.Label(ctrl_frame, text="", bg=t["BG"], fg=t["TEXT"])
            progress_label.pack(side="right", padx=6)

            refresh_card()
            return

        tk.Button(right_controls, text="Add Card", bg=t["BTN"], relief="flat", command=add_card).pack(side="left", padx=6)
        tk.Button(right_controls, text="Study (All)", bg=t["ACCENT"], fg="white", relief="flat", command=lambda: start_study(review_only=False)).pack(side="left", padx=6)
        tk.Button(right_controls, text="Study (Review)", bg=t["BTN"], relief="flat", command=lambda: start_study(review_only=True)).pack(side="left", padx=6)

        # -------------------------
        # Cards list (Treeview)
        # -------------------------
        cards_frame = tk.Frame(right_frame, bg=t["CARD"], bd=1, relief="solid")
        cards_frame.pack(fill="both", expand=True, padx=6, pady=(4,6))
        cards_tree = ttk.Treeview(cards_frame, columns=("front","status","created"), show="headings", selectmode="browse")
        cards_tree.heading("front", text="Front (preview)")
        cards_tree.heading("status", text="Status")
        cards_tree.heading("created", text="Created")
        cards_tree.column("front", width=380)
        cards_tree.column("status", width=80, anchor="center")
        cards_tree.column("created", width=120, anchor="center")
        cards_tree.pack(side="left", fill="both", expand=True)
        cards_scroll = ttk.Scrollbar(cards_frame, orient="vertical", command=cards_tree.yview)
        cards_scroll.pack(side="right", fill="y")
        cards_tree.configure(yscrollcommand=cards_scroll.set)

        cards_bot = tk.Frame(right_frame, bg=t["BG"])
        cards_bot.pack(fill="x", padx=6, pady=(6,0))

        def get_selected_card_id():
            sel = cards_tree.selection()
            return sel[0] if sel else None

        def edit_card():
            cid = get_selected_card_id()
            if not cid:
                messagebox.showwarning("Select Card", "Select card to edit.")
                return
            conn, cur = get_flash_conn()
            cur.execute("SELECT front_text, back_text, deck_uid FROM study_flashcards WHERE card_uid=?", (cid,))
            row = cur.fetchone()
            conn.close()
            if not row:
                messagebox.showerror("Not found", "Card not found.")
                return
            front_text, back_text, deck_uid = row

            edit_win = tk.Toplevel(pg)
            edit_win.title("Edit Card")
            edit_win.geometry("640x480")
            edit_win.transient(pg)

            tk.Label(edit_win, text="Front:", bg=t["BG"]).pack(anchor="w", padx=8, pady=(8,0))
            front_txt = scrolledtext.ScrolledText(edit_win, height=6, wrap=tk.WORD)
            front_txt.pack(fill="x", padx=8, pady=6)
            front_txt.insert("1.0", front_text)

            tk.Label(edit_win, text="Back:", bg=t["BG"]).pack(anchor="w", padx=8, pady=(6,0))
            back_txt = scrolledtext.ScrolledText(edit_win, height=10, wrap=tk.WORD)
            back_txt.pack(fill="both", expand=True, padx=8, pady=6)
            back_txt.insert("1.0", back_text)

            def save_edit():
                f = front_txt.get("1.0", tk.END).strip()
                b = back_txt.get("1.0", tk.END).strip()
                if not f or not b:
                    messagebox.showwarning("Input Error", "Both front and back required.", parent=edit_win)
                    return
                conn, cur = get_flash_conn()
                cur.execute("UPDATE study_flashcards SET front_text=?, back_text=? WHERE card_uid=?", (f, b, cid))
                conn.commit(); conn.close()
                edit_win.destroy()
                load_cards_for_deck(deck_uid)

            tk.Button(edit_win, text="Save", bg=t["BTN"], relief="flat", command=save_edit).pack(pady=8)

        def delete_card():
            cid = get_selected_card_id()
            if not cid:
                messagebox.showwarning("Select Card", "Select card to delete.")
                return
            if not messagebox.askyesno("Delete Card", "Delete this card?"):
                return
            conn, cur = get_flash_conn()
            cur.execute("SELECT deck_uid FROM study_flashcards WHERE card_uid=?", (cid,))
            row = cur.fetchone()
            deck_uid = row[0] if row else None
            cur.execute("DELETE FROM study_flashcards WHERE card_uid=?", (cid,))
            conn.commit(); conn.close()
            if deck_uid:
                load_cards_for_deck(deck_uid)

        tk.Button(cards_bot, text="Edit Card", bg=t["BTN"], relief="flat", command=edit_card).pack(side="left", padx=6)
        tk.Button(cards_bot, text="Delete Card", bg="#E57373", fg="white", relief="flat", command=delete_card).pack(side="left", padx=6)

        # -------------------------
        # Data loading helpers
        # -------------------------
        deck_ids = []

        def load_decks():
            deck_listbox.delete(0, tk.END)
            conn, cur = get_flash_conn()
            cur.execute("SELECT deck_uid, deck_name FROM study_flashcard_decks ORDER BY created_at DESC")
            rows = cur.fetchall()
            conn.close()
            deck_ids.clear()
            for d in rows:
                deck_listbox.insert(tk.END, d[1])
                deck_ids.append(d[0])
            clear_cards_view()

        def clear_cards_view():
            deck_title_label.config(text="Select a deck →")
            for i in cards_tree.get_children():
                cards_tree.delete(i)

        def load_cards_for_deck(deck_uid):
            conn, cur = get_flash_conn()
            cur.execute("SELECT deck_name FROM study_flashcard_decks WHERE deck_uid=?", (deck_uid,))
            row = cur.fetchone()
            deck_name = row[0] if row else "Deck"
            deck_title_label.config(text=f"{deck_name}")
            for i in cards_tree.get_children():
                cards_tree.delete(i)

            # filter by status if needed
            status_filter = status_filter_var.get()
            if status_filter == "All":
                cur.execute("SELECT card_uid, front_text, status, created_at FROM study_flashcards WHERE deck_uid=? ORDER BY created_at DESC", (deck_uid,))
            else:
                cur.execute("SELECT card_uid, front_text, status, created_at FROM study_flashcards WHERE deck_uid=? AND status=?", (deck_uid, status_filter))
            rows = cur.fetchall()
            conn.close()
            for r in rows:
                preview = (r[1].strip().replace("\n", " "))[:120]
                created = r[3].split("T")[0] if r[3] else ""
                cards_tree.insert("", "end", iid=r[0], values=(preview, r[2], created))

        # Bind deck selection
        def on_deck_select(evt):
            sel = deck_listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            load_cards_for_deck(deck_ids[idx])

        deck_listbox.bind("<<ListboxSelect>>", on_deck_select)

        # Initial load
        load_decks()

    # --- WORKOUT PAGE ---
    if pn == "Workout":

        # --- Global Variables ---
        global workout_date_entry, workout_notebook, workout_listbox
        global lift_exercise_var, lift_weight_var, lift_reps_var
        global cardio_duration_var, cardio_distance_var, cardio_notes_var
        global sets_display_frame, current_workout_id, workout_detail_frame

        # --- Tkinter Variables ---
        lift_exercise_var = tk.StringVar()
        lift_weight_var = tk.StringVar()
        lift_reps_var = tk.StringVar()
        cardio_duration_var = tk.StringVar()
        cardio_distance_var = tk.StringVar()
        cardio_notes_var = tk.StringVar()

        # --- Helper Functions ---
        def db_connect():
            """Return a sqlite3 connection."""
            return sqlite3.connect("mochi.db")

        # --- Lifting Logging ---
        def log_lifting_set():
            date_str = workout_date_entry.get_date().strftime("%Y-%m-%d")
            exercise = lift_exercise_var.get().strip()

            try:
                weight = float(lift_weight_var.get())
                reps = int(lift_reps_var.get())
            except ValueError:
                messagebox.showerror("Input Error", "Weight must be a number and Reps must be an integer.")
                return

            if not exercise or weight <= 0 or reps <= 0:
                messagebox.showwarning("Invalid Input", "Please enter a valid exercise, weight, and reps.")
                return

            conn = db_connect()
            c = conn.cursor()

            try:
                # Check for existing lifting session
                c.execute("SELECT id FROM workouts WHERE date=? AND type='Lifting'", (date_str,))
                row = c.fetchone()
                if row:
                    workout_id = row[0]
                else:
                    c.execute("INSERT INTO workouts (date, type) VALUES (?, 'Lifting')", (date_str,))
                    workout_id = c.lastrowid

                # Determine next set number
                c.execute("SELECT MAX(set_number) FROM sets_reps WHERE workout_id=?", (workout_id,))
                max_set = c.fetchone()[0] or 0
                set_number = max_set + 1

                c.execute(
                    "INSERT INTO sets_reps (workout_id, exercise_name, set_number, weight, reps) VALUES (?, ?, ?, ?, ?)",
                    (workout_id, exercise, set_number, weight, reps)
                )
                conn.commit()
                messagebox.showinfo("Success", f"Logged set: {weight}kg x {reps} reps for {exercise}.")
                lift_weight_var.set("")
                lift_reps_var.set("")
                load_workout_data_and_update_ui()
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to log set: {e}")
            finally:
                conn.close()

        # --- Cardio Logging ---
        def log_cardio_session():
            date_str = workout_date_entry.get_date().strftime("%Y-%m-%d")
            try:
                duration = float(cardio_duration_var.get()) if cardio_duration_var.get().strip() else None
                distance_km = float(cardio_distance_var.get()) if cardio_distance_var.get().strip() else None
                distance_m = distance_km * 1000 if distance_km is not None else None
            except ValueError:
                messagebox.showerror("Input Error", "Duration and Distance must be numbers.")
                return

            notes = cardio_notes_var.get().strip()
            if duration is None and distance_m is None:
                messagebox.showwarning("Invalid Input", "Please enter Duration or Distance.")
                return

            conn = db_connect()
            c = conn.cursor()
            try:
                c.execute(
                    "INSERT INTO workouts (date, type, duration, distance, notes) VALUES (?, 'Cardio', ?, ?, ?)",
                    (date_str, duration, distance_m, notes)
                )
                conn.commit()
                messagebox.showinfo("Success", f"Cardio session logged for {date_str}.")
                cardio_duration_var.set("")
                cardio_distance_var.set("")
                cardio_notes_var.set("")
                load_workout_data_and_update_ui()
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to log cardio: {e}")
            finally:
                conn.close()

        # --- Delete Workout ---
        def delete_workout_log(w_id):
            if w_id is None:
                messagebox.showerror("Error", "No workout selected.")
                return
            confirm = messagebox.askyesno("Confirm Deletion", f"Delete Workout ID {w_id}?")
            if not confirm:
                return

            conn = db_connect()
            c = conn.cursor()
            try:
                c.execute("DELETE FROM workouts WHERE id=?", (w_id,))
                conn.commit()
                messagebox.showinfo("Success", "Workout deleted.")
                load_workout_data_and_update_ui()
                view_workout_details(None)
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to delete workout: {e}")
            finally:
                conn.close()

        # --- Delete Individual Set ---
        def delete_individual_set(s_id):
            confirm = messagebox.askyesno("Confirm Delete", f"Delete this set (ID: {s_id})?")
            if not confirm:
                return
            conn = db_connect()
            c = conn.cursor()
            try:
                c.execute("DELETE FROM sets_reps WHERE id=?", (s_id,))
                conn.commit()
                messagebox.showinfo("Deleted", "Set deleted successfully.")
                load_workout_data_and_update_ui()
                view_workout_details(None)
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to delete set: {e}")
            finally:
                conn.close()

        # --- Update Workout Log ---
        def update_workout_log(w_id, duration_var, distance_var, notes_widget):
            try:
                duration = float(duration_var.get()) if duration_var.get() else None
                distance_m = float(distance_var.get()) if distance_var.get() else None
                notes = notes_widget.get("1.0", tk.END).strip()
            except ValueError:
                messagebox.showerror("Input Error", "Duration and Distance must be numbers.")
                return

            conn = db_connect()
            c = conn.cursor()
            try:
                c.execute("UPDATE workouts SET duration=?, distance=?, notes=? WHERE id=?",
                        (duration, distance_m, notes, w_id))
                conn.commit()
                messagebox.showinfo("Success", "Workout updated.")
                load_workout_data_and_update_ui()
                view_workout_details(None)
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to update workout: {e}")
            finally:
                conn.close()

        # --- Update All Lifting Sets ---
        def update_all_lifting_sets(sets_data, w_id):
            conn = db_connect()
            c = conn.cursor()
            errors = 0
            for s in sets_data:
                try:
                    set_id = s['id']
                    weight = float(s['weight'].get())
                    reps = int(s['reps'].get())
                    if weight > 0 and reps > 0:
                        c.execute("UPDATE sets_reps SET weight=?, reps=? WHERE id=?", (weight, reps, set_id))
                    else:
                        errors += 1
                except:
                    errors += 1
            conn.commit()
            conn.close()
            if errors:
                messagebox.showwarning("Partial Success", f"{errors} sets failed.")
            else:
                messagebox.showinfo("Success", "All sets updated.")
            load_workout_data_and_update_ui()
            view_workout_details(None)

        # --- Load Data & Update UI ---
        def load_workout_data_and_update_ui():
            conn = db_connect()
            c = conn.cursor()
            try:
                # Load history
                rows = c.execute("SELECT id, date, type, duration, distance FROM workouts ORDER BY date DESC").fetchall()
                workout_listbox.delete(0, tk.END)
                for wid, w_date, w_type, dur, dist in rows:
                    text = f"{wid}|{w_date} - {w_type}"
                    if w_type == 'Cardio':
                        if dur: text += f" ({dur:.1f} min)"
                        if dist: text += f" ({dist:.0f} m)"
                    workout_listbox.insert(tk.END, text)

                # Load today's lifting sets
                today = workout_date_entry.get_date().strftime("%Y-%m-%d")
                c.execute("SELECT id FROM workouts WHERE date=? AND type='Lifting'", (today,))
                row = c.fetchone()
                for w in sets_display_frame.winfo_children():
                    w.destroy()
                tk.Label(sets_display_frame, text="Sets Logged Today:", bg=theme()["CARD"], fg=theme()["TEXT"],
                        font=("Segoe UI", 10, "bold")).pack(pady=5, anchor="nw")

                if row:
                    workout_id = row[0]
                    sets = c.execute("SELECT exercise_name, weight, reps FROM sets_reps WHERE workout_id=? ORDER BY exercise_name, set_number",
                                    (workout_id,)).fetchall()
                    if sets:
                        text_widget = tk.Text(sets_display_frame, height=15, width=40, bg=theme()["BG"], fg=theme()["TEXT"], state="normal")
                        text_widget.pack(fill="both", expand=True, padx=5, pady=5)
                        current_ex = ""
                        set_count = 1
                        for ex, wgt, reps in sets:
                            if ex != current_ex:
                                text_widget.insert(tk.END, f"\n**{ex.upper()}**\n")
                                current_ex = ex
                                set_count = 1
                            text_widget.insert(tk.END, f"  Set {set_count}: {wgt:.1f} kg x {reps} reps\n")
                            set_count += 1
                        text_widget.config(state="disabled")
                    else:
                        tk.Label(sets_display_frame, text="No lifting sets logged today.", bg=theme()["CARD"], fg=theme()["TEXT"]).pack(pady=10)
                else:
                    tk.Label(sets_display_frame, text="No lifting session logged today.", bg=theme()["CARD"], fg=theme()["TEXT"]).pack(pady=10)

            finally:
                conn.close()

        # --- View Workout Details ---
        def view_workout_details(event):
            global current_workout_id
            sel = workout_listbox.curselection()
            for w in workout_detail_frame.winfo_children():
                w.destroy()
            if not sel:
                current_workout_id = None
                tk.Label(workout_detail_frame, text="Select an entry for details.", bg=theme()["BG"], fg=theme()["TEXT"]).pack(pady=20)
                return
            index = sel[0]
            w_id = int(workout_listbox.get(index).split("|")[0])
            current_workout_id = w_id

            conn = db_connect()
            c = conn.cursor()
            try:
                row = c.execute("SELECT date, type, duration, distance, notes FROM workouts WHERE id=?", (w_id,)).fetchone()
                if not row:
                    tk.Label(workout_detail_frame, text="Workout not found.", bg=theme()["BG"], fg=theme()["ACCENT"]).pack(pady=20)
                    return
                w_date, w_type, dur, dist, notes = row

                tk.Label(workout_detail_frame, text=f"Details for {w_date} ({w_type})", bg=theme()["BG"], fg=theme()["TEXT"], font=("Segoe UI", 11, "bold")).pack(pady=(0, 10), anchor="nw")

                # Edit Frame
                edit_frame = tk.Frame(workout_detail_frame, bg=theme()["BG"])
                edit_frame.pack(fill="x", pady=5)
                dur_var = tk.StringVar(value=f"{dur:.1f}" if dur else "")
                dist_var = tk.StringVar(value=f"{dist:.0f}" if dist else "")
                tk.Label(edit_frame, text="Duration (min):", bg=theme()["BG"], fg=theme()["TEXT"]).grid(row=0, column=0, sticky="w")
                tk.Entry(edit_frame, textvariable=dur_var, width=10, bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=0, column=1)
                tk.Label(edit_frame, text="Distance (m):", bg=theme()["BG"], fg=theme()["TEXT"]).grid(row=1, column=0, sticky="w")
                tk.Entry(edit_frame, textvariable=dist_var, width=10, bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=1, column=1)
                tk.Label(edit_frame, text="Notes:", bg=theme()["BG"], fg=theme()["TEXT"]).grid(row=2, column=0, sticky="nw")
                notes_txt = tk.Text(edit_frame, height=3, width=30, bg=theme()["CARD"], fg=theme()["TEXT"])
                notes_txt.grid(row=2, column=1, padx=5, pady=5)
                notes_txt.insert("1.0", notes if notes else "")

                tk.Button(workout_detail_frame, text="Update Log", bg=theme()["ACCENT"], fg="white",
                        command=lambda: update_workout_log(w_id, dur_var, dist_var, notes_txt)).pack(pady=5)
                tk.Button(workout_detail_frame, text="Delete Log", bg="#ECB6B5", fg="white",
                        command=lambda: delete_workout_log(w_id)).pack(pady=5)

                if w_type == 'Lifting':
                    # Editable Sets
                    tk.Label(workout_detail_frame, text="Lifting Sets (Edit/Delete):", bg=theme()["BG"], fg=theme()["TEXT"], font=("Segoe UI", 10, "bold")).pack(pady=(10, 5), anchor="nw")
                    scroll_frame = tk.Frame(workout_detail_frame, bg=theme()["BG"])
                    scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
                    canvas = tk.Canvas(scroll_frame, bg=theme()["BG"], highlightthickness=0)
                    canvas.pack(side="left", fill="both", expand=True)
                    scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
                    scrollbar.pack(side="right", fill="y")
                    canvas.configure(yscrollcommand=scrollbar.set)
                    inner = tk.Frame(canvas, bg=theme()["BG"])
                    canvas.create_window((0, 0), window=inner, anchor="nw")
                    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
                    canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas.find_all()[0], width=e.width))

                    # Fetch sets
                    sets_rows = c.execute("SELECT id, exercise_name, weight, reps FROM sets_reps WHERE workout_id=? ORDER BY exercise_name, set_number", (w_id,)).fetchall()
                    editable_sets = []
                    current_ex = ""
                    for sid, ex, wgt, reps in sets_rows:
                        if ex != current_ex:
                            tk.Label(inner, text=ex.upper(), bg=theme()["BG"], fg="black", font=("Segoe UI", 9, "bold")).pack(fill="x", pady=(5, 0))
                            current_ex = ex
                        row_frame = tk.Frame(inner, bg=theme()["BG"])
                        row_frame.pack(fill="x")
                        tk.Label(row_frame, text=f"Set", width=15, anchor="w", bg=theme()["BG"], fg=theme()["TEXT"]).pack(side="left")
                        w_var = tk.StringVar(value=f"{wgt:.1f}")
                        r_var = tk.StringVar(value=str(reps))
                        tk.Entry(row_frame, textvariable=w_var, width=8, bg=theme()["CARD"], fg=theme()["TEXT"]).pack(side="left", padx=5)
                        tk.Entry(row_frame, textvariable=r_var, width=5, bg=theme()["CARD"], fg=theme()["TEXT"]).pack(side="left", padx=5)
                        tk.Button(row_frame, text="Delete", bg="#ECB6B5", fg="white", font=("Segoe UI", 8),
                                command=lambda s=sid: delete_individual_set(s)).pack(side="right", padx=5)
                        editable_sets.append({'id': sid, 'weight': w_var, 'reps': r_var})
                    tk.Button(workout_detail_frame, text="Save All Set Changes", bg=theme()["BG"], fg="white",
                            command=lambda: update_all_lifting_sets(editable_sets, w_id), padx=10, pady=5).pack(pady=10)
            finally:
                conn.close()

        # --- UI Construction ---
        tk.Label(content, text="💪 Workout Tracker", font=("Segoe UI", 16, "bold"), bg=theme()["CARD"], fg=theme()["TEXT"], pady=10).pack(fill="x", padx=10)
        date_frame = tk.Frame(content, bg=theme()["BG"])
        date_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(date_frame, text="Workout Date:", bg=theme()["BG"], fg=theme()["TEXT"]).pack(side="left", padx=5)
        workout_date_entry = DateEntry(date_frame, width=12, date_pattern='yyyy-mm-dd', selectmode='day', background=theme()["ACCENT"], foreground='white')
        workout_date_entry.set_date(date.today())
        workout_date_entry.pack(side="left", padx=5)

        workout_notebook = ttk.Notebook(content)
        workout_notebook.pack(fill="both", expand=True, padx=10, pady=10)
        lifting_tab = tk.Frame(workout_notebook, bg=theme()["CARD"])
        cardio_tab = tk.Frame(workout_notebook, bg=theme()["CARD"])
        history_tab = tk.Frame(workout_notebook, bg=theme()["CARD"])
        workout_notebook.add(lifting_tab, text="🏋️ Lifting Log")
        workout_notebook.add(cardio_tab, text="🏃 Cardio Log")
        workout_notebook.add(history_tab, text="📚 History")

        # --- Lifting Tab ---
        log_frame = tk.Frame(lifting_tab, bg=theme()["CARD"], padx=10, pady=10)
        log_frame.pack(side="left", fill="y")
        tk.Label(log_frame, text="Log New Set:", bg=theme()["CARD"], fg=theme()["TEXT"], font=("Segoe UI", 10, "bold")).grid(row=0, column=0, columnspan=2, pady=5)
        tk.Label(log_frame, text="Exercise:", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=1, column=0, sticky="w")
        tk.Entry(log_frame, textvariable=lift_exercise_var, width=20, bg=theme()["BG"], fg=theme()["TEXT"]).grid(row=1, column=1)
        tk.Label(log_frame, text="Weight (kg):", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=2, column=0, sticky="w")
        tk.Entry(log_frame, textvariable=lift_weight_var, width=20, bg=theme()["BG"], fg=theme()["TEXT"]).grid(row=2, column=1)
        tk.Label(log_frame, text="Reps:", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=3, column=0, sticky="w")
        tk.Entry(log_frame, textvariable=lift_reps_var, width=20, bg=theme()["BG"], fg=theme()["TEXT"]).grid(row=3, column=1)
        tk.Button(log_frame, text="Add Set", bg=theme()["BG"], fg="white", command=log_lifting_set).grid(row=4, column=0, columnspan=2, pady=10)

        sets_display_frame = tk.Frame(lifting_tab, bg=theme()["CARD"])
        sets_display_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # --- Cardio Tab ---
        cardio_frame = tk.Frame(cardio_tab, bg=theme()["CARD"], padx=10, pady=10)
        cardio_frame.pack(fill="x")
        tk.Label(cardio_frame, text="Log Cardio Session:", bg=theme()["CARD"], fg=theme()["TEXT"], font=("Segoe UI", 10, "bold")).grid(row=0, column=0, columnspan=2, pady=5)
        tk.Label(cardio_frame, text="Duration (min):", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=1, column=0, sticky="w")
        tk.Entry(cardio_frame, textvariable=cardio_duration_var, width=20, bg=theme()["BG"], fg=theme()["TEXT"]).grid(row=1, column=1)
        tk.Label(cardio_frame, text="Distance (m):", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=2, column=0, sticky="w")
        tk.Entry(cardio_frame, textvariable=cardio_distance_var, width=20, bg=theme()["BG"], fg=theme()["TEXT"]).grid(row=2, column=1)
        tk.Label(cardio_frame, text="Notes:", bg=theme()["CARD"], fg=theme()["TEXT"]).grid(row=3, column=0, sticky="nw")
        tk.Entry(cardio_frame, textvariable=cardio_notes_var, width=30, bg=theme()["BG"], fg=theme()["TEXT"]).grid(row=3, column=1)
        tk.Button(cardio_frame, text="Add Cardio Session", bg=theme()["BG"], fg="white", command=log_cardio_session).grid(row=4, column=0, columnspan=2, pady=10)

        # --- History Tab ---
        workout_listbox = tk.Listbox(history_tab, bg=theme()["CARD"], fg=theme()["TEXT"], selectbackground=theme()["ACCENT"], font=("Segoe UI", 10))
        workout_listbox.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        workout_listbox.bind("<<ListboxSelect>>", view_workout_details)
        workout_detail_frame = tk.Frame(history_tab, bg=theme()["BG"])
        workout_detail_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # --- Initial Load ---
        load_workout_data_and_update_ui()
        
# --------------------- Final setup and run ---------------------

# Initial page and highlight
show_page("HomeHub")

# Apply initial theme
apply_theme()

# keep canvas width static so it looks compact
canvas.config(width=sidebar_width)

root.mainloop()

