import os
import sys
import json
import datetime
from collections import Counter
import polars as pl
from tqdm import tqdm

# Add the parent directory to the path so we can import pipeline modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from pipeline.loader import stream_candidates
from pipeline.honeypot_detector import analyze_honeypot_signals

def run_exploration(file_path: str, limit: int = None):
    print(f"Starting exploration on {file_path} (limit: {limit or 'ALL'})...")
    
    total_candidates = 0
    honeypot_count = 0
    
    # Counters for distributions
    titles = Counter()
    companies = Counter()
    company_sizes = Counter()
    countries = Counter()
    locations = Counter()
    education_tiers = Counter()
    skill_names = Counter()
    skill_proficiency = Counter()
    
    # YOE tracking
    yoe_list = []
    
    # Redrob signals tracking
    completeness_scores = []
    recruiter_response_rates = []
    avg_response_times = []
    notice_periods = []
    github_activity_scores = []
    willing_to_relocate_count = 0
    open_to_work_count = 0
    
    # Candidate category classifications
    categories = {
        "AI/ML/Data Roles": 0,
        "General Software / Backend / Frontend": 0,
        "Engineering Management / PM": 0,
        "Non-Technical / Unrelated Roles": 0,
        "Other / Unspecified": 0
    }
    
    # Function to classify a title
    def classify_title(title: str) -> str:
        title_lower = title.lower()
        
        # AI/ML/Data roles
        ai_ml_keywords = ["machine learning", "ml", "ai ", "artificial intelligence", "data scientist", 
                           "data science", "nlp", "computer vision", "deep learning", "research scientist",
                           "data engineer", "data analyst", "recommendation", "retrieval"]
        if any(kw in title_lower for kw in ai_ml_keywords) or title_lower.startswith("ai ") or title_lower.endswith(" ai"):
            return "AI/ML/Data Roles"
            
        # General Software
        se_keywords = ["software", "developer", "engineer", "programmer", "backend", "frontend", 
                       "fullstack", "full stack", "devops", "cloud", "qa", "test", "systems", "mobile", 
                       "android", "ios", "web"]
        if any(kw in title_lower for kw in se_keywords):
            return "General Software / Backend / Frontend"
            
        # Management
        mgmt_keywords = ["manager", "lead", "director", "head", "product manager", "project manager", "scrum master"]
        if any(kw in title_lower for kw in mgmt_keywords):
            return "Engineering Management / PM"
            
        # Non-Technical / Unrelated
        non_tech_keywords = ["marketing", "sales", "hr ", "recruiter", "accountant", "finance", "business development", 
                             "operations", "support", "writer", "designer", "graphic", "civil", "mechanical", 
                             "accounting", "human resources", "admin", "executive"]
        if any(kw in title_lower for kw in non_tech_keywords):
            return "Non-Technical / Unrelated Roles"
            
        return "Other / Unspecified"

    # Streaming load and process to avoid memory issues (JSONL is large)
    print("Processing candidates stream...")
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: Candidate file not found at {file_path}")
        return
        
    for cand in tqdm(stream_candidates(file_path, limit)):
        total_candidates += 1
        
        # Profile fields
        profile = cand.get("profile", {})
        yoe = profile.get("years_of_experience", 0.0)
        yoe_list.append(yoe)
        
        current_title = profile.get("current_title", "")
        if current_title:
            titles[current_title] += 1
            cat = classify_title(current_title)
            categories[cat] += 1
        else:
            categories["Other / Unspecified"] += 1
            
        current_company = profile.get("current_company", "")
        if current_company:
            companies[current_company] += 1
            
        company_size = profile.get("current_company_size", "")
        if company_size:
            company_sizes[company_size] += 1
            
        country = profile.get("country", "")
        if country:
            countries[country] += 1
            
        location = profile.get("location", "")
        if location:
            locations[location] += 1
            
        # Education tiers
        education = cand.get("education", [])
        tiers_in_edu = [edu.get("tier", "unknown") for edu in education]
        if tiers_in_edu:
            # Get the highest tier (tier_1 > tier_2 > tier_3 > tier_4 > unknown)
            tier_priority = {"tier_1": 4, "tier_2": 3, "tier_3": 2, "tier_4": 1, "unknown": 0}
            best_tier = max(tiers_in_edu, key=lambda t: tier_priority.get(t, 0))
            education_tiers[best_tier] += 1
        else:
            education_tiers["no_education_listed"] += 1
            
        # Skills
        for skill in cand.get("skills", []):
            name = skill.get("name", "")
            prof = skill.get("proficiency", "")
            if name:
                skill_names[name] += 1
            if prof:
                skill_proficiency[prof] += 1
                
        # Redrob signals
        signals = cand.get("redrob_signals", {})
        completeness_scores.append(signals.get("profile_completeness_score", 0.0))
        recruiter_response_rates.append(signals.get("recruiter_response_rate", 0.0))
        avg_response_times.append(signals.get("avg_response_time_hours", 0.0))
        notice_periods.append(signals.get("notice_period_days", 0))
        github_activity_scores.append(signals.get("github_activity_score", -1.0))
        
        if signals.get("willing_to_relocate", False):
            willing_to_relocate_count += 1
        if signals.get("open_to_work_flag", False):
            open_to_work_count += 1
            
        # Honeypot checks
        reasons, severity = analyze_honeypot_signals(cand)
        if severity >= 0.8:
            honeypot_count += 1

    # Print summary report
    print("\n" + "="*50)
    print("           FITRANK AI DATA EXPLORATION REPORT")
    print("="*50)
    print(f"Total candidates analyzed: {total_candidates}")
    print(f"Honeypot profiles detected: {honeypot_count} ({honeypot_count/total_candidates*100:.3f}%)")
    
    print("\n--- Current Title Distribution (Top 15) ---")
    for title, count in titles.most_common(15):
        print(f"  {title}: {count} ({count/total_candidates*100:.2f}%)")
        
    print("\n--- Candidate Categories ---")
    for cat, count in categories.items():
        print(f"  {cat}: {count} ({count/total_candidates*100:.2f}%)")
        
    print("\n--- Years of Experience Range ---")
    yoe_series = pl.Series("yoe", yoe_list)
    print(f"  Mean YOE: {yoe_series.mean():.2f}")
    print(f"  Median YOE: {yoe_series.median():.2f}")
    print(f"  Min/Max YOE: {yoe_series.min():.2f} / {yoe_series.max():.2f}")
    
    # YOE bins
    yoe_0_3 = sum(1 for y in yoe_list if y < 3.0)
    yoe_3_5 = sum(1 for y in yoe_list if 3.0 <= y < 5.0)
    yoe_5_9 = sum(1 for y in yoe_list if 5.0 <= y <= 9.0)
    yoe_9_12 = sum(1 for y in yoe_list if 9.0 < y <= 12.0)
    yoe_12_plus = sum(1 for y in yoe_list if y > 12.0)
    
    print(f"  < 3 years: {yoe_0_3} ({yoe_0_3/total_candidates*100:.2f}%)")
    print(f"  3 - 5 years: {yoe_3_5} ({yoe_3_5/total_candidates*100:.2f}%)")
    print(f"  5 - 9 years (JD preferred): {yoe_5_9} ({yoe_5_9/total_candidates*100:.2f}%)")
    print(f"  9 - 12 years: {yoe_9_12} ({yoe_9_12/total_candidates*100:.2f}%)")
    print(f"  12+ years: {yoe_12_plus} ({yoe_12_plus/total_candidates*100:.2f}%)")
    
    print("\n--- Education Tier Distribution ---")
    for tier, count in education_tiers.most_common():
        print(f"  {tier}: {count} ({count/total_candidates*100:.2f}%)")
        
    print("\n--- Skills Frequency (Top 15) ---")
    for skill, count in skill_names.most_common(15):
        print(f"  {skill}: {count}")
        
    print("\n--- Country Distribution ---")
    for country, count in countries.most_common(5):
        print(f"  {country}: {count} ({count/total_candidates*100:.2f}%)")
        
    print("\n--- Redrob Platform Engagement Metrics (Means) ---")
    comp_series = pl.Series("completeness", completeness_scores)
    resp_series = pl.Series("response", recruiter_response_rates)
    time_series = pl.Series("time", avg_response_times)
    notice_series = pl.Series("notice", notice_periods)
    
    gh_valid_scores = [s for s in github_activity_scores if s >= 0]
    gh_series = pl.Series("github", gh_valid_scores) if gh_valid_scores else None
    
    print(f"  Profile Completeness: {comp_series.mean():.1f}%")
    print(f"  Recruiter Response Rate: {resp_series.mean()*100:.1f}%")
    print(f"  Avg Response Time: {time_series.mean():.1f} hours")
    print(f"  Notice Period: {notice_series.mean():.1f} days")
    if gh_series is not None:
        print(f"  GitHub Activity Score (for {len(gh_valid_scores)} candidates): {gh_series.mean():.1f}")
        print(f"  Candidates with GitHub linked: {len(gh_valid_scores)} ({len(gh_valid_scores)/total_candidates*100:.1f}%)")
    else:
        print("  GitHub Activity: No candidate has GitHub linked")
    print(f"  Open to Work: {open_to_work_count} ({open_to_work_count/total_candidates*100:.1f}%)")
    print(f"  Willing to Relocate: {willing_to_relocate_count} ({willing_to_relocate_count/total_candidates*100:.1f}%)")
    print("="*50)

    # Save Markdown report
    report_path = os.path.join(os.path.dirname(__file__), "data_exploration_report.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# FitRank AI — Dataset Exploration Report\n\n")
        f.write(f"Analyzed date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total candidate profiles processed: **{total_candidates:,}**\n\n")
        
        f.write("## Honeypot Profile Analysis\n")
        f.write(f"- **Honeypot Candidates Detected:** {honeypot_count:,}\n")
        f.write(f"- **Honeypot Rate:** {honeypot_count/total_candidates*100:.4f}%\n")
        f.write("> [!WARNING]\n")
        f.write("> Honeypots are fake/impossible candidate profiles inserted to test if ranking systems rely purely on keywords. Any candidate ranking pipeline must completely exclude them from the top 100.\n\n")
        
        f.write("## Current Title Distribution (Top 20)\n")
        f.write("| Rank | Title | Count | Percentage |\n")
        f.write("| --- | --- | --- | --- |\n")
        for i, (title, count) in enumerate(titles.most_common(20)):
            f.write(f"| {i+1} | {title} | {count:,} | {count/total_candidates*100:.2f}% |\n")
        f.write("\n")
        
        f.write("## Role Category Classification\n")
        f.write("| Category | Count | Percentage |\n")
        f.write("| --- | --- | --- |\n")
        for cat, count in categories.items():
            f.write(f"| {cat} | {count:,} | {count/total_candidates*100:.2f}% |\n")
        f.write("\n")
        
        f.write("## Experience Distribution (YOE)\n")
        f.write(f"- **Mean Experience:** {yoe_series.mean():.2f} years\n")
        f.write(f"- **Median Experience:** {yoe_series.median():.2f} years\n")
        f.write(f"- **Range:** {yoe_series.min():.2f} to {yoe_series.max():.2f} years\n\n")
        
        f.write("| YOE Range | Count | Percentage |\n")
        f.write("| --- | --- | --- |\n")
        f.write(f"| < 3 years (Junior) | {yoe_0_3:,} | {yoe_0_3/total_candidates*100:.2f}% |\n")
        f.write(f"| 3 - 5 years (Mid) | {yoe_3_5:,} | {yoe_3_5/total_candidates*100:.2f}% |\n")
        f.write(f"| 5 - 9 years (Senior/JD Ideal) | {yoe_5_9:,} | {yoe_5_9/total_candidates*100:.2f}% |\n")
        f.write(f"| 9 - 12 years (Lead) | {yoe_9_12:,} | {yoe_9_12/total_candidates*100:.2f}% |\n")
        f.write(f"| 12+ years (Principal/Director) | {yoe_12_plus:,} | {yoe_12_plus/total_candidates*100:.2f}% |\n")
        f.write("\n")
        
        f.write("## Education Tier Distribution\n")
        f.write("| Tier | Count | Percentage |\n")
        f.write("| --- | --- | --- |\n")
        for tier, count in education_tiers.most_common():
            f.write(f"| {tier} | {count:,} | {count/total_candidates*100:.2f}% |\n")
        f.write("\n")
        
        f.write("## Most Common Skills (Top 30)\n")
        f.write("| Rank | Skill | Count | Percentage of Profiles |\n")
        f.write("| --- | --- | --- | --- |\n")
        for i, (skill, count) in enumerate(skill_names.most_common(30)):
            f.write(f"| {i+1} | {skill} | {count:,} | {count/total_candidates*100:.2f}% |\n")
        f.write("\n")
        
        f.write("## Country Distribution\n")
        f.write("| Country | Count | Percentage |\n")
        f.write("| --- | --- | --- |\n")
        for country, count in countries.most_common(10):
            f.write(f"| {country} | {count:,} | {count/total_candidates*100:.2f}% |\n")
        f.write("\n")
        
        f.write("## Redrob Platform Engagement Metrics\n")
        f.write(f"- **Average Profile Completeness:** {comp_series.mean():.1f}%\n")
        f.write(f"- **Average Recruiter Response Rate:** {resp_series.mean()*100:.1f}%\n")
        f.write(f"- **Average Response Time:** {time_series.mean():.1f} hours\n")
        f.write(f"- **Average Notice Period:** {notice_series.mean():.1f} days\n")
        if gh_series is not None:
            f.write(f"- **Candidates with GitHub linked:** {len(gh_valid_scores):,} ({len(gh_valid_scores)/total_candidates*100:.1f}%)\n")
            f.write(f"- **Average GitHub Activity Score (if linked):** {gh_series.mean():.1f}/100\n")
        f.write(f"- **Candidates marked Open to Work:** {open_to_work_count:,} ({open_to_work_count/total_candidates*100:.1f}%)\n")
        f.write(f"- **Candidates willing to relocate:** {willing_to_relocate_count:,} ({willing_to_relocate_count/total_candidates*100:.1f}%)\n")
        
    print(f"\nSaved markdown report to {report_path}")

if __name__ == "__main__":
    import time
    start = time.time()
    
    # Run exploration on candidates.jsonl (100K profiles)
    # Using the path inside workspace data/
    candidates_file = os.path.join(os.path.dirname(__file__), "..", "data", "candidates.jsonl")
    
    # We can pass limit=None to analyze all 100K candidates
    run_exploration(candidates_file, limit=None)
    
    print(f"\nTotal exploration time: {time.time() - start:.2f} seconds")
