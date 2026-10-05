import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import sqlite3
import datetime
import pandas as pd
from college_course_content import COLLEGE_COURSE_TOPICS

DB_NAME = "nexus_app.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Subjects & Notes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            level TEXT DEFAULT 'College'
        )
    """)

    # Backwards-compatibility: if an older DB exists without the `level` column,
    # add it so SELECTs that reference `level` do not fail.
    cursor.execute("PRAGMA table_info(subjects)")
    existing_cols = [r[1] for r in cursor.fetchall()]
    if 'level' not in existing_cols:
        cursor.execute("ALTER TABLE subjects ADD COLUMN level TEXT DEFAULT 'College'")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subject_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            front TEXT NOT NULL,
            back TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'Manual',
            due_at TEXT NOT NULL,
            interval_days REAL NOT NULL DEFAULT 0,
            review_count INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE
        )
    """)

    # 2. Tasks
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            priority TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0,
            due_date DATE
        )
    """)
    cursor.execute("PRAGMA table_info(tasks)")
    task_columns = [row[1] for row in cursor.fetchall()]
    if "due_date" not in task_columns:
        cursor.execute("ALTER TABLE tasks ADD COLUMN due_date DATE")

    # 3. Quizzes & Questions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            title TEXT NOT NULL,
            questions_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 4. Study Sessions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS study_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            hours REAL NOT NULL,
            session_date DATE DEFAULT (DATE('now'))
        )
    """)

    # 5. Chat History (required by Streamlit sidebar)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 6. Starter Courses
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS starter_courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            level TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 7. Reference Wiki Topics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reference_wiki_topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            title TEXT NOT NULL,
            summary TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reading_reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            scheduled_at TEXT NOT NULL,
            notified INTEGER NOT NULL DEFAULT 0,
            completed INTEGER NOT NULL DEFAULT 0
        )
    """)

    # Seed Default Starter Courses across Grade Levels
    cursor.execute("SELECT COUNT(*) FROM subjects")
    if cursor.fetchone()[0] == 0:
        default_courses = [
            ("Intro to Computer Science (CS101)", "College"),
            ("Calculus I: Limits & Derivatives", "College"),
            ("General Chemistry & Lab", "College"),
            ("Academic Writing & Research Methods", "College"),
            ("Algebra II & Trigonometry", "High School"),
            ("AP Biology Foundations", "High School"),
            ("World History & Civilization", "High School"),
            ("Pre-Algebra & Geometry Basics", "Middle School"),
            ("Physical Science & Earth Systems", "Middle School"),
            ("Language Arts & Reading Comprehension", "Middle School"),
        ]
        cursor.executemany("INSERT INTO subjects (name, level) VALUES (?, ?)", default_courses)

    cursor.execute("SELECT COUNT(*) FROM starter_courses")
    if cursor.fetchone()[0] == 0:
        default_starter_courses = [
            ("Intro to Computer Science (CS101)", "College", "Foundational overview of algorithms, logic, and programming basics."),
            ("Calculus I: Limits & Derivatives", "College", "Differentiation, rates of change, and motion applications."),
            ("General Chemistry & Lab", "College", "Essential atomic structure, bonding, and lab-based measurements."),
            ("Academic Writing & Research Methods", "College", "How to build arguments, cite sources, and structure research papers."),
            ("Algebra II & Trigonometry", "High School", "Equations, functions, radians, sine/cosine relationships, and graphing."),
            ("AP Biology Foundations", "High School", "Core cell biology, genetics, ecosystems, and scientific reasoning."),
            ("World History & Civilization", "High School", "Major civilizations, political change, and historical analysis."),
            ("Pre-Algebra & Geometry Basics", "Middle School", "Foundational geometry, variables, and numerical reasoning."),
            ("Physical Science & Earth Systems", "Middle School", "Earth science, forces, matter, and scientific observation."),
            ("Language Arts & Reading Comprehension", "Middle School", "Reading strategies, vocabulary, and informational text analysis."),
        ]
        cursor.executemany(
            "INSERT INTO starter_courses (title, level, description) VALUES (?, ?, ?)",
            default_starter_courses
        )

    cursor.execute("SELECT value FROM app_settings WHERE key = 'college_catalog_seeded'")
    if cursor.fetchone() is None:
        college_courses = [
            (
                "English",
                "College-level study of writing, literature, rhetoric, and critical interpretation.",
                "Core areas: close reading and literary analysis; rhetoric and argument; academic research and citation; writing workshops and revision; language, genre, and cultural context. Suggested work: analyze primary texts, build evidence-based arguments, and complete a researched essay.",
            ),
            (
                "Chemistry",
                "A college chemistry foundation connecting molecular theory, quantitative problem-solving, and laboratory practice.",
                "Core areas: atomic structure and periodicity; chemical bonding and molecular geometry; stoichiometry and reactions; thermodynamics and kinetics; equilibrium, acids, and bases; introductory organic chemistry; laboratory measurement, safety, and data analysis. Suggested work: solve quantitative problem sets and write lab reports from experimental evidence.",
            ),
            (
                "Social Studies",
                "Interdisciplinary college study of societies, institutions, historical change, and human geography.",
                "Core areas: historical methods and primary sources; social structure and institutions; political systems and public policy; economic reasoning; human geography and migration; research methods and evaluating evidence. Suggested work: compare perspectives across sources and develop a documented case study.",
            ),
            (
                "Arts",
                "College-level exploration of artistic practice, visual culture, design, and critical interpretation.",
                "Core areas: studio practice and material techniques; elements and principles of design; art history and cultural context; visual analysis and critique; ethics and representation; portfolio development. Suggested work: create a series of studies, document revisions, and present a critical reflection.",
            ),
            (
                "Mathematics",
                "A college mathematics pathway emphasizing proof, modeling, and quantitative reasoning.",
                "Core areas: calculus and multivariable analysis; linear algebra; differential equations; probability and statistics; discrete mathematics; mathematical proof and modeling. Suggested work: explain solution methods, verify assumptions, and apply models to real data or scientific questions.",
            ),
            (
                "Physics",
                "College-level study of physical systems through mathematical models, experiments, and evidence.",
                "Core areas: classical mechanics; oscillations and waves; electricity and magnetism; thermodynamics; optics; introductory quantum and modern physics; experimental design and uncertainty. Suggested work: derive models, solve quantitative problems, and interpret laboratory measurements.",
            ),
        ]
        for name, summary, content in college_courses:
            cursor.execute("SELECT id FROM subjects WHERE name = ?", (name,))
            subject_row = cursor.fetchone()
            if subject_row is None:
                cursor.execute(
                    "INSERT INTO subjects (name, level) VALUES (?, 'College')",
                    (name,),
                )
                subject_id = cursor.lastrowid
            else:
                subject_id = subject_row[0]
                cursor.execute(
                    "UPDATE subjects SET level = 'College' WHERE id = ?",
                    (subject_id,),
                )

            cursor.execute(
                "SELECT id FROM reference_wiki_topics WHERE subject_id = ? AND title = ?",
                (subject_id, "College course guide"),
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    "INSERT INTO reference_wiki_topics (subject_id, title, summary, content) VALUES (?, ?, ?, ?)",
                    (subject_id, "College course guide", summary, content),
                )

        cursor.execute(
            "INSERT INTO app_settings (key, value) VALUES ('college_catalog_seeded', '1')"
        )

    for subject_name, topics in COLLEGE_COURSE_TOPICS.items():
        cursor.execute("SELECT id FROM subjects WHERE name = ?", (subject_name,))
        subject_row = cursor.fetchone()
        if subject_row is None:
            continue
        subject_id = subject_row[0]
        for title, summary, content in topics:
            cursor.execute(
                "SELECT id FROM reference_wiki_topics WHERE subject_id = ? AND title = ?",
                (subject_id, title),
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    "INSERT INTO reference_wiki_topics (subject_id, title, summary, content) VALUES (?, ?, ?, ?)",
                    (subject_id, title, summary, content),
                )

    # Seed Sample Study Log Data
    cursor.execute("SELECT COUNT(*) FROM study_sessions")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO study_sessions (subject_id, hours, session_date) VALUES (?, ?, ?)",
            [
                (1, 2.5, "2026-09-25"), (1, 4.0, "2026-09-26"),
                (1, 1.5, "2026-09-27"), (1, 3.5, "2026-09-28"),
                (1, 5.0, "2026-09-29"), (1, 2.0, "2026-09-30"),
                (1, 4.5, "2026-10-01")
            ]
        )

    conn.commit()
    conn.close()


# --- HELPER FUNCTIONS ---

def get_subjects(level_filter=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if level_filter:
        cursor.execute("SELECT id, name, level FROM subjects WHERE level = ? ORDER BY name ASC", (level_filter,))
    else:
        cursor.execute("SELECT id, name, level FROM subjects ORDER BY name ASC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "level": r[2]} for r in rows]


def add_subject(name, level="College"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO subjects (name, level) VALUES (?, ?)", (name, level))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success


def delete_subject(subject_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("BEGIN")
    for table in ("subject_notes", "quizzes", "study_sessions", "reference_wiki_topics", "reading_reminders", "flashcards"):
        cursor.execute(f"DELETE FROM {table} WHERE subject_id = ?", (subject_id,))
    cursor.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def add_reading_reminder(subject_id, title, scheduled_at):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reading_reminders (subject_id, title, scheduled_at) VALUES (?, ?, ?)",
        (subject_id, title, scheduled_at),
    )
    conn.commit()
    conn.close()


def get_reading_reminders():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT reminders.id, reminders.subject_id, subjects.name, reminders.title,
               reminders.scheduled_at, reminders.notified
        FROM reading_reminders AS reminders
        JOIN subjects ON subjects.id = reminders.subject_id
        WHERE reminders.completed = 0
        ORDER BY reminders.scheduled_at ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "subject_id": row[1],
            "subject_name": row[2],
            "title": row[3],
            "scheduled_at": row[4],
            "notified": bool(row[5]),
        }
        for row in rows
    ]


def mark_reading_reminder_notified(reminder_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE reading_reminders SET notified = 1 WHERE id = ?",
        (reminder_id,),
    )
    conn.commit()
    conn.close()


def complete_reading_reminder(reminder_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE reading_reminders SET completed = 1 WHERE id = ?",
        (reminder_id,),
    )
    conn.commit()
    conn.close()


def delete_reading_reminder(reminder_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reading_reminders WHERE id = ?", (reminder_id,))
    conn.commit()
    conn.close()


def save_subject_note(subject_id, title, content):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO subject_notes (subject_id, title, content) VALUES (?, ?, ?)",
        (subject_id, title, content),
    )
    conn.commit()
    conn.close()


def get_notes_for_subject(subject_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content FROM subject_notes WHERE subject_id = ?", (subject_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "content": r[2]} for r in rows]


def save_flashcards(subject_id, source, cards):
    due_at = datetime.datetime.now().isoformat(timespec="seconds")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO flashcards (subject_id, front, back, source, due_at) VALUES (?, ?, ?, ?, ?)",
        [
            (subject_id, card["front"], card["back"], source, due_at)
            for card in cards
        ],
    )
    conn.commit()
    conn.close()
    return len(cards)


def get_flashcards_for_subject(subject_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, front, back, source, due_at, interval_days, review_count
        FROM flashcards
        WHERE subject_id = ?
        ORDER BY due_at ASC, id ASC
        """,
        (subject_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "front": row[1],
            "back": row[2],
            "source": row[3],
            "due_at": row[4],
            "interval_days": row[5],
            "review_count": row[6],
        }
        for row in rows
    ]


def review_flashcard(flashcard_id, rating):
    intervals = {"Again": 10 / (24 * 60), "Hard": 1, "Good": 3, "Easy": 7}
    if rating not in intervals:
        raise ValueError(f"Unsupported flashcard rating: {rating}")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT interval_days FROM flashcards WHERE id = ?",
        (flashcard_id,),
    )
    row = cursor.fetchone()
    if row is None:
        conn.close()
        raise ValueError(f"Flashcard {flashcard_id} does not exist.")

    previous_interval = row[0]
    if previous_interval:
        multipliers = {"Again": 0, "Hard": 1.2, "Good": 2, "Easy": 2.5}
        interval_days = max(
            intervals[rating],
            previous_interval * multipliers[rating],
        )
    else:
        interval_days = intervals[rating]

    due_at = (
        datetime.datetime.now()
        + datetime.timedelta(days=interval_days)
    ).isoformat(timespec="seconds")
    cursor.execute(
        """
        UPDATE flashcards
        SET due_at = ?, interval_days = ?, review_count = review_count + 1
        WHERE id = ?
        """,
        (due_at, interval_days, flashcard_id),
    )
    conn.commit()
    conn.close()


def delete_flashcard(flashcard_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM flashcards WHERE id = ?", (flashcard_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def get_tasks():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, priority, done, due_date FROM tasks ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": r[0], "title": r[1], "priority": r[2], "done": bool(r[3]), "due_date": r[4]}
        for r in rows
    ]


def add_task(title, priority, due_date=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, priority, done, due_date) VALUES (?, ?, 0, ?)",
        (title, priority, due_date),
    )
    conn.commit()
    conn.close()


def update_task_status(task_id, done):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET done = ? WHERE id = ?", (1 if done else 0, task_id))
    conn.commit()
    conn.close()


def save_quiz(subject_id, title, questions_json):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO quizzes (subject_id, title, questions_json) VALUES (?, ?, ?)",
        (subject_id, title, questions_json),
    )
    conn.commit()
    conn.close()


def get_quizzes_for_subject(subject_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, questions_json, created_at FROM quizzes WHERE subject_id = ?", (subject_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "questions_json": r[2], "created_at": r[3]} for r in rows]


def log_study_session(subject_id, hours, session_date=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if session_date is None:
        cursor.execute(
            "INSERT INTO study_sessions (subject_id, hours, session_date) VALUES (?, ?, DATE('now'))",
            (subject_id, float(hours)),
        )
    else:
        cursor.execute(
            "INSERT INTO study_sessions (subject_id, hours, session_date) VALUES (?, ?, ?)",
            (subject_id, float(hours), session_date),
        )
    conn.commit()
    conn.close()


def get_chat_history():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM chat_history ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in rows]


def save_chat_message(role, content):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_history (role, content) VALUES (?, ?)", (role, content))
    conn.commit()
    conn.close()


def clear_chat_history():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history")
    conn.commit()
    conn.close()


def get_starter_courses(level_filter=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if level_filter:
        cursor.execute(
            "SELECT id, title, level, description FROM starter_courses WHERE level = ? ORDER BY title ASC",
            (level_filter,),
        )
    else:
        cursor.execute("SELECT id, title, level, description FROM starter_courses ORDER BY title ASC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "level": r[2], "description": r[3]} for r in rows]


def get_reference_wiki_topics(subject_id=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if subject_id is not None:
        cursor.execute(
            "SELECT id, subject_id, title, summary, content FROM reference_wiki_topics WHERE subject_id = ? ORDER BY title ASC",
            (subject_id,),
        )
    else:
        cursor.execute("SELECT id, subject_id, title, summary, content FROM reference_wiki_topics ORDER BY title ASC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "subject_id": r[1], "title": r[2], "summary": r[3], "content": r[4]} for r in rows]


def add_reference_wiki_topic(subject_id, title, summary, content):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reference_wiki_topics (subject_id, title, summary, content) VALUES (?, ?, ?, ?)",
        (subject_id, title, summary, content),
    )
    conn.commit()
    conn.close()


def get_study_hours_data():
    conn = sqlite3.connect(DB_NAME)
    query = """
        SELECT strftime('%Y-%m-%d', session_date) as date, STRFTIME('%a', session_date) as Day, SUM(hours) as Hours
        FROM study_sessions WHERE session_date >= DATE('now', '-6 days')
        GROUP BY session_date ORDER BY session_date ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_task_status_data():
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT CASE WHEN done = 1 THEN 'Completed' ELSE 'Pending' END AS Status, COUNT(*) as Count FROM tasks GROUP BY done"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
