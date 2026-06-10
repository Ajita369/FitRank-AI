import os
import sys
import csv
import json
import re
from typing import Dict, Any, List

# Add parent directory to path so we can import project modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.loader import load_candidates

def run_reasoning_audit(submission_file: str, candidates_file: str) -> None:
    if not os.path.exists(submission_file):
        print(f"Error: Submission file not found at {submission_file}")
        sys.exit(1)
        
    # 1. Load submission rows
    submission_candidates = []
    with open(submission_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            submission_candidates.append(row)
            
    print(f"Loaded {len(submission_candidates)} candidates from {submission_file}.")
    
    # 2. Extract IDs from submission to stream only relevant candidates
    submission_ids = {row["candidate_id"] for row in submission_candidates}
    
    # Load raw candidate profiles for submission candidates
    print("Loading candidate profile details from source dataset...")
    raw_candidates = {}
    with open(candidates_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            c = json.loads(line)
            cid = c.get("candidate_id")
            if cid in submission_ids:
                raw_candidates[cid] = c
                
    print(f"Loaded {len(raw_candidates)} matching candidate profiles.")
    
    # 3. Perform audits
    passed_checks = 0
    total_checks = 0
    issues = []
    
    # Check A: Character Length Limit (<= 250 characters)
    print("\nAuditing length constraints...")
    length_violations = 0
    for row in submission_candidates:
        total_checks += 1
        reason = row["reasoning"]
        if len(reason) > 250:
            length_violations += 1
            issues.append(f"Length Violation in {row['candidate_id']}: length is {len(reason)} characters (max 250)")
        else:
            passed_checks += 1
    print(f" - Length constraint pass rate: {(len(submission_candidates) - length_violations) / len(submission_candidates) * 100:.1f}% ({length_violations} violations)")
    
    # Check B: Uniqueness / Variation (non-templated)
    print("\nAuditing uniqueness and variation...")
    reasonings = [row["reasoning"] for row in submission_candidates]
    unique_reasonings = set(reasonings)
    duplicate_count = len(reasonings) - len(unique_reasonings)
    total_checks += 1
    if duplicate_count > 0:
        # Check if they are filler backups
        fillers = sum(1 for r in reasonings if "Backup filler candidate" in r)
        non_filler_duplicates = duplicate_count - max(0, fillers - 1)
        if non_filler_duplicates > 0:
            issues.append(f"Uniqueness Alert: Found {non_filler_duplicates} non-filler duplicate reasonings out of 100 rows.")
            print(f" - Uniqueness rate: {len(unique_reasonings) / len(reasonings) * 100:.1f}% ({duplicate_count} duplicates)")
        else:
            passed_checks += 1
            print(f" - Uniqueness rate: 100% (excluding backup filler entries)")
    else:
        passed_checks += 1
        print(" - Uniqueness rate: 100% (all reasonings are unique)")
        
    # Check C: Fact Consistency and Hallucination Check
    print("\nAuditing factual grounding (cross-referencing with profile)...")
    fact_errors = 0
    checked_candidates = 0
    
    for row in submission_candidates:
        cid = row["candidate_id"]
        reason = row["reasoning"]
        raw = raw_candidates.get(cid)
        if not raw:
            continue
            
        checked_candidates += 1
        profile = raw.get("profile", {})
        
        # 1. Verify Years of Experience
        yoe = profile.get("years_of_experience", 0.0)
        # Regex to find YOE in reasoning (e.g. "7.2 yrs" or "7.2 YOE")
        yoe_match = re.search(r"(\d+\.\d+|\d+)\s*(?:yrs|years)", reason, re.IGNORECASE)
        if yoe_match:
            total_checks += 1
            yoe_val = float(yoe_match.group(1))
            if abs(yoe_val - yoe) > 0.05: # allow small float differences
                fact_errors += 1
                issues.append(f"Fact Error in {cid}: reasoning says {yoe_val} years, but profile claims {yoe} YOE")
            else:
                passed_checks += 1
                
        # 2. Verify current title
        # Ensure some keywords from the current title are mentioned
        current_title = profile.get("current_title", "").lower()
        # Clean current title (remove senior/lead/staff prefixes)
        clean_title = current_title.replace("senior", "").replace("lead", "").replace("staff", "").replace("engineer", "").replace("developer", "").strip()
        # Find if title words are in reasoning
        title_words = [w for w in clean_title.split() if len(w) > 3]
        if title_words:
            total_checks += 1
            if not any(w in reason.lower() for w in title_words) and "backup filler" not in reason.lower():
                # Let's check if the current title itself is represented
                # sometimes current title is "applied scientist" and reasoning says "applied scientist"
                if not any(w in reason.lower() for w in current_title.split()):
                    fact_errors += 1
                    issues.append(f"Title Mismatch in {cid}: reasoning does not mention title keywords from '{current_title}'")
                else:
                    passed_checks += 1
            else:
                passed_checks += 1
                
        # 3. Verify Location
        location = profile.get("location", "").lower()
        loc_words = [w.strip() for w in location.split(",") if w.strip()]
        if loc_words:
            total_checks += 1
            # Check if any location word is in reasoning
            # E.g. "Noida, Uttar Pradesh" -> Noida
            if not any(w.lower() in reason.lower() for w in loc_words if len(w) > 3) and "backup filler" not in reason.lower():
                fact_errors += 1
                issues.append(f"Location Mismatch in {cid}: reasoning does not contain location keywords from '{location}'")
            else:
                passed_checks += 1
                
    print(f" - Fact grounding pass rate: {(checked_candidates * 3 - fact_errors) / (checked_candidates * 3) * 100:.1f}% ({fact_errors} issues)")
    
    # 4. Summary Report
    print("\n" + "="*80)
    print("REASONING QUALITY AUDIT SUMMARY")
    print("="*80)
    print(f"Total Programmatic Checks Run : {total_checks}")
    print(f"Total Passed Checks           : {passed_checks}")
    print(f"Overall Quality Score         : {passed_checks / max(1, total_checks) * 100:.2f}%")
    print("="*80)
    
    if issues:
        print("\nDetected Issues:")
        for issue in issues[:10]: # Print top 10 issues
            print(f"  - {issue}")
        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more issues.")
        sys.exit(1)
    else:
        print("\nSUCCESS: All candidate reasonings passed quality and fact-grounding checks!")
        sys.exit(0)

if __name__ == "__main__":
    submission_file = "output/submission.csv"
    candidates_file = "data/candidates.jsonl"
    run_reasoning_audit(submission_file, candidates_file)
