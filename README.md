# Candidate Resume Search Platform

> **Resume Parser Case Study: By Sakibul Alam**
>
> Built for Millennium's Business Development team to efficiently source and evaluate analyst talent across global markets, investment strategies, and sectors.

---

## Table of Contents
- [Business Context](#business-context)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Usage Guide](#usage-guide)
- [Architecture Overview](#architecture-overview)
- [System Design](#system-design)
- [Future Enhancements](#future-enhancements)

---

## Business Context

### The Challenge
Millennium's Business Development has to comb through resumes to find promising candidates for their roles. This case study is limited to 10 resumes but in reality, they'll deal with thousands of resumes and want a platform to find the right candidates for the right job as manually parsing through them is time consuming.

### The Solution
A web app that allows the team to comb through resumes with relevant filters such as sectors, education, and experience. We'll use AI to help extract the data from the resumes into a backend that can power the web app.

---

## Key Features

### Search & Filtering
- **Filters**:
  - Geographic market
  - Investment approach (Fundamental vs. Quantitative)
  - Sector focus
  - Education level (BS, MS, MBA, PhD)
  - Past employers
  - Schools
  - Years of experience (range slider)
  - Skills (multi-select)

- **Full-Text Search (FTS5)**: Lightning-fast search across all candidate data including names, companies, skills, education, certifications, and **experience descriptions** (bullet points extracted by AI). Future iterations would scale this with Elastic Search.

### Candidate Profiles
- **Rich Detail Views**: Expandable profiles with full work history, education, skills, and certifications
- **Performance Metrics**: Sharpe ratios, alpha, AUM/coverage, valuation methods, quant tools if applicable, extracted from the resume
- **Resume Viewer**: Embedded PDF/DOCX preview with download capability
- **Role Flagging**: Flag candidates for specific job requisitions and track across roles (Demo purposes only)

### Analytics Dashboard
- **Geographic Distribution**: Bar charts showing candidate density by region
- **Sector Breakdown**: Donut chart with sector allocations
- **Investment Approach**: Distribution of fundamental vs. quantitative experience
- **Real-Time Metrics**: Dynamic candidate counts based on applied filters

---

## Quick Start

### Prerequisites
- Python 3.13+
- OpenAI API Key

### Installation

```bash
# Clone repository
git clone <repo_url>
cd resume-platform

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

### Running the Pipeline

**1. Parse Resumes & Build Warehouse**
```bash
# Open Jupyter notebook 
No 
jupyter notebook Case_Study.ipynb

# No need to run the code, all pipelines are built. Can simply launch the app. 
```

**2. Launch Streamlit App**
```bash
cd app
streamlit run app.py
```

The app will open at `http://localhost:8501`
The app is also live at `https://resume-platform-sakib.streamlit.app/`

---

## Project Structure

```
resume-platform/
├── Case_Study.ipynb           # Main pipeline: parsing, validation, warehouse ingestion
├── README.md                  # This file
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (not in repo)
│
├── app/                       # Streamlit application
│   ├── app.py                 # Main application file
│   └── styles.css             # Custom CSS styling
│
├── utils/                     # Shared utility modules
│   ├── parser.py              # Text extraction (PDF/DOCX)
│   ├── prompts.py             # LLM prompts for parsing and summarization
│   ├── db.py                  # Database operations and schema
│   └── data_validator.py      # Quality validation and completeness scoring
│
├── data/
│   ├── resumes/
│   │   ├── raw/               # Original resume files (PDF/DOCX)
│   │   ├── processed/         # Parsed JSON (detailed)
│   │   ├── summaries/         # Summary JSON (executive)
│   │   └── candidate_validation/  # Quality reports
│   └── db/
│       └── warehouse.db       # SQLite database
│
└── docs/                      # Documentation and diagrams
    ├── WAREHOUSE_SCHEMA.md    # Detailed database schema and query patterns
    ├── QUICK_REFERENCE.md     # Commands, functions, and troubleshooting
    └── screenshots/           # Application screenshots for README
```

---

## Usage Guide

### Using the Search Platform

#### 1. Filtering
- **Geographic Market**: Filter by US, Europe, or Asia-Pacific
- **Investment Approach**: Fundamental vs. Systematic
- **Sector**: Technology, Healthcare, Financial Services, etc.
- **Education**: Filter by highest degree (BS, MS, MBA, PhD)
- **Company**: Any past employer (e.g., "JP Morgan", "Citadel")
- **School**: Alma mater (e.g., "Harvard", "MIT")
- **Experience**: Years of experience (slider)
- **Skills**: Multi-select (e.g., "Python", "Bloomberg", "DCF")

#### 2. Candidate Profiles
- Click any result to expand full profile
- View detailed experience with metrics (Sharpe ratio, alpha, AUM)
- See complete education history
- Review all skills and certifications
- Preview or download original resume

#### 3 Flagging for Roles (Demo)
- Flag candidates for specific job requisitions (Role 1, Role 2, Role 3)
- Track flagged candidates in the sidebar
- Review flagged candidates by role in dedicated tabs

#### 4. Smart Search Experimental
**Free-text search** across all candidate data text data:
- Example: `machine learning` → Matches "machine learning" via the text of the resume

### Analytics Dashboard
- **Geographic Distribution**: See where candidates are concentrated
- **Sector Breakdown**: Understand sector coverage in your pipeline
- **Investment Approach**: Balance between fundamental and quant talent

---

## Architecture Overview

### High-Level System Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Resume Processing Pipeline                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Raw Resumes (PDF/DOCX)                                              │
│         ↓                                                             │
│  Text Extraction (PyPDF2, python-docx)                               │
│         ↓                                                             │
│  LLM Parsing (GPT-4o-mini + Custom Prompts)                          │
│         ↓                                                             │
│  Structured Data (JSON)                                              │
│         ├──> Parsed Resume (detailed)                                │
│         └──> Candidate Summary (executive overview)                  │
│         ↓                                                             │
│  Data Validation                                                     │
│         ↓                                                             │
│  SQLite Warehouse (warehouse.db)                                     │
│         ├──> Normalized tables (candidates, experiences, education)  │
│         ├──> Full-text search index (FTS5)                           │
│         └──> Pre-computed filter values                              │
│         ↓                                                             │
│  Streamlit Web Application                                           │
│         ├──> Search & Filter Interface                               │
│         ├──> Analytics Visualizations (Plotly)                       │
│         └──> Candidate Profile Views                                 │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Resume Parsing

We first parse the text from the word document or PDF via `utils/parser.py`. We then feed this into AI using 2 prompts in `utils/prompts.py` to extract data from the resume:

- **RESUME_PARSER_PROMPT**: Extracts all the properties we want from a candidate (experiences, education, skills, email, etc). This gets saved in `data/resumes/processed/`
- **SUMMARY_PROMPT**: Extracts a high-level summary given the JSON from RESUME_PARSER_PROMPT and the resume to help the recruiter have a high-level summary of the candidate. In a future iteration, this prompt could probably be extraneous and we could derive said insights from the output of RESUME_PARSER_PROMPT. The output of the summary prompt is saved in `data/resumes/summaries/`

### Data Validation

Sometimes AI would extract nulls or put the wrong information in the field. This validation is mainly used for debugging. This is in `utils/data_validator.py`. As resumes scale, we'll need a way to understand which resumes are presenting problems (noticed that resumes with tabular formats were difficult). Potentially resumes with color or pictures could be problematic too.

Having the validation also helps to have data in a standardized way, such as having education, dates, etc standardized so we have filters working accordingly.

### Warehouse

With the extracted JSON files we need to have a warehouse so Streamlit can talk to the app. For now, we spin up SQLite as a local warehouse, but for a bigger scale we'll need a cloud solution, potentially Athena or RDS in AWS. NoSQL databases might be of use to store the text since properties could be changing for resumes, and perhaps an Elastic Search type database for fast lookups against the text.

Since resumes could scale into thousands, filtering can be costly by having to scan our database for each column (education, experience, skills, etc). So instead we pre-computed a filter table that has all the unique values for the app to talk to directly.

We also use Full Text Search (FTS5), an extension from SQLite to help do full text search across these resumes. That way users can search across resumes and get insights. We can use these insights to help design future iterations of properties we want to capture.

---

## System Design

### Database Schema Overview

#### Core Tables
- **`candidates`**: Candidate summary profiles (current role, geography, sector, years of experience)
- **`parsed_resumes`**: Full parsed resume JSON with metadata
- **`experiences`**: Individual work experiences with performance metrics
- **`education`**: Educational background (degrees, schools, honors)
- **`skills`**: Individual skills (one skill per row for flexible querying)
- **`quality_scores`**: Data completeness and validation results

#### Performance Optimization Tables
- **`filter_values`**: Pre-computed unique values for all filterable fields (10-100x faster than SELECT DISTINCT)
- **`candidates_fts`**: FTS5 full-text search index with BM25 ranking

> **📊 Detailed Schema Documentation**: See [docs/WAREHOUSE_SCHEMA.md](docs/WAREHOUSE_SCHEMA.md) for complete ERD, query patterns, and performance analysis.

### Entity Relationship Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          WAREHOUSE DATABASE SCHEMA                            │
└──────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────┐
                    │   parsed_resumes        │
                    ├─────────────────────────┤
                    │ id (PK)                 │
                    │ candidate_name          │
                    │ parsed_json (JSON)      │──── Full LLM-extracted data
                    │ source_file             │     (all fields, dates, metrics)
                    │ resume_path             │
                    │ created_at              │
                    └─────────────────────────┘
                               │
                               │ FK: parsed_id
                               │ (1:1 relationship)
                               ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  ┌──────────────────────────┐          ┌──────────────────────────┐        │
│  │   candidates             │          │   quality_scores         │        │
│  ├──────────────────────────┤          ├──────────────────────────┤        │
│  │ id (PK)                  │◄────────┤│ id (PK)                  │        │
│  │ name                     │    1:1   │ candidate_id (FK)        │        │
│  │ current_title            │          │ quality_score (0-100)    │        │
│  │ current_company          │          │ grade (A-F)              │        │
│  │ years_experience         │          │ total_issues             │        │
│  │ primary_sector           │          │ issues (JSON)            │        │
│  │ investment_approach      │          │ data_completeness (JSON) │        │
│  │ primary_geography        │          │ created_at               │        │
│  │ summary_blurb (TEXT)     │          └──────────────────────────┘        │
│  │ top_skills (JSON)        │                                               │
│  │ notable_experience (JSON)│            Data Validation Results            │
│  │ education_highlight      │            - Completeness: 10 required +      │
│  │ certifications (JSON)    │              5 optional fields                │
│  │ resume_path              │            - Format checks: dates, names,     │
│  │ parsed_id (FK)           │              degrees                          │
│  │ created_at               │                                               │
│  └──────────────────────────┘                                               │
│         │    │    │    │                                                     │
│         │    │    │    │                                                     │
└─────────┼────┼────┼────┼─────────────────────────────────────────────────────┘
          │    │    │    │
          │    │    │    └─────────────────────────────────────────┐
          │    │    │                                         1:N  │
          │    │    │    ┌──────────────────────────┐             │
          │    │    │    │   education              │             │
          │    │    │    ├──────────────────────────┤             │
          │    │    └───►│ id (PK)                  │             │
          │    │    1:N  │ candidate_id (FK)        │             │
          │    │         │ degree                   │             │
          │    │         │ major                    │             │
          │    │         │ school                   │             │
          │    │         │ start_date               │             │
          │    │         │ end_date                 │             │
          │    │         │ honors                   │             │
          │    │         └──────────────────────────┘             │
          │    │                                                   │
          │    │         ┌──────────────────────────┐             │
          │    │         │   skills                 │             │
          │    │         ├──────────────────────────┤             │
          │    └────────►│ id (PK)                  │             │
          │         1:N  │ candidate_id (FK)        │             │
          │              │ skill (TEXT)             │             │
          │              └──────────────────────────┘             │
          │                                                        │
          │              ┌──────────────────────────────────────┐ │
          │              │   experiences                        │ │
          │              ├──────────────────────────────────────┤ │
          └─────────────►│ id (PK)                              │◄┘
                    1:N  │ candidate_id (FK)                    │
                         │ company                              │
                         │ title                                │
                         │ start_date, end_date                 │
                         │ sectors (JSON)                       │
                         │ approach                             │
                         │ client_type                          │
                         │ num_companies_covered                │
                         │ num_sectors_covered                  │
                         │ coverage_value                       │
                         │ regions_covered (JSON)               │
                         │ sharpe_ratio (REAL)                  │
                         │ alpha (TEXT)                         │
                         │ valuation_methods_used (JSON)        │
                         │ quant_tools_used (JSON)              │
                         │ bullet_points (JSON)                 │
                         └──────────────────────────────────────┘
                                   Hedge Fund Metrics


┌──────────────────────────────────────────────────────────────────────────────┐
│                      PERFORMANCE OPTIMIZATION LAYER                           │
└──────────────────────────────────────────────────────────────────────────────┘

  ┌────────────────────────────────┐       ┌────────────────────────────────┐
  │  candidates_fts (FTS5)         │       │  filter_values                 │
  ├────────────────────────────────┤       ├────────────────────────────────┤
  │ candidate_id (UNINDEXED)       │       │ id (PK)                        │
  │ name (INDEXED)                 │       │ field_name (INDEXED)           │
  │ current_title (INDEXED)        │       │ field_value                    │
  │ current_company (INDEXED)      │       │ created_at                     │
  │ skills (INDEXED)               │       │                                │
  │ experience_text (INDEXED)      │       │ UNIQUE(field_name,field_value) │
  │ education_text (INDEXED)       │       └────────────────────────────────┘
  │ all_companies (INDEXED)        │                     │
  │ certifications (INDEXED)       │                     │
  └────────────────────────────────┘                     │
            │                                            │
            │ Full-Text Search                           │ Pre-computed Lookups
            │ - BM25 ranking                             │ - geography
            │ - Sub-second search                        │ - sector
            │ - Boolean operators                        │ - approach
            │ - Phrase matching                          │ - skill
            │                                            │ - company
            └──────────────┐                             │ - school
                           │                             │ - degree
                           ↓                             ↓
                    ┌────────────────────────────────────────┐
                    │   Streamlit Application Queries        │
                    │   - Search: FTS5 MATCH                 │
                    │   - Filters: JOIN on filter_values     │
                    │   - Details: JOIN all related tables   │
                    └────────────────────────────────────────┘
```

### Data Processing Flow

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         DATA INGESTION PIPELINE                              │
│                         (Case_Study.ipynb)                                   │
└──────────────────────────────────────────────────────────────────────────────┘

 INPUT: data/resumes/raw/*.{pdf,docx}
   │
   │
   ├──────────── STEP 1: TEXT EXTRACTION ────────────┐
   │                                                   │
   │  ┌────────────────────┐    ┌─────────────────┐  │
   │  │  PDF Resume        │    │  DOCX Resume    │  │
   │  │  (PyPDF2)          │    │  (python-docx)  │  │
   │  └────────┬───────────┘    └────────┬────────┘  │
   │           │                         │            │
   │           └──────────┬──────────────┘            │
   │                      │                           │
   │                      ▼                           │
   │            ┌──────────────────┐                  │
   │            │  Raw Text        │                  │
   │            │  - Headings      │                  │
   │            │  - Paragraphs    │                  │
   │            │  - Tables        │                  │
   │            │  - Bullet points │                  │
   │            └──────────────────┘                  │
   │                      │                           │
   └──────────────────────┼───────────────────────────┘
                          │
                          │
   ┌──────────────────────┼───────────────────────────┐
   │                      │                           │
   │       STEP 2: LLM PARSING (GPT-4o-mini)         │
   │                      │                           │
   │                      ▼                           │
   │     ┌───────────────────────────────────┐       │
   │     │  RESUME_PARSER_PROMPT             │       │
   │     │  - Extract structured fields      │       │
   │     │  - Normalize dates (MMM-DD-YYYY)  │       │
   │     │  - Normalize degrees (B.S., MBA)  │       │
   │     │  - Extract metrics (Sharpe, AUM)  │       │
   │     │  - JSON schema enforcement        │       │
   │     └───────────────┬───────────────────┘       │
   │                     │                           │
   │                     ▼                           │
   │     ┌───────────────────────────────────┐       │
   │     │  Parsed Resume JSON               │       │
   │     │  {                                │       │
   │     │    name, email, phone, location,  │       │
   │     │    experiences: [                 │       │
   │     │      {company, title, dates,      │       │
   │     │       sectors, sharpe_ratio,      │       │
   │     │       alpha, coverage, ...}       │       │
   │     │    ],                             │       │
   │     │    education: [...],              │       │
   │     │    skills: [...]                  │       │
   │     │  }                                │       │
   │     └───────────────┬───────────────────┘       │
   │                     │                           │
   │  OUTPUT: data/resumes/processed/{name}_parsed.json
   └─────────────────────┼───────────────────────────┘
                         │
                         │
   ┌─────────────────────┼───────────────────────────┐
   │                     │                           │
   │       STEP 3: SUMMARY GENERATION                │
   │                     │                           │
   │                     ▼                           │
   │     ┌───────────────────────────────────┐       │
   │     │  SUMMARY_PROMPT                   │       │
   │     │  - Extract current role (exp[0])  │       │
   │     │  - Identify sector focus          │       │
   │     │  - Calculate years experience     │       │
   │     │  - List top skills                │       │
   │     │  - Generate summary blurb         │       │
   │     └───────────────┬───────────────────┘       │
   │                     │                           │
   │                     ▼                           │
   │     ┌───────────────────────────────────┐       │
   │     │  Candidate Summary JSON           │       │
   │     │  {                                │       │
   │     │    name, current_title,           │       │
   │     │    current_company,               │       │
   │     │    years_experience,              │       │
   │     │    sector_focus,                  │       │
   │     │    investment_approach,           │       │
   │     │    primary_geography,             │       │
   │     │    top_skills,                    │       │
   │     │    summary_blurb                  │       │
   │     │  }                                │       │
   │     └───────────────┬───────────────────┘       │
   │                     │                           │
   │  OUTPUT: data/resumes/summaries/{name}_summary.json
   └─────────────────────┼───────────────────────────┘
                         │
                         │
   ┌─────────────────────┼───────────────────────────┐
   │                     │                           │
   │       STEP 4: DATA VALIDATION                   │
   │                     │                           │
   │                     ▼                           │
   │     ┌───────────────────────────────────┐       │
   │     │  calculate_completeness_score()   │       │
   │     │  - Check 10 required fields       │       │
   │     │  - Check 5 optional fields        │       │
   │     │  - Calculate % complete           │       │
   │     │  - Assign letter grade (A-F)      │       │
   │     └───────────────┬───────────────────┘       │
   │                     │                           │
   │                     ▼                           │
   │     ┌───────────────────────────────────┐       │
   │     │  validate_resume_data()           │       │
   │     │  - Check date formats             │       │
   │     │  - Check name title case          │       │
   │     │  - Check degree formats           │       │
   │     │  - Flag critical/formatting/warn  │       │
   │     └───────────────┬───────────────────┘       │
   │                     │                           │
   │  OUTPUT: data/resumes/candidate_validation/{name}_validation.json
   └─────────────────────┼───────────────────────────┘
                         │
                         │
   ┌─────────────────────┼───────────────────────────┐
   │                     │                           │
   │    STEP 5: DATABASE INGESTION                   │
   │              (warehouse.db)                     │
   │                     │                           │
   │                     ▼                           │
   │     ┌───────────────────────────────────┐       │
   │     │  1. insert_parsed()               │       │
   │     │     → parsed_resumes table        │       │
   │     │                                   │       │
   │     │  2. insert_candidate()            │       │
   │     │     → candidates table            │       │
   │     │                                   │       │
   │     │  3. insert_experience() (loop)    │       │
   │     │     → experiences table           │       │
   │     │                                   │       │
   │     │  4. insert_education() (loop)     │       │
   │     │     → education table             │       │
   │     │                                   │       │
   │     │  5. insert_skill() (loop)         │       │
   │     │     → skills table                │       │
   │     │                                   │       │
   │     │  6. insert_quality_score()        │       │
   │     │     → quality_scores table        │       │
   │     └───────────────┬───────────────────┘       │
   │                     │                           │
   └─────────────────────┼───────────────────────────┘
                         │
                         │
   ┌─────────────────────┼───────────────────────────┐
   │                     │                           │
   │    STEP 6: SEARCH INDEX & FILTER POPULATION     │
   │                     │                           │
   │                     ▼                           │
   │     ┌───────────────────────────────────┐       │
   │     │  insert_to_fts()                  │       │
   │     │  - Combine all searchable text    │       │
   │     │  - Skills, companies, education   │       │
   │     │  - Certifications, bullet points  │       │
   │     │  → candidates_fts (FTS5 index)    │       │
   │     └───────────────┬───────────────────┘       │
   │                     │                           │
   │                     ▼                           │
   │     ┌───────────────────────────────────┐       │
   │     │  update_filter_values_for_candidate()│    │
   │     │  - Extract geography              │       │
   │     │  - Extract sector                 │       │
   │     │  - Extract approach               │       │
   │     │  - Extract all skills             │       │
   │     │  - Extract all companies          │       │
   │     │  - Extract all schools            │       │
   │     │  - Extract all degrees            │       │
   │     │  → filter_values (lookup table)   │       │
   │     └───────────────┬───────────────────┘       │
   │                     │                           │
   └─────────────────────┼───────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Data Ready for App  │
              │  - Searchable (FTS5) │
              │  - Filterable        │
              │  - Complete profiles │
              └──────────────────────┘
```

---

## Future Enhancements

- **Validation**: We only received a sample of resumes. As we scale, there will be issues we will encounter from the parsing. Whether be nulls, hallucination or picking the wrong values, or different formats. We'll need to work on the prompt engineering and parsing to make sure we have data in a clean warehouse.

- **Job Matching x Candidates**: We should allow users to upload a job posting so we can find the best candidate for the role. We can do surface level matching such as overlapping skillsets, experiences etc. A more sophisticated approach could be doing vector embeddings and do similarities across resumes and job postings.

- **Feedback Loop**: We need to be integrated with the recruiting team. From feedback of what properties they look at resumes the most, as well as help label resumes that they think are not a good match. We can use this as feedback to go back to prompt engineering to see if we're extracting the wrong data.

---
