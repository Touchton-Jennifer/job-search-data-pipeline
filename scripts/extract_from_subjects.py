import pandas as pd
import re
import spacy
from datetime import datetime

print("🎯 Starting targeted subject extraction and artifact removal...")
print(f"Started at: {datetime.now()}")

# Load spaCy
try:
    nlp = spacy.load("en_core_web_sm")
    print("✅ spaCy language model loaded")
except:
    print("❌ spaCy model not found")
    nlp = None

def is_obviously_wrong_company(company_name):
    """Identify companies that are clearly extraction artifacts"""
    if pd.isna(company_name) or not company_name:
        return True
    
    company_lower = str(company_name).lower().strip()
    
    # Obviously wrong "companies"
    wrong_companies = [
        'jennifer touchton', 'jennifer', 'touchton',  # User's own name
        'email', 'emails', 'gmail', 'outlook', 'yahoo',  # Email platforms
        'noreply', 'no-reply', 'donotreply', 'do-not-reply',  # Email artifacts
        'candidates', 'candidate', 'applicant', 'applicants',  # Generic terms
        'dear', 'hello', 'hi', 'thanks', 'thank', 'notification',  # Greetings
        'team', 'recruiting', 'talent', 'hr', 'human resources',  # Generic roles
        'divthank', 'div', 'span', 'img', 'src',  # HTML artifacts
        'schemas-microsoft-com', 'xmlns', 'http', 'www',  # XML/HTML
        'tion powered by icims, the', 'powered by', 'icims',  # ATS artifacts
        'application', 'apply', 'job', 'position', 'role',  # Job terms
        'update', 'reminder', 'confirmation', 'receipt'  # Email types
    ]
    
    # Check for exact matches or if the company name is mostly one of these terms
    for wrong in wrong_companies:
        if (company_lower == wrong or 
            wrong in company_lower and len(wrong) > len(company_lower) * 0.6):
            return True
    
    # Check for patterns that indicate artifacts
    artifact_patterns = [
        r'^(re|fw|fwd):\s*',  # Email prefixes
        r'^\d+$',  # Just numbers
        r'^[^a-zA-Z]*$',  # No letters
        r'^\s*$',  # Just whitespace
    ]
    
    for pattern in artifact_patterns:
        if re.search(pattern, company_lower):
            return True
    
    return False

def extract_company_from_subject_advanced(subject, body_preview=""):
    """Advanced company extraction from subjects"""
    if not subject:
        return ""
    
    subject = str(subject).strip()
    
    # Pattern 1: "Thank you for your interest in [COMPANY]"
    thank_patterns = [
        r'(?:thank you for your interest in|interest in)\s+([^,\n!\.]+?)(?:\s*[,!\.]\s*|$)',
        r'(?:thank you for applying to|applying to)\s+([^,\n!\.]+?)(?:\s*[,!\.]\s*|$)',
        r'(?:your application to|application to)\s+([^,\n!\.]+?)(?:\s*[,!\.]\s*|$)',
        r'(?:regarding your|your)\s+([A-Z][a-zA-Z\s&,\.]+?)\s+(?:employment\s+)?application',
    ]
    
    for pattern in thank_patterns:
        match = re.search(pattern, subject, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            candidate = re.sub(r'\s*(inc|llc|corp|corporation|company|co\.?)\s*$', '', candidate, flags=re.IGNORECASE)
            if validate_extracted_company(candidate):
                return candidate.title()
    
    # Pattern 2: Position at [COMPANY] format
    position_patterns = [
        r'(?:position|role|opportunity|job)\s+(?:at|with|for)\s+([A-Z][a-zA-Z\s&,\.]+?)(?:\s|$|[,\.])',
        r'([A-Z][a-zA-Z\s&,\.]+?)\s+(?:position|role|opportunity|job|interview)',
        r'(?:@|at)\s+([A-Z][a-zA-Z\s&,\.]+?)(?:\s|$|[,\.])',
    ]
    
    for pattern in position_patterns:
        match = re.search(pattern, subject, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            if validate_extracted_company(candidate):
                return candidate.title()
    
    # Pattern 3: Company - Position format
    dash_pattern = r'^([A-Z][a-zA-Z\s&,\.]+?)\s*[-–—]\s*'
    match = re.search(dash_pattern, subject)
    if match:
        candidate = match.group(1).strip()
        if validate_extracted_company(candidate):
            return candidate.title()
    
    # Pattern 4: From [COMPANY] format
    from_patterns = [
        r'(?:from|by)\s+([A-Z][a-zA-Z\s&,\.]+?)(?:\s|$|[,\.])',
        r'^([A-Z][a-zA-Z\s&,\.]+?)\s+(?:team|recruiting|talent|hiring)',
    ]
    
    for pattern in from_patterns:
        match = re.search(pattern, subject, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            if validate_extracted_company(candidate):
                return candidate.title()
    
    # Pattern 5: spaCy extraction from subject + body
    if nlp:
        text = f"{subject} {body_preview[:100]}"
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ == "ORG":
                candidate = ent.text.strip()
                if validate_extracted_company(candidate):
                    return candidate.title()
    
    return ""

def validate_extracted_company(name):
    """Validate if extracted text is a real company name"""
    if not name or len(name.strip()) < 2:
        return False
    
    name = name.strip()
    name_lower = name.lower()
    
    # Filter out common false positives
    false_positives = [
        'thank', 'thanks', 'your', 'our', 'the', 'this', 'that', 'with', 'from',
        'application', 'position', 'role', 'job', 'opportunity', 'interview',
        'team', 'hiring', 'recruiting', 'talent', 'employment', 'career',
        'dear', 'hello', 'hi', 'jennifer', 'regards', 'best', 'sincerely',
        'email', 'message', 'notification', 'update', 'reminder', 'confirmation',
        'time', 'work', 'new', 'great', 'excited', 'pleased', 'happy'
    ]
    
    if name_lower in false_positives:
        return False
    
    # Must be reasonable length
    if len(name) > 60:
        return False
    
    # Should contain letters
    if not re.search(r'[a-zA-Z]{2,}', name):
        return False
    
    # Should not be mostly punctuation
    letter_count = sum(c.isalpha() for c in name)
    if letter_count < len(name) * 0.5:
        return False
    
    return True

def fix_platform_artifacts(company_name):
    """Fix known platform-specific artifacts"""
    if pd.isna(company_name) or not company_name:
        return company_name
    
    company = str(company_name).strip()
    
    # Known fixes for platform artifacts
    fixes = {
        'schemas-microsoft-com': 'Microsoft',
        'ziprecruiter phil': 'ZipRecruiter',
        'ziprecruiter': 'ZipRecruiter',
        'applytojob': 'ApplyToJob',
        'ashbyhq': 'Ashby',
        'marriotthiring': 'Marriott',
        'pyramidci': 'Pyramid Consulting',
        'hiretalent': 'HireTalent',
        'cdi-careers': 'CDI',
        'divthank': '',  # Remove this artifact
    }
    
    company_lower = company.lower()
    for artifact, fix in fixes.items():
        if artifact in company_lower:
            return fix
    
    # Clean up common platform suffixes
    platform_suffixes = [
        r'\s+phil$',  # ZipRecruiter Phil -> ZipRecruiter
        r'\s+hiring$',  # Company Hiring -> Company
        r'\s+careers?$',  # Company Careers -> Company
        r'\s+jobs?$',  # Company Jobs -> Company
        r'\s+talent$',  # Company Talent -> Company
    ]
    
    for pattern in platform_suffixes:
        company = re.sub(pattern, '', company, flags=re.IGNORECASE)
    
    return company.title() if company else ''

# Load the dataset
print("📊 Loading dataset...")
df = pd.read_csv('processed_data/job_emails_FINAL_CLEANED_20250613_1137.csv')

print(f"Original records: {len(df)}")
print(f"Companies before cleanup: {df['company_name'].nunique()}")

# Backup original company names
df['company_before_cleanup'] = df['company_name']

# Step 1: Remove obviously wrong companies
print(f"\n🚨 Step 1: Removing obviously wrong companies...")
wrong_company_mask = df['company_name'].apply(is_obviously_wrong_company)
wrong_companies = df[wrong_company_mask]['company_name'].value_counts()

if len(wrong_companies) > 0:
    print(f"Removing {len(wrong_companies)} types of wrong companies:")
    for company, count in wrong_companies.head(10).items():
        print(f"  '{company}': {count} emails")

df.loc[wrong_company_mask, 'company_name'] = 'Unknown Company'

# Step 2: Fix platform artifacts
print(f"\n🔧 Step 2: Fixing platform artifacts...")
df['company_name'] = df['company_name'].apply(fix_platform_artifacts)

# Step 3: Extract from Unknown Company records using advanced subject parsing
print(f"\n🔍 Step 3: Advanced extraction from subjects...")
unknown_mask = df['company_name'] == 'Unknown Company'
unknown_records = df[unknown_mask]

print(f"Processing {len(unknown_records)} unknown company records...")

extracted_companies = []
for _, row in unknown_records.iterrows():
    subject = str(row.get('subject_line', ''))
    body = str(row.get('body_preview', ''))
    
    extracted = extract_company_from_subject_advanced(subject, body)
    if not extracted:
        extracted = 'Unknown Company'
    
    extracted_companies.append(extracted)

df.loc[unknown_mask, 'company_name'] = extracted_companies

# Step 4: Final cleanup pass
print(f"\n🧹 Step 4: Final cleanup pass...")
# Remove empty companies
df.loc[df['company_name'] == '', 'company_name'] = 'Unknown Company'

# Update confidence scores for newly extracted companies
newly_extracted_mask = (df['company_name'] != df['company_before_cleanup']) & (df['company_name'] != 'Unknown Company')
df.loc[newly_extracted_mask, 'company_confidence'] = 65

# Calculate results
companies_before = df['company_before_cleanup'].nunique()
companies_after = df['company_name'].nunique()
unknown_after = len(df[df['company_name'] == 'Unknown Company'])
total_extracted = len(df[newly_extracted_mask])

print(f"\n📈 CLEANUP RESULTS:")
print(f"Companies before: {companies_before}")
print(f"Companies after: {companies_after}")
print(f"Newly extracted companies: {total_extracted}")
print(f"Unknown companies remaining: {unknown_after}")

# Show examples of what was cleaned
print(f"\n🎯 EXAMPLES OF IMPROVEMENTS:")
changes = df[df['company_name'] != df['company_before_cleanup']].copy()

if len(changes) > 0:
    print("Company name changes:")
    change_examples = changes[['company_before_cleanup', 'company_name', 'subject_line']].drop_duplicates('company_name')
    
    for _, row in change_examples.head(15).iterrows():
        before = row['company_before_cleanup']
        after = row['company_name']
        subject = str(row['subject_line'])[:50]
        print(f"  '{before}' → '{after}' (from: '{subject}...')")

# Show top companies after cleanup
print(f"\n📊 TOP COMPANIES AFTER CLEANUP:")
legitimate_companies = df[df['company_name'] != 'Unknown Company']['company_name'].value_counts().head(20)
for company, count in legitimate_companies.items():
    print(f"  {company}: {count} emails")

# Analyze remaining unknowns
remaining_unknowns = df[df['company_name'] == 'Unknown Company']
if len(remaining_unknowns) > 0:
    print(f"\n🔍 REMAINING {len(remaining_unknowns)} UNKNOWN RECORDS:")
    print("Sample subjects:")
    for subject in remaining_unknowns['subject_line'].head(5):
        print(f"  '{str(subject)[:70]}...'")
    
    print("Sender domains:")
    domain_counts = remaining_unknowns['sender_domain'].value_counts().head(5)
    for domain, count in domain_counts.items():
        print(f"  {domain}: {count}")

# Remove temporary column
df = df.drop('company_before_cleanup', axis=1)

# Save final cleaned dataset
output_file = f"processed_data/job_emails_SUPER_CLEAN_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
df.to_csv(output_file, index=False)

# Create Power BI version
powerbi_clean = df[df['company_name'] != 'Unknown Company'].copy()
powerbi_file = f"processed_data/POWERBI_SUPER_CLEAN_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
powerbi_clean.to_csv(powerbi_file, index=False)

print(f"\n🎯 SUPER CLEAN DATASETS SAVED:")
print(f"Complete dataset: {output_file}")
print(f"  - Total records: {len(df)}")
print(f"  - Unique companies: {companies_after}")
print(f"  - Unknown companies: {unknown_after}")

print(f"Power BI ready: {powerbi_file}")
print(f"  - Clean records: {len(powerbi_clean)}")
print(f"  - Unique companies: {powerbi_clean['company_name'].nunique()}")

print(f"\n🏁 Super cleanup completed at: {datetime.now()}")
print(f"\n🚀 READY FOR POWER BI DASHBOARD!")