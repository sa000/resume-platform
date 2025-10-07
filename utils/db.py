"""
Database operations for the resume warehouse.

This module provides functions for:
- Database initialization and schema management
- Data insertion (candidates, experiences, education, skills)
- Full-text search index population (FTS5)
- Filter value pre-computation for fast filtering
- Search and retrieval operations

The warehouse uses a normalized star schema with performance
optimization tables (FTS5 for search, filter_values for fast lookups).
"""

import os
import sqlite3
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Database configuration
DB_PATH = "data/db/warehouse.db"
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def load_json(path: str) -> dict:
    """
    Load JSON data from a file.

    Args:
        path: Path to JSON file

    Returns:
        dict: Parsed JSON data
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """
    Create a connection to the SQLite database.

    Args:
        db_path: Path to database file (defaults to warehouse.db)

    Returns:
        sqlite3.Connection: Database connection object
    """
    return sqlite3.connect(db_path)


def drop_and_create_tables(conn: sqlite3.Connection) -> None:
    """
    Initialize database schema by dropping and recreating all tables.

    Creates a normalized star schema with:
    - Core tables: candidates, parsed_resumes, experiences, education, skills
    - Quality tracking: quality_scores
    - Performance optimization: filter_values (indexed lookups), candidates_fts (FTS5 search)

    Args:
        conn: Database connection

    Note:
        This will DELETE all existing data. Use only for initialization or reset.
    """
    cur = conn.cursor()
    cur.executescript("""
    DROP TABLE IF EXISTS candidates;
    DROP TABLE IF EXISTS parsed_resumes;
    DROP TABLE IF EXISTS experiences;
    DROP TABLE IF EXISTS education;
    DROP TABLE IF EXISTS skills;
    DROP TABLE IF EXISTS quality_scores;
    DROP TABLE IF EXISTS filter_values;
    DROP TABLE IF EXISTS candidates_fts;

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

    CREATE TABLE filter_values (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        field_name TEXT NOT NULL,
        field_value TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(field_name, field_value)
    );

    CREATE INDEX idx_filter_field ON filter_values(field_name);

    CREATE VIRTUAL TABLE candidates_fts USING fts5(
        candidate_id UNINDEXED,
        name,
        current_title,
        current_company,
        skills,
        experience_text,
        education_text,
        all_companies,
        certifications
    );
    """)
    conn.commit()


# ---------- INSERT FUNCTIONS ---------- #

def insert_parsed(conn: sqlite3.Connection, parsed_data: dict,
                  candidate_name: str, resume_path: str = None) -> int:
    """
    Insert parsed resume data into the warehouse.

    Stores the complete LLM-extracted JSON for archival and debugging.

    Args:
        conn: Database connection
        parsed_data: Full parsed resume dictionary
        candidate_name: Candidate's name
        resume_path: Path to original resume file

    Returns:
        int: Inserted row ID (parsed_resumes.id)
    """
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


def insert_candidate(conn: sqlite3.Connection, summary_data: dict,
                     parsed_id: int = None, resume_path: str = None) -> int:
    """
    Insert candidate summary profile into the warehouse.

    Stores executive summary data for fast candidate scanning.

    Args:
        conn: Database connection
        summary_data: Candidate summary dictionary
        parsed_id: Foreign key to parsed_resumes table
        resume_path: Path to original resume file

    Returns:
        int: Inserted row ID (candidates.id)
    """
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


def insert_experience(conn: sqlite3.Connection, candidate_id: int, exp: dict) -> None:
    """
    Insert a work experience record.

    Args:
        conn: Database connection
        candidate_id: Foreign key to candidates table
        exp: Experience dictionary with company, title, dates, metrics
    """
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


def insert_education(conn: sqlite3.Connection, candidate_id: int, edu: dict) -> None:
    """
    Insert an education record.

    Args:
        conn: Database connection
        candidate_id: Foreign key to candidates table
        edu: Education dictionary with degree, school, major, dates
    """
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


def insert_skill(conn: sqlite3.Connection, candidate_id: int, skill: str) -> None:
    """
    Insert a skill record (normalized, one skill per row).

    Args:
        conn: Database connection
        candidate_id: Foreign key to candidates table
        skill: Skill name (e.g., "Python", "DCF", "Machine Learning")
    """
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO skills (candidate_id, skill)
        VALUES (?, ?)
    """, (candidate_id, skill))
    conn.commit()


def insert_quality_score(conn: sqlite3.Connection, candidate_id: int,
                        quality_score: float, grade: str, total_issues: int,
                        issues: dict, missing_required: list = None,
                        missing_optional: list = None) -> int:
    """
    Insert data quality metrics for a candidate.

    Stores completeness score, letter grade, and validation issues
    for quality tracking and debugging.

    Args:
        conn: Database connection
        candidate_id: Foreign key to candidates table
        quality_score: Completeness percentage (0-100)
        grade: Letter grade (A-F)
        total_issues: Total validation issues count
        issues: Dictionary with critical/formatting/warnings lists
        missing_required: List of missing required fields
        missing_optional: List of missing optional fields

    Returns:
        int: Inserted row ID (quality_scores.id)
    """
    cur = conn.cursor()

    # Build data completeness dict
    data_completeness = {
        "missing_required": missing_required or [],
        "missing_optional": missing_optional or []
    }

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


def insert_filter_value(conn: sqlite3.Connection, field_name: str, field_value: str) -> None:
    """
    Insert a filter value for fast dropdown population.

    Uses INSERT OR IGNORE to automatically deduplicate values.
    Populates the pre-computed filter_values table for 10-100x
    faster filter loading compared to SELECT DISTINCT.

    Args:
        conn: Database connection
        field_name: Filter category (e.g., 'skill', 'company', 'geography')
        field_value: Value to index (e.g., 'Python', 'Goldman Sachs', 'US')
    """
    if not field_value or not str(field_value).strip():
        return  # Skip empty/null values

    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO filter_values (field_name, field_value, created_at)
        VALUES (?, ?, ?)
    """, (
        field_name,
        str(field_value).strip(),
        datetime.utcnow().isoformat()
    ))
    conn.commit()


def update_filter_values_for_candidate(conn: sqlite3.Connection, candidate_id: int,
                                      summary_data: dict, parsed_data: dict) -> None:
    """
    Extract and index all filterable values from candidate data.

    Populates filter_values table with all unique values for:
    - geography, sector, investment approach
    - skills, companies, schools, degrees

    This enables instant filter dropdown population without
    expensive SELECT DISTINCT queries.

    Args:
        conn: Database connection
        candidate_id: Foreign key to candidates table
        summary_data: Candidate summary dictionary
        parsed_data: Full parsed resume dictionary
    """
    # Geography
    if summary_data.get('primary_geography'):
        insert_filter_value(conn, 'geography', summary_data['primary_geography'])

    # Sector
    if summary_data.get('sector_focus'):
        # sector_focus can be a list, insert first one as primary
        sectors = summary_data['sector_focus']
        if isinstance(sectors, list) and len(sectors) > 0:
            insert_filter_value(conn, 'sector', sectors[0])
        elif isinstance(sectors, str):
            insert_filter_value(conn, 'sector', sectors)

    # Investment Approach
    if summary_data.get('investment_approach'):
        insert_filter_value(conn, 'approach', summary_data['investment_approach'])

    # Skills
    skills = summary_data.get('top_skills', []) or []
    for skill in skills:
        if skill:  # Skip None values
            insert_filter_value(conn, 'skill', skill)

    # Companies from experiences
    experiences = parsed_data.get('experiences', []) or []
    for exp in experiences:
        company = exp.get('company')
        if company:
            insert_filter_value(conn, 'company', company)

    # Schools and Degrees from education
    education = parsed_data.get('education', []) or []
    for edu in education:
        school = edu.get('school')
        degree = edu.get('degree')

        if school:
            insert_filter_value(conn, 'school', school)
        if degree:
            insert_filter_value(conn, 'degree', degree)


def insert_to_fts(conn: sqlite3.Connection, candidate_id: int,
                 parsed_data: dict, summary_data: dict) -> None:
    """
    Populate FTS5 full-text search index for a candidate.

    Combines all searchable text into a single indexed record:
    - Name, title, company
    - Skills, certifications
    - All experience text (companies, titles, bullet points)
    - Education text (degrees, majors, schools)

    Enables sub-second search with BM25 ranking across all candidate data.

    Args:
        conn: Database connection
        candidate_id: Foreign key to candidates table
        parsed_data: Full parsed resume dictionary
        summary_data: Candidate summary dictionary
    """
    # Skills text
    skills_text = ' '.join(summary_data.get('top_skills', []) or [])

    # Certifications text
    certs = summary_data.get('certifications', []) or []
    certs_text = ' '.join(certs) if certs else ''

    # Experience text: all companies, titles, and bullet points
    experiences = parsed_data.get('experiences', []) or []
    all_companies = []
    experience_parts = []

    for exp in experiences:
        company = exp.get('company', '')
        title = exp.get('title', '')
        if company:
            all_companies.append(company)
        experience_parts.append(f"{company} {title}")

        # Add bullet points for deeper search
        bullets = exp.get('bullet_points', [])
        if bullets:
            experience_parts.extend(bullets)

    experience_text = ' '.join(experience_parts)
    all_companies_text = ' '.join(all_companies)

    # Education text: degrees, majors, and schools
    education = parsed_data.get('education', []) or []
    education_parts = []

    for edu in education:
        degree = edu.get('degree', '')
        major = edu.get('major', '')
        school = edu.get('school', '')
        education_parts.append(f"{degree} {major} {school}")

    education_text = ' '.join(education_parts)

    # Insert into FTS table
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO candidates_fts (
            candidate_id, name, current_title, current_company,
            skills, experience_text, education_text, all_companies, certifications
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        candidate_id,
        summary_data.get('name', ''),
        summary_data.get('current_title', ''),
        summary_data.get('current_company', ''),
        skills_text,
        experience_text,
        education_text,
        all_companies_text,
        certs_text
    ))
    conn.commit()


# ---------- SEARCH FUNCTIONS ---------- #

def search_candidates(search_query: str, db_path: str = DB_PATH):
    """
    Full-text search across all candidate data using FTS5.

    Uses BM25 ranking algorithm for relevance scoring. Supports:
    - Simple terms: "Python"
    - Boolean operators: "Python AND machine learning"
    - Phrase matching: '"Goldman Sachs"'
    - Prefix matching: "Goldm*"

    Args:
        search_query: Search terms
        db_path: Path to database (defaults to warehouse.db)

    Returns:
        pandas.DataFrame: Matching candidates with all fields, ranked by relevance
        None: If search query is empty or search fails
    """
    import pandas as pd

    if not search_query or search_query.strip() == "":
        return None  # Return None to indicate no search performed

    conn = get_connection(db_path)

    # FTS5 query with ranking - join back to get all candidate data
    query = """
        SELECT
            c.*,
            GROUP_CONCAT(DISTINCT s.skill) AS all_skills,
            GROUP_CONCAT(DISTINCT e.company) AS all_companies,
            GROUP_CONCAT(DISTINCT ed.school) AS all_schools,
            GROUP_CONCAT(DISTINCT ed.degree) AS all_degrees,
            fts.rank
        FROM candidates_fts fts
        JOIN candidates c ON c.id = fts.candidate_id
        LEFT JOIN skills s ON s.candidate_id = c.id
        LEFT JOIN experiences e ON e.candidate_id = c.id
        LEFT JOIN education ed ON ed.candidate_id = c.id
        WHERE candidates_fts MATCH ?
        GROUP BY c.id
        ORDER BY fts.rank
    """

    try:
        df = pd.read_sql_query(query, conn, params=(search_query,))
        conn.close()
        return df
    except Exception as e:
        logger.error(f"Search failed: {e}")
        conn.close()
        return None


def get_filter_values(field_name: str, db_path: str = DB_PATH) -> list:
    """
    Fast retrieval of unique filter values using pre-computed lookup table.

    Replaces expensive SELECT DISTINCT queries with indexed lookups
    for 10-100x performance improvement.

    Args:
        field_name: Filter category (e.g., 'skill', 'company', 'geography')
        db_path: Path to database (defaults to warehouse.db)

    Returns:
        list: Sorted list of unique values for the specified field
    """
    conn = get_connection(db_path)

    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT field_value
            FROM filter_values
            WHERE field_name = ?
            ORDER BY field_value
        """, (field_name,))

        values = [row[0] for row in cur.fetchall()]
        conn.close()
        return values

    except Exception as e:
        logger.error(f"Failed to get filter values for {field_name}: {e}")
        conn.close()
        return []


def get_search_suggestions(db_path: str = DB_PATH) -> list:
    """
    Get common search terms for autocomplete/suggestions.

    Combines popular companies, skills, and degrees into a single
    sorted list for search bar suggestions.

    Args:
        db_path: Path to database (defaults to warehouse.db)

    Returns:
        list: Sorted list of unique search suggestions
    """
    import pandas as pd

    conn = get_connection(db_path)
    suggestions = []

    try:
        # Top companies
        companies = pd.read_sql_query(
            "SELECT DISTINCT company FROM experiences WHERE company IS NOT NULL ORDER BY company LIMIT 30",
            conn
        )
        suggestions.extend(companies['company'].tolist())

        # Top skills
        skills = pd.read_sql_query(
            "SELECT DISTINCT skill FROM skills WHERE skill IS NOT NULL ORDER BY skill LIMIT 30",
            conn
        )
        suggestions.extend(skills['skill'].tolist())

        # Degrees
        degrees = pd.read_sql_query(
            "SELECT DISTINCT degree FROM education WHERE degree IS NOT NULL ORDER BY degree",
            conn
        )
        suggestions.extend(degrees['degree'].tolist())

    except Exception as e:
        logger.error(f"Failed to get suggestions: {e}")

    conn.close()
    return sorted(set(suggestions))  # Remove duplicates and sort
