"""
Data quality validation for parsed resumes.
Simple checks for missing data and formatting issues - no scoring.
"""

import os
import json
from datetime import datetime
import re

VALIDATION_DIR = "data/resumes/candidate_validation"
os.makedirs(VALIDATION_DIR, exist_ok=True)


def is_title_case(name):
    """Check if name is in proper Title Case."""
    if not name:
        return False
    words = name.split()
    for word in words:
        if word.isupper() and len(word) > 1:  # All caps like "JOHN"
            return False
        if word and not word[0].isupper():  # Doesn't start with capital
            return False
    return True


def is_valid_date_format(date_str):
    """Check if date is in MMM-DD-YYYY format."""
    if not date_str or date_str == "Present":
        return True
    pattern = r'^[A-Z][a-z]{2}-\d{2}-\d{4}$'
    return bool(re.match(pattern, str(date_str)))


def is_valid_degree_format(degree):
    """Check if degree follows standard format (B.S., MBA, Ph.D., etc.)."""
    if not degree:
        return False
    valid_patterns = [
        r'^[BMD]\.[A-Z]\.$',           # B.S., M.A., D.A., etc.
        r'^[BMD]\.[A-Z]\.[A-Z]\.$',    # M.B.A., M.B.B.S., B.B.A., etc.
        r'^Ph\.D\.$',                  # Ph.D.
        r'^D\.Phil\.$',                # D.Phil.
        r'^[MJ]\.D\.$',                # M.D., J.D.
        r'^[A-Z]{2,4}$',               # MBA, MFA, BBA, MBBS, etc.
    ]
    return any(re.match(pattern, degree.strip()) for pattern in valid_patterns)


def validate_resume_data(parsed_data, summary_data):
    """
    Validate resume data and identify quality issues.

    Returns dict with three severity levels:
    - critical: Missing important attributes
    - formatting: Format/consistency issues
    - warnings: Minor issues or missing optional data
    """
    issues = {
        "critical": [],
        "formatting": [],
        "warnings": []
    }

    # ===== CHECK CRITICAL ATTRIBUTES =====
    if not parsed_data.get('name'):
        issues["critical"].append("Missing candidate name")

    if not parsed_data.get('email'):
        issues["critical"].append("Missing email address")

    if not summary_data.get('name'):
        issues["critical"].append("Missing name in summary")

    if not summary_data.get('current_title'):
        issues["critical"].append("Missing current title")

    if not summary_data.get('current_company'):
        issues["critical"].append("Missing current company")

    # ===== CHECK NAME FORMATTING =====
    name = parsed_data.get('name')
    if name and not is_title_case(name):
        issues["formatting"].append(f"Name not in Title Case: '{name}'")

    summary_name = summary_data.get('name')
    if summary_name and not is_title_case(summary_name):
        issues["formatting"].append(f"Summary name not in Title Case: '{summary_name}'")

    # ===== CHECK EDUCATION FORMATTING =====
    for i, edu in enumerate(parsed_data.get('education', [])):
        degree = edu.get('degree')
        if degree and not is_valid_degree_format(degree):
            issues["formatting"].append(f"Education #{i+1}: Invalid degree format '{degree}' (expected B.S., MBA, Ph.D., etc.)")

        if not degree:
            issues["warnings"].append(f"Education #{i+1}: Missing degree")

        # Check date formats
        if edu.get('start') and not is_valid_date_format(edu.get('start')):
            issues["formatting"].append(f"Education #{i+1}: Invalid start date format '{edu.get('start')}' (expected MMM-DD-YYYY)")

        if edu.get('end') and not is_valid_date_format(edu.get('end')):
            issues["formatting"].append(f"Education #{i+1}: Invalid end date format '{edu.get('end')}' (expected MMM-DD-YYYY)")

    # ===== CHECK EXPERIENCE DATE FORMATTING =====
    for i, exp in enumerate(parsed_data.get('experiences', [])):
        if exp.get('start') and not is_valid_date_format(exp.get('start')):
            issues["formatting"].append(f"Experience #{i+1} ({exp.get('company', 'Unknown')}): Invalid start date '{exp.get('start')}'")

        if exp.get('end') and not is_valid_date_format(exp.get('end')):
            issues["formatting"].append(f"Experience #{i+1} ({exp.get('company', 'Unknown')}): Invalid end date '{exp.get('end')}'")

    # ===== CHECK NULL/MISSING DATA FOR IMPORTANT ATTRIBUTES =====
    if not parsed_data.get('phone'):
        issues["warnings"].append("Missing phone number")

    if not parsed_data.get('location'):
        issues["warnings"].append("Missing location")

    if not parsed_data.get('experiences') or len(parsed_data.get('experiences', [])) == 0:
        issues["critical"].append("No work experience found")

    if not parsed_data.get('education') or len(parsed_data.get('education', [])) == 0:
        issues["warnings"].append("No education history found")

    if not parsed_data.get('skills') or len(parsed_data.get('skills', [])) == 0:
        issues["warnings"].append("No skills listed")

    if not summary_data.get('years_experience'):
        issues["warnings"].append("Missing years of experience")

    # ===== CHECK DATA TYPE CONSISTENCY =====
    if summary_data.get('years_experience') and not isinstance(summary_data.get('years_experience'), (int, float)):
        issues["formatting"].append(f"Years of experience should be numeric, got: {type(summary_data.get('years_experience'))}")

    return issues


def save_validation_report(candidate_name, candidate_id, issues, parsed_data, summary_data):
    """
    Save validation report to JSON file.
    """
    total_issues = len(issues["critical"]) + len(issues["formatting"]) + len(issues["warnings"])

    report = {
        "candidate_name": candidate_name,
        "candidate_id": candidate_id,
        "timestamp": datetime.utcnow().isoformat(),
        "total_issues": total_issues,
        "issues_by_severity": {
            "critical": len(issues["critical"]),
            "formatting": len(issues["formatting"]),
            "warnings": len(issues["warnings"])
        },
        "issues": issues
    }

    # Save to file
    safe_filename = candidate_name.replace(' ', '_').replace('/', '_') if candidate_name else 'unknown'
    output_path = os.path.join(VALIDATION_DIR, f"{safe_filename}_validation.json")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"✅ Validation report saved: {output_path}")
    return output_path
