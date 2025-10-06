"""
Data quality validation for parsed resumes.
Identifies data quality issues and validation errors without scoring.
"""

import os
import json
from datetime import datetime
from pathlib import Path
import re

VALIDATION_DIR = "data/resumes/candidate_validation"
os.makedirs(VALIDATION_DIR, exist_ok=True)


def is_title_case(name):
    """Check if name is in proper Title Case."""
    if not name:
        return False
    # Should start with capital, no all caps words
    words = name.split()
    for word in words:
        if word.isupper() and len(word) > 1:  # All caps word (like "JOHN")
            return False
        if word and not word[0].isupper():  # Doesn't start with capital
            return False
    return True


def is_valid_date_format(date_str):
    """Check if a date string is in valid format MMM-DD-YYYY."""
    if not date_str or date_str == "Present":
        return True
    try:
        # Check for MMM-DD-YYYY format
        pattern = r'^[A-Z][a-z]{2}-\d{2}-\d{4}$'
        return bool(re.match(pattern, str(date_str)))
    except:
        return False


def is_valid_degree_format(degree):
    """Check if degree is in expected format (e.g., B.S., MBA, Ph.D.)."""
    if not degree:
        return False
    # Common valid formats: B.S., M.S., MBA, Ph.D., B.A., M.A., etc.
    valid_patterns = [
        r'^[BMD]\.[A-Z]\.$',  # B.S., M.A., D.Phil.
        r'^Ph\.D\.$',         # Ph.D.
        r'^[A-Z]{2,4}$',      # MBA, MFA, etc.
    ]
    return any(re.match(pattern, degree.strip()) for pattern in valid_patterns)


def validate_resume_data(parsed_data, summary_data):
    """
    Validate resume data quality and identify issues.

    Checks:
    - Missing critical attributes
    - Name formatting (Title Case)
    - Degree formatting
    - Date formatting
    - Data type consistency

    Args:
        parsed_data: Full parsed resume JSON
        summary_data: Summary JSON

    Returns:
        dict: Validation report with issues categorized by severity
    """
    issues = {
        "critical": [],  # Missing critical data
        "formatting": [],  # Format issues
        "warnings": []  # Minor issues
    }

    # === BASIC INFORMATION (20 points) ===
    if parsed_data.get('name'):
        score += 5
    else:
        issues.append("Missing candidate name")

    if parsed_data.get('email'):
        score += 5
    else:
        issues.append("Missing email address")

    if parsed_data.get('phone'):
        score += 5
    else:
        issues.append("Missing phone number")

    if parsed_data.get('location'):
        score += 5
    else:
        issues.append("Missing location information")

    # === EXPERIENCE QUALITY (30 points) ===
    if experiences:
        score += 10

        # Check for quantitative metrics
        has_metrics = False
        valid_dates = True
        has_detailed_bullets = True

        for exp in experiences:
            # Check for performance metrics
            if exp.get('sharpe_ratio') or exp.get('alpha') or exp.get('coverage_value'):
                has_metrics = True

            # Check date validity
            if not is_valid_date(exp.get('start_date')) or not is_valid_date(exp.get('end_date')):
                valid_dates = False

            # Check bullet point quality
            if exp.get('bullet_points'):
                try:
                    bullets = json.loads(exp['bullet_points']) if isinstance(exp['bullet_points'], str) else exp['bullet_points']
                    if bullets and any(len(b) < 50 for b in bullets):
                        has_detailed_bullets = False
                except:
                    pass

        if has_metrics:
            score += 10
        else:
            issues.append("No quantitative performance metrics (Sharpe ratio, alpha, AUM)")

        if valid_dates:
            score += 5
        else:
            issues.append("Invalid or missing experience dates")

        if has_detailed_bullets:
            score += 5
        else:
            issues.append("Experience descriptions are too brief")
    else:
        issues.append("No work experience found")

    # === EDUCATION (15 points) ===
    if education:
        score += 10

        has_degree = any(ed.get('degree') for ed in education)
        has_honors = any(ed.get('honors') for ed in education)

        if has_degree:
            score += 2
        else:
            issues.append("Missing degree information")

        if has_honors:
            score += 3
        else:
            issues.append("No honors or awards listed in education")
    else:
        issues.append("No education history found")

    # === SKILLS & CERTIFICATIONS (15 points) ===
    if skills and len(skills) >= 5:
        score += 10
    elif skills:
        score += 5
        issues.append(f"Limited skills listed ({len(skills)} skills)")
    else:
        issues.append("No skills found")

    certifications = summary_data.get('certifications', [])
    if certifications:
        score += 5
    else:
        issues.append("No professional certifications (CFA, FRM, etc.)")

    # === SPECIALIZED DATA (20 points) ===
    has_valuation_methods = False
    has_quant_tools = False
    has_client_type = False
    has_sectors = False

    for exp in experiences:
        if exp.get('valuation_methods_used'):
            try:
                methods = json.loads(exp['valuation_methods_used']) if isinstance(exp['valuation_methods_used'], str) else exp['valuation_methods_used']
                if methods:
                    has_valuation_methods = True
            except:
                pass

        if exp.get('quant_tools_used'):
            try:
                tools = json.loads(exp['quant_tools_used']) if isinstance(exp['quant_tools_used'], str) else exp['quant_tools_used']
                if tools:
                    has_quant_tools = True
            except:
                pass

        if exp.get('client_type'):
            has_client_type = True

        if exp.get('sectors'):
            try:
                sectors = json.loads(exp['sectors']) if isinstance(exp['sectors'], str) else exp['sectors']
                if sectors:
                    has_sectors = True
            except:
                pass

    if has_valuation_methods:
        score += 5
    else:
        issues.append("No valuation methods mentioned")

    if has_quant_tools:
        score += 5
    else:
        issues.append("No quantitative tools/techniques mentioned")

    if has_client_type:
        score += 5
    else:
        issues.append("Client type (buy-side/sell-side) not identified")

    if has_sectors:
        score += 5
    else:
        issues.append("Sector coverage not specified")

    # Normalize to 0-100
    quality_score = min(100, (score / max_score) * 100)

    # Calculate data completeness metrics
    data_completeness = {
        "has_name": bool(parsed_data.get('name')),
        "has_email": bool(parsed_data.get('email')),
        "has_phone": bool(parsed_data.get('phone')),
        "has_location": bool(parsed_data.get('location')),
        "num_experiences": len(experiences),
        "num_education": len(education),
        "num_skills": len(skills),
        "num_certifications": len(summary_data.get('certifications', [])),
        "has_linkedin": bool(parsed_data.get('linkedin')),
        "has_metrics": has_metrics,
        "has_valuation_methods": has_valuation_methods,
        "has_quant_tools": has_quant_tools,
    }

    return quality_score, issues, data_completeness


def save_quality_report(candidate_name, candidate_id, quality_score, issues, parsed_data, summary_data):
    """
    Save detailed quality report to JSON file.

    Args:
        candidate_name: Name of the candidate
        candidate_id: Database ID
        quality_score: Calculated quality score
        issues: List of identified issues
        parsed_data: Full parsed resume data
        summary_data: Summary data
    """
    report = {
        "candidate_name": candidate_name,
        "candidate_id": candidate_id,
        "quality_score": quality_score,
        "score_grade": get_score_grade(quality_score),
        "total_issues": len(issues),
        "issues": issues,
        "timestamp": datetime.utcnow().isoformat(),
        "data_completeness": {
            "has_name": bool(parsed_data.get('name')),
            "has_email": bool(parsed_data.get('email')),
            "has_phone": bool(parsed_data.get('phone')),
            "has_location": bool(parsed_data.get('location')),
            "num_experiences": len(parsed_data.get('experiences', [])),
            "num_education": len(parsed_data.get('education', [])),
            "num_skills": len(parsed_data.get('skills', [])),
            "num_certifications": len(parsed_data.get('certifications', [])),
            "has_linkedin": bool(parsed_data.get('linkedin')),
        },
        "summary": {
            "current_title": summary_data.get('current_title'),
            "current_company": summary_data.get('current_company'),
            "years_experience": summary_data.get('years_experience'),
            "investment_approach": summary_data.get('investment_approach'),
        }
    }

    # Save to file
    safe_filename = candidate_name.replace(' ', '_').replace('/', '_')
    output_path = os.path.join(SCORING_DIR, f"{safe_filename}_quality_report.json")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"✅ Quality report saved: {output_path}")
    return output_path


def get_score_grade(score):
    """Convert numeric score to letter grade."""
    if score >= 90:
        return "A (Excellent)"
    elif score >= 80:
        return "B (Good)"
    elif score >= 70:
        return "C (Acceptable)"
    elif score >= 60:
        return "D (Poor)"
    else:
        return "F (Inadequate)"


def update_candidate_quality_score(conn, candidate_id, quality_score):
    """Update the quality_score column for a candidate."""
    cur = conn.cursor()
    cur.execute("""
        UPDATE candidates
        SET quality_score = ?
        WHERE id = ?
    """, (quality_score, candidate_id))
    conn.commit()
