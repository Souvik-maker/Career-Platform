import sqlite3
import json
import os

DB_NAME = "career_platform.db"
DB_PATH = os.path.abspath(DB_NAME)

def get_connection():
    """Helper to establish a stable connection with WAL mode and timeout enabled."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL;")  # Prevents Streamlit database locking
    return conn

def init_db():
    """Initializes the local SQLite database and creates necessary tables."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Table 1: Resumes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                resume_text TEXT NOT NULL,
                parsed_skills TEXT,
                parsed_certifications TEXT,
                experience TEXT,
                recommended_roles TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table 2: Job Searches
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER,
                selected_role TEXT,
                company TEXT,
                title TEXT,
                location TEXT,
                description TEXT,
                required_skills TEXT,
                FOREIGN KEY (resume_id) REFERENCES resumes (id)
            )
        """)

        # Table 3: Match & Gap Analysis
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS match_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER,
                job_title TEXT,
                company TEXT,
                match_score REAL,
                matched_skills TEXT,
                missing_skills TEXT,
                recommendation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (resume_id) REFERENCES resumes (id)
            )
        """)

        # Table 4: Downloadable Reports & Resumes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS generated_resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER,
                job_title TEXT,
                company TEXT,
                tailored_resume_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER,
                report_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()
        print(f"[DB SUCCESS] Database initialized at: {DB_PATH}")
    except Exception as e:
        print(f"[DB ERROR] Failed to initialize DB: {e}")

def save_initial_resume(file_name: str, resume_text: str) -> int:
    """Saves raw uploaded resume text and returns the row ID."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO resumes (file_name, resume_text) VALUES (?, ?)",
            (file_name, resume_text)
        )
        resume_id = cursor.lastrowid
        conn.commit()
        conn.close()
        print(f"[DB SUCCESS] Saved initial resume with ID: {resume_id}")
        return resume_id
    except Exception as e:
        print(f"[DB ERROR] save_initial_resume failed: {e}")
        return -1

def update_resume_analysis(resume_id: int, skills: list, certifications: list, experience: str, roles: list):
    """Updates the saved resume record with analyzed skills and recommended roles."""
    if resume_id == -1:
        print("[DB WARNING] Invalid resume_id passed to update_resume_analysis.")
        return

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE resumes 
            SET parsed_skills = ?, parsed_certifications = ?, experience = ?, recommended_roles = ?
            WHERE id = ?
        """, (json.dumps(skills), json.dumps(certifications), experience, json.dumps(roles), resume_id))
        conn.commit()
        conn.close()
        print(f"[DB SUCCESS] Updated resume analysis for ID: {resume_id}")
    except Exception as e:
        print(f"[DB ERROR] update_resume_analysis failed: {e}")

def save_parsed_jobs(resume_id: int, selected_role: str, parsed_jobs: list):
    """Saves fetched and parsed jobs into the database."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        for job in parsed_jobs:
            cursor.execute("""
                INSERT INTO job_searches (
                    resume_id, selected_role, company, title, location, description, required_skills
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                resume_id,
                selected_role,
                job.get("company", ""),
                job.get("title", ""),
                job.get("location", ""),
                job.get("description", ""),
                json.dumps(job.get("required_skills", []))
            ))
        conn.commit()
        conn.close()
        print(f"[DB SUCCESS] Saved {len(parsed_jobs)} parsed jobs for resume ID: {resume_id}")
    except Exception as e:
        print(f"[DB ERROR] save_parsed_jobs failed: {e}")

def save_match_results(resume_id: int, match_results: list):
    """Saves Phase 3 match scores and skill gap analyses to the database."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        for item in match_results:
            cursor.execute("""
                INSERT INTO match_analysis (
                    resume_id, job_title, company, match_score, matched_skills, missing_skills, recommendation
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                resume_id,
                item.get("job_title", ""),
                item.get("company", ""),
                item.get("match_score", 0.0),
                json.dumps(item.get("matched_skills", [])),
                json.dumps(item.get("missing_skills", [])),
                item.get("recommendation", "")
            ))
        conn.commit()
        conn.close()
        print(f"[DB SUCCESS] Saved match results for resume ID: {resume_id}")
    except Exception as e:
        print(f"[DB ERROR] save_match_results failed: {e}")

def save_generated_resume(resume_id: int, job_title: str, company: str, content: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO generated_resumes (resume_id, job_title, company, tailored_resume_text)
            VALUES (?, ?, ?, ?)
        """, (resume_id, job_title, company, content))
        conn.commit()
        conn.close()
        print(f"[DB SUCCESS] Saved generated resume for {company}")
    except Exception as e:
        print(f"[DB ERROR] save_generated_resume failed: {e}")

def save_market_report(resume_id: int, report_text: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO market_reports (resume_id, report_text)
            VALUES (?, ?)
        """, (resume_id, report_text))
        conn.commit()
        conn.close()
        print(f"[DB SUCCESS] Saved market report for resume ID: {resume_id}")
    except Exception as e:
        print(f"[DB ERROR] save_market_report failed: {e}")