import os
import sqlite3
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# === Database Path ===
DB_PATH = "data/db/warehouse.db"

# Ensure the directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def load_json(path):
    print(path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_connection(db_path: str = DB_PATH):
    print('db path', db_path)
    """Return a SQLite connection object."""
    return sqlite3.connect(db_path)


def drop_and_create_tables(conn):
    """Drop existing tables (for debugging) and recreate schema."""
    cur = conn.cursor()
    cur.executescript("""
    DROP TABLE IF EXISTS candidates;
    DROP TABLE IF EXISTS parsed_resumes;
    DROP TABLE IF EXISTS experiences;
    DROP TABLE IF EXISTS education;
    DROP TABLE IF EXISTS skills;
    DROP TABLE IF EXISTS quality_scores;

    CREATE TABLE candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        current_title TEXT,
        current_company TEXT,
        years_experience REAL,
        primary_sector TEXT,
        investment_approach TEXT,
        primary_geography TEXT,
        summary_blurb TEXT,
        top_skills JSON,
        notable_experience JSON,
        education_highlight TEXT,
        certifications JSON,
        resume_path TEXT,
        parsed_id INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE parsed_resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_name TEXT,
        parsed_json JSON,
        source_file TEXT,
        resume_path TEXT,
        summary_id INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE experiences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER,
        company TEXT,
        title TEXT,
        start_date TEXT,
        end_date TEXT,
        sectors JSON,
        approach TEXT,
        client_type TEXT,
        num_companies_covered INTEGER,
        num_sectors_covered INTEGER,
        coverage_value TEXT,
        regions_covered JSON,
        sharpe_ratio REAL,
        alpha TEXT,
        valuation_methods_used JSON,
        quant_tools_used JSON,
        bullet_points JSON,
        FOREIGN KEY(candidate_id) REFERENCES candidates(id)
    );

    CREATE TABLE education (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER,
        degree TEXT,
        major TEXT,
        school TEXT,
        start_date TEXT,
        end_date TEXT,
        honors TEXT,
        FOREIGN KEY(candidate_id) REFERENCES candidates(id)
    );

    CREATE TABLE skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER,
        skill TEXT,
        FOREIGN KEY(candidate_id) REFERENCES candidates(id)
    );

    CREATE TABLE quality_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER,
        quality_score REAL,
        grade TEXT,
        total_issues INTEGER,
        issues JSON,
        data_completeness JSON,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(candidate_id) REFERENCES candidates(id)
    );
    """)
    conn.commit()


# ---------- INSERT FUNCTIONS ---------- #

def insert_parsed(conn, parsed_data: dict, candidate_name: str, resume_path: str = None) -> int:
    """Insert parsed resume JSON. Returns inserted row ID."""
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO parsed_resumes (
            candidate_name, parsed_json, source_file, resume_path, created_at
        ) VALUES (?, ?, ?, ?, ?)
    """, (
        candidate_name,
        json.dumps(parsed_data),
        f"{candidate_name}.json",
        resume_path,
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    return cur.lastrowid


def insert_candidate(conn, summary_data: dict, parsed_id: int = None, resume_path: str = None) -> int:
    """Insert candidate summary. Returns inserted row ID."""
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO candidates (
            name, current_title, current_company, years_experience,
            primary_sector, investment_approach, primary_geography,
            summary_blurb, top_skills, notable_experience,
            education_highlight, certifications, resume_path, parsed_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        summary_data.get("name"),
        summary_data.get("current_title"),
        summary_data.get("current_company"),
        summary_data.get("years_experience"),
        summary_data.get("sector_focus")[0] if summary_data.get("sector_focus") else None,
        summary_data.get("investment_approach"),
        summary_data.get("primary_geography"),
        summary_data.get("summary_blurb"),
        json.dumps(summary_data.get("top_skills")),
        json.dumps(summary_data.get("notable_experience")),
        summary_data.get("education_highlight"),
        json.dumps(summary_data.get("certifications")) if summary_data.get("certifications") else None,
        resume_path,
        parsed_id,
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    return cur.lastrowid


def insert_experience(conn, candidate_id: int, exp: dict):
    """Insert a single experience record for a candidate."""
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO experiences (
            candidate_id, company, title, start_date, end_date, sectors, approach, client_type,
            num_companies_covered, num_sectors_covered, coverage_value, regions_covered,
            sharpe_ratio, alpha, valuation_methods_used, quant_tools_used, bullet_points
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        candidate_id,
        exp.get("company"),
        exp.get("title"),
        exp.get("start"),
        exp.get("end"),
        json.dumps(exp.get("sectors")) if exp.get("sectors") else None,
        exp.get("approach"),
        exp.get("client_type"),
        exp.get("num_companies_covered"),
        exp.get("num_sectors_covered"),
        exp.get("coverage_value"),
        json.dumps(exp.get("regions_covered")) if exp.get("regions_covered") else None,
        exp.get("sharpe_ratio"),
        exp.get("alpha"),
        json.dumps(exp.get("valuation_methods_used")) if exp.get("valuation_methods_used") else None,
        json.dumps(exp.get("quant_tools_used")) if exp.get("quant_tools_used") else None,
        json.dumps(exp.get("bullet_points"))
    ))
    conn.commit()


def insert_education(conn, candidate_id: int, edu: dict):
    """Insert a single education record for a candidate."""
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO education (
            candidate_id, degree, major, school, start_date, end_date, honors
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        candidate_id,
        edu.get("degree"),
        edu.get("major"),
        edu.get("school"),
        edu.get("start"),
        edu.get("end"),
        edu.get("honors")
    ))
    conn.commit()


def insert_skill(conn, candidate_id: int, skill: str):
    """Insert a single skill for a candidate."""
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO skills (candidate_id, skill)
        VALUES (?, ?)
    """, (candidate_id, skill))
    conn.commit()


def insert_quality_score(conn, candidate_id: int, quality_score: float, grade: str,
                        total_issues: int, issues: list, data_completeness: dict):
    """Insert quality score record for a candidate."""
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO quality_scores (
            candidate_id, quality_score, grade, total_issues, issues, data_completeness, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        candidate_id,
        quality_score,
        grade,
        total_issues,
        json.dumps(issues),
        json.dumps(data_completeness),
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    return cur.lastrowid
