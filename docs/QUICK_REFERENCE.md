# Quick Reference Guide

## Common Commands

### Setup
```bash
# First-time setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "OPENAI_API_KEY=your_key" > .env

# Daily workflow
source venv/bin/activate
```

### Running the Application
```bash
# Launch Streamlit app
cd app
streamlit run app.py

# Open in browser (auto-opens or manually navigate to):
# http://localhost:8501
```

### Processing Resumes
```bash
# Option 1: Use Jupyter Notebook (recommended)
jupyter notebook Case_Study.ipynb
# Run cells 1-8 sequentially

# Option 2: Command line (future enhancement)
# python scripts/parse_resumes.py --input data/resumes/raw/
```

### Database Operations
```bash
# View database schema
sqlite3 data/db/warehouse.db ".schema"

# Count candidates
sqlite3 data/db/warehouse.db "SELECT COUNT(*) FROM candidates;"

# Query candidates
sqlite3 data/db/warehouse.db "SELECT name, current_company FROM candidates LIMIT 5;"

# Backup database
cp data/db/warehouse.db data/db/warehouse_backup_$(date +%Y%m%d).db

# Reset database (WARNING: Deletes all data!)
rm data/db/warehouse.db
# Then re-run notebook cells 7-8
```

---

## File Locations

| What | Where |
|------|-------|
| Raw resumes (PDF/DOCX) | `data/resumes/raw/` |
| Parsed JSON (detailed) | `data/resumes/processed/` |
| Summary JSON (executive) | `data/resumes/summaries/` |
| Validation reports | `data/resumes/candidate_validation/` |
| SQLite database | `data/db/warehouse.db` |
| Streamlit app | `app/app.py` |
| Custom CSS | `app/styles.css` |
| LLM prompts | `utils/prompts.py` |
| Database functions | `utils/db.py` |
| Parsing logic | `utils/parser.py` |
| Quality validation | `utils/data_validator.py` |

---

## Key Functions

### Parsing (`Case_Study.ipynb`)
```python
# Parse a single resume
from utils.parser import extract_text
from utils.prompts import RESUME_PARSER_PROMPT

text = extract_text("data/resumes/raw/resume.pdf")
parsed_data = parse_resume(text, filename="resume")

# Generate summary
summary_data = summarize_candidate(parsed_data, filename="resume")
```

### Database Operations (`utils/db.py`)
```python
from utils.db import get_connection, insert_candidate, insert_parsed

conn = get_connection()

# Insert parsed resume
parsed_id = insert_parsed(conn, parsed_data, candidate_name, resume_path)

# Insert candidate summary
candidate_id = insert_candidate(conn, summary_data, parsed_id, resume_path)

# Insert experiences, education, skills
for exp in parsed_data['experiences']:
    insert_experience(conn, candidate_id, exp)

# Populate search index
insert_to_fts(conn, candidate_id, parsed_data, summary_data)

# Update filter values
update_filter_values_for_candidate(conn, candidate_id, summary_data, parsed_data)

conn.close()
```

### Search (`utils/db.py`)
```python
from utils.db import search_candidates, get_filter_values

# Full-text search
results = search_candidates("Goldman Sachs Python")

# Get filter options
skills = get_filter_values("skill")
companies = get_filter_values("company")
```

---

## LLM Prompts

### Resume Parser Prompt
**Location**: `utils/prompts.py` → `RESUME_PARSER_PROMPT`

**Key Instructions**:
- Extract structured data from resume text
- Normalize dates to MMM-DD-YYYY format
- Normalize degrees to B.S., M.S., MBA, Ph.D.
- Extract hedge fund-specific metrics (Sharpe ratio, alpha, AUM)
- Output strict JSON schema

**Model**: GPT-4o-mini, temperature=0, JSON mode

### Summary Prompt
**Location**: `utils/prompts.py` → `SUMMARY_PROMPT`

**Key Instructions**:
- Extract executive summary from parsed data
- Identify current title/company from experiences[0]
- Summarize sector focus, geography, investment approach
- List top skills and notable companies
- Generate 2-3 sentence blurb

**Model**: GPT-4o-mini, temperature=0.2, JSON mode

---

## Database Schema Quick Reference

### Main Tables
```
candidates              # Summary profiles
├── id (PK)
├── name
├── current_title
├── current_company
├── years_experience
├── primary_sector
├── investment_approach
├── primary_geography
└── ...

experiences            # Work history
├── id (PK)
├── candidate_id (FK)
├── company
├── title
├── start_date, end_date
├── sharpe_ratio, alpha
└── ...

education              # Academic background
├── id (PK)
├── candidate_id (FK)
├── degree, major, school
└── ...

skills                 # Skills (normalized)
├── id (PK)
├── candidate_id (FK)
└── skill

candidates_fts         # Full-text search (FTS5)
└── (virtual table)

filter_values          # Pre-computed filters
├── field_name
└── field_value
```

**Detailed Schema**: See [WAREHOUSE_SCHEMA.md](WAREHOUSE_SCHEMA.md)

---

## Search Syntax

### Basic Search
```
Goldman Sachs          # Simple phrase
Python                 # Single term
```

### Advanced Search (FTS5)
```
Python AND machine     # Both terms required
Python OR R            # Either term
Python NOT Java        # Python but not Java
"Goldman Sachs"        # Exact phrase
Goldman*               # Prefix matching (Goldman, Goldmans, etc.)
```

### Example Searches
```
"JP Morgan" AND Python                    # Company + skill
CFA AND quantitative                      # Certification + approach
PhD AND "machine learning"                # Degree + skill phrase
Healthcare AND (Fundamental OR Sellside)  # Sector + approach
```

---

## Filter Fields

| Filter | Database Field | Example Values |
|--------|---------------|----------------|
| Geographic Market | `primary_geography` | US, Europe, Asia-Pacific |
| Investment Approach | `investment_approach` | Fundamental, Systematic |
| Sector | `primary_sector` | Technology, Healthcare, Financial Services |
| Education | `all_degrees` (derived) | B.S., M.S., MBA, Ph.D. |
| Company | `all_companies` (aggregated) | Goldman Sachs, JP Morgan, Citadel |
| School | `all_schools` (aggregated) | Harvard, MIT, Stanford |
| Years Experience | `years_experience` | 0-20+ (slider) |
| Skills | `all_skills` (aggregated) | Python, Bloomberg, Excel |

---

## Troubleshooting

### App won't start
```bash
# Check if warehouse.db exists
ls -la data/db/warehouse.db

# If missing, run notebook cells 7-8 to create it
jupyter notebook Case_Study.ipynb

# Check Python version
python --version  # Should be 3.13+

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Database is empty
```bash
# Check candidate count
sqlite3 data/db/warehouse.db "SELECT COUNT(*) FROM candidates;"

# If 0, re-run ingestion
jupyter notebook Case_Study.ipynb
# Run cell 8 (ingestion pipeline)
```

### Search not working
```bash
# Check if FTS table is populated
sqlite3 data/db/warehouse.db "SELECT COUNT(*) FROM candidates_fts;"

# Should match candidate count
# If 0, FTS index wasn't populated - re-run ingestion
```

### Filters are empty
```bash
# Check filter_values table
sqlite3 data/db/warehouse.db "SELECT COUNT(*) FROM filter_values;"

# Should have 100+ rows
# If 0, filter values weren't populated - re-run ingestion
```

### OpenAI API errors
```bash
# Check API key is set
cat .env

# Should show: OPENAI_API_KEY=sk-...
# If missing, create .env file with your key

# Test API key
python -c "from openai import OpenAI; import os; from dotenv import load_dotenv; load_dotenv(); client = OpenAI(); print('API key valid' if client.models.list() else 'Invalid')"
```

---

## Performance Tips

### For 10-100 candidates
- SQLite default settings are fine
- No optimization needed

### For 100-1,000 candidates
```sql
-- Analyze query planner
sqlite3 data/db/warehouse.db "ANALYZE;"

-- Optimize FTS index
sqlite3 data/db/warehouse.db "INSERT INTO candidates_fts(candidates_fts) VALUES('optimize');"
```

### For 1,000+ candidates
- Consider adding more indexes
- Run VACUUM periodically
- Monitor query performance with EXPLAIN QUERY PLAN

### For 10,000+ candidates
- Migrate to PostgreSQL
- Use connection pooling
- Consider read replicas

---

## Development Workflow

### Adding a new resume
1. Place PDF/DOCX in `data/resumes/raw/`
2. Open `Case_Study.ipynb`
3. Run cell 6 (parsing)
4. Run cell 8 (ingestion)
5. Refresh Streamlit app

### Modifying the schema
1. Edit `utils/db.py` → `drop_and_create_tables()`
2. Run notebook cell 7 to recreate database
3. Run notebook cell 8 to re-ingest all data
4. Update `utils/db.py` insert functions if needed

### Updating LLM prompts
1. Edit `utils/prompts.py`
2. Delete `data/resumes/processed/` and `data/resumes/summaries/`
3. Re-run notebook cell 6 to re-parse all resumes
4. Re-run notebook cell 8 to re-ingest

### Modifying the UI
1. Edit `app/app.py` or `app/styles.css`
2. Save changes
3. Streamlit auto-reloads (or manually refresh browser)

---

## Useful SQL Queries

### Analytics
```sql
-- Candidates by geography
SELECT primary_geography, COUNT(*) FROM candidates GROUP BY primary_geography;

-- Candidates by sector
SELECT primary_sector, COUNT(*) FROM candidates GROUP BY primary_sector;

-- Average years of experience
SELECT AVG(years_experience) FROM candidates;

-- Top skills
SELECT skill, COUNT(*) as count FROM skills GROUP BY skill ORDER BY count DESC LIMIT 10;

-- Top companies
SELECT company, COUNT(*) as count FROM experiences GROUP BY company ORDER BY count DESC LIMIT 10;
```

### Data Quality
```sql
-- Completeness scores
SELECT grade, COUNT(*) FROM quality_scores GROUP BY grade;

-- Average completeness
SELECT AVG(quality_score) FROM quality_scores;

-- Candidates with critical issues
SELECT c.name, qs.total_issues
FROM candidates c
JOIN quality_scores qs ON qs.candidate_id = c.id
WHERE json_extract(qs.issues, '$.critical') != '[]';
```

### Searching
```sql
-- Find candidates with specific skill
SELECT c.name, c.current_company
FROM candidates c
JOIN skills s ON s.candidate_id = c.id
WHERE s.skill LIKE '%Python%';

-- Find candidates from specific companies
SELECT DISTINCT c.name, e.company
FROM candidates c
JOIN experiences e ON e.candidate_id = c.id
WHERE e.company IN ('Goldman Sachs', 'JP Morgan', 'Citadel');
```

---

## Environment Variables

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o-mini | Yes | `sk-proj-abc123...` |

**File**: `.env` (not in version control)

**Example .env**:
```bash
OPENAI_API_KEY=sk-proj-your_key_here
```

---

## Dependencies

**Core**:
- `streamlit` - Web application framework
- `openai` - LLM API client
- `pandas` - Data processing
- `plotly` - Interactive visualizations
- `sqlite3` - Database (built into Python)

**Parsing**:
- `PyPDF2` - PDF text extraction
- `python-docx` - DOCX text extraction

**Utilities**:
- `python-dotenv` - Environment variable management

**Full list**: See `requirements.txt`

---

## Resources

- [Main README](../README.md) - Complete documentation
- [Warehouse Schema](WAREHOUSE_SCHEMA.md) - Database design details
- [Streamlit Docs](https://docs.streamlit.io/) - Web framework
- [SQLite FTS5](https://www.sqlite.org/fts5.html) - Full-text search
- [OpenAI API Docs](https://platform.openai.com/docs/api-reference) - LLM API

---

## Support

For issues or questions:
1. Check this quick reference
2. Review [main README](../README.md)
3. Check [WAREHOUSE_SCHEMA.md](WAREHOUSE_SCHEMA.md) for database questions
4. Contact development team
