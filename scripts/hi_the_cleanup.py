import pandas as pd
import re
import spacy
from datetime import datetime

print("🧹 Starting comprehensive final cleanup...")
print(f"Started at: {datetime.now()}")

# Load spaCy for better company extraction
try:
    nlp = spacy.load("en_core_web_sm")
    print("✅ spaCy language model loaded")
except:
    print("❌ spaCy model not found - using pattern matching only")
    nlp = None

def clean_company_name_artifacts(company_name):
    """Remove common artifacts from company names"""
    if pd.isna(company_name) or not company_name:
        return ""
    
    company = str(company_name).strip()
    
    # Remove common email artifacts
    artifacts_to_remove = [
        r'\s*(logo|hi|dear|hello)\s+jennifer\s*',
        r'\s*jennifer\s*$',
        r'\s*hi\s+jennifer\s*$',
        r'\s*dear\s+jennifer\s*$',
        r'\s*logo\s*$',
        r'\s*notification\s*$',
        r'^\s*(gdpr|thank|thanks|update)\s+',
        r'\s*team\s*$',
        r'\s*recruiting\s*$',
        r'^\s*(the|a|an)\s+',
        r'\s+(inc|llc|corp|corporation|company|co)\s*$'
    ]
    
    original = company
    for pattern in artifacts_to_remove:
        company = re.sub(pattern, '', company, flags=re.IGNORECASE).strip()
    
    # If we removed too much, try a simpler approach
    if len(company) < 2:
        # Try just removing the greeting parts
        company = re.sub(r'\s*(hi|dear|hello)\s+jennifer\s*', '', original, flags=re.IGNORECASE).strip()
        company = re.sub(r'\s*jennifer\s*$', '', company, flags=re.IGNORECASE).strip()
        company = re.sub(r'\s*logo\s*$', '', company, flags=re.IGNORECASE).strip()
    
    # Capitalize properly
    if len(company) >= 2:
        # Handle acronyms (all caps 2-5 letters)
        if company.isupper() and 2 <= len(company) <= 5:
            return company.upper()
        else:
            return company.title()
    
    return ""

def extract_company_from_unknown(row):
    """Try to extract company from Unknown Company records using all available data"""
    subject = str(row.get('subject_line', ''))
    body = str(row.get('body_preview', ''))
    sender_email = str(row.get('sender_email', ''))
    sender_domain = str(row.get('sender_domain', ''))
    
    # Method 1: Email domain analysis (but smarter this time)
    if '@' in sender_email and sender_domain:
        # Known ATS platforms - extract from content instead
        ats_domains = ['greenhouse-mail.io', 'lever.co', 'workday.com', 'icims.com', 'bamboohr.com']
        
        if not any(ats in sender_domain for ats in ats_domains):
            # Regular company email - extract from domain
            domain_parts = sender_domain.lower().split('.')
            if len(domain_parts) >= 2:
                company_part = domain_parts[0]
                # Filter out generic domains
                if company_part not in ['no-reply', 'noreply', 'mail', 'email', 'info', 'contact', 'support']:
                    return company_part.title()
    
    # Method 2: Subject line patterns for unknown companies
    subject_patterns = [
        r'(?:from|at|with|@)\s+([A-Z][a-zA-Z\s&,\.]{2,30}?)(?:\s|$|[,\.])',
        r'([A-Z][a-zA-Z\s&,\.]{2,30}?)\s+(?:team|opportunity|position|role|job)',
        r'(?:application|interview|position)\s+(?:at|with|for)\s+([A-Z][a-zA-Z\s&,\.]{2,30}?)(?:\s|$)',
        r'^([A-Z][a-zA-Z\s&,\.]{2,30}?)\s+[-–—]',  # Company - Job Title format
        r'([A-Z][a-zA-Z\s&,\.]{2,30}?)\s+(?:is\s+)?(?:hiring|looking|seeking)',
    ]
    
    for pattern in subject_patterns:
        match = re.search(pattern, subject)
        if match:
            candidate = match.group(1).strip()
            if validate_company_name(candidate):
                return candidate.title()
    
    # Method 3: Body content analysis
    body_patterns = [
        r'(?:work|join|at)\s+([A-Z][a-zA-Z\s&,\.]{2,30}?)(?:\s|$|[,\.])',
        r'([A-Z][a-zA-Z\s&,\.]{2,30}?)\s+(?:is\s+)?(?:excited|pleased|happy)\s+to',
        r'(?:team\s+at|opportunity\s+at)\s+([A-Z][a-zA-Z\s&,\.]{2,30}?)(?:\s|$)',
    ]
    
    for pattern in body_patterns:
        match = re.search(pattern, body)
        if match:
            candidate = match.group(1).strip()
            if validate_company_name(candidate):
                return candidate.title()
    
    # Method 4: spaCy entity recognition
    if nlp:
        search_text = f"{subject} {body[:200]}"
        doc = nlp(search_text)
        
        for ent in doc.ents:
            if ent.label_ == "ORG":
                candidate = ent.text.strip()
                if validate_company_name(candidate):
                    return candidate.title()
    
    return "Unknown Company"

def validate_company_name(name):
    """Validate if a string looks like a real company name"""
    if not name or len(name) < 2 or len(name) > 50:
        return False
    
    # Filter out common false positives
    false_positives = [
        'thank', 'thanks', 'application', 'position', 'role', 'job', 'opportunity',
        'team', 'interview', 'hiring', 'looking', 'seeking', 'excited', 'pleased',
        'happy', 'interested', 'received', 'update', 'notification', 'jennifer',
        'your', 'our', 'the', 'this', 'that', 'with', 'from', 'dear', 'hello',
        'hi', 'email', 'message', 'sent', 'time', 'work', 'new', 'great'
    ]
    
    name_lower = name.lower().strip()
    if name_lower in false_positives:
        return False
    
    # Must contain at least one letter
    if not re.search(r'[a-zA-Z]', name):
        return False
    
    # Should not be mostly numbers or symbols
    letter_count = sum(c.isalpha() for c in name)
    if letter_count < len(name) * 0.6:  # At least 60% letters
        return False
    
    return True

def analyze_unknown_companies(df):
    """Analyze patterns in Unknown Company records"""
    unknown_records = df[df['company_name'] == 'Unknown Company'].copy()
    
    print(f"\n🔍 ANALYZING {len(unknown_records)} UNKNOWN COMPANY RECORDS:")
    
    # Sender domain analysis
    print(f"\nTop sender domains for unknowns:")
    domain_counts = unknown_records['sender_domain'].value_counts().head(10)
    for domain, count in domain_counts.items():
        print(f"  {domain}: {count}")
    
    # Subject pattern analysis
    print(f"\nSample subjects from unknowns:")
    for subject in unknown_records['subject_line'].head(10):
        print(f"  '{str(subject)[:70]}...'")
    
    return unknown_records

# Load the dataset
print("📊 Loading dataset...")
df = pd.read_csv('processed_data/job_emails_FINAL_CLEAN_20250613_1132.csv')

print(f"Original records: {len(df)}")
print(f"Companies before cleanup: {df['company_name'].nunique()}")

# Analyze unknowns before cleanup
unknown_before = len(df[df['company_name'] == 'Unknown Company'])
print(f"Unknown companies before: {unknown_before}")

if unknown_before > 0:
    analyze_unknown_companies(df)

# Step 1: Clean existing company names of artifacts
print(f"\n🧹 Step 1: Cleaning existing company name artifacts...")
df['company_name_original'] = df['company_name']  # Backup
df['company_name_cleaned'] = df['company_name'].apply(clean_company_name_artifacts)

# Step 2: Try to extract companies from Unknown Company records
print(f"\n🔍 Step 2: Extracting companies from Unknown Company records...")
unknown_mask = (df['company_name_cleaned'] == '') | (df['company_name'] == 'Unknown Company')
unknown_records = df[unknown_mask].copy()

print(f"Processing {len(unknown_records)} unknown/empty company records...")

# Extract companies for unknown records
extracted_companies = unknown_records.apply(extract_company_from_unknown, axis=1)
df.loc[unknown_mask, 'company_name_cleaned'] = extracted_companies

# Step 3: Final cleanup - use cleaned names, fall back to original if cleaning failed
df['company_name_final'] = df.apply(lambda row: 
    row['company_name_cleaned'] if row['company_name_cleaned'] and row['company_name_cleaned'] != '' 
    else row['company_name'], axis=1)

# Update the main company_name column
df['company_name'] = df['company_name_final']

# Update confidence scores
cleaned_mask = df['company_name'] != df['company_name_original']
df.loc[cleaned_mask, 'company_confidence'] = 70  # Medium confidence for cleaned names

# Calculate results
unknown_after = len(df[df['company_name'] == 'Unknown Company'])
companies_after = df['company_name'].nunique()
extracted_count = unknown_before - unknown_after

print(f"\n📈 CLEANUP RESULTS:")
print(f"Unknown companies before: {unknown_before}")
print(f"Unknown companies after: {unknown_after}")
print(f"Successfully extracted: {extracted_count}")
print(f"Total unique companies after cleanup: {companies_after}")

# Show examples of what was cleaned
print(f"\n🎯 EXAMPLES OF CLEANING:")
cleaned_examples = df[df['company_name'] != df['company_name_original']].copy()

if len(cleaned_examples) > 0:
    print("Company name improvements:")
    for _, row in cleaned_examples.head(10).iterrows():
        original = row['company_name_original']
        cleaned = row['company_name']
        if original != cleaned:
            print(f"  '{original}' → '{cleaned}'")

# Show top companies after cleanup
print(f"\n📊 TOP COMPANIES AFTER CLEANUP:")
top_companies = df[df['company_name'] != 'Unknown Company']['company_name'].value_counts().head(20)
for company, count in top_companies.items():
    print(f"  {company}: {count} emails")

# Remove temporary columns
df = df.drop(['company_name_original', 'company_name_cleaned', 'company_name_final'], axis=1)

# Save final cleaned dataset
output_file = f"processed_data/job_emails_FINAL_CLEANED_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
df.to_csv(output_file, index=False)

# Create new Power BI optimized version
powerbi_clean = df[df['company_name'] != 'Unknown Company'].copy()
powerbi_file = f"processed_data/POWERBI_FINAL_CLEANED_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
powerbi_clean.to_csv(powerbi_file, index=False)

print(f"\n🎯 FINAL CLEANED DATASETS:")
print(f"Complete dataset: {output_file}")
print(f"  - Total records: {len(df)}")
print(f"  - Unique companies: {companies_after}")
print(f"  - Unknown companies: {unknown_after}")

print(f"Power BI optimized: {powerbi_file}")
print(f"  - Clean records: {len(powerbi_clean)}")
print(f"  - Unique companies: {powerbi_clean['company_name'].nunique()}")

# Final unknown analysis
if unknown_after > 0:
    print(f"\n🔍 REMAINING UNKNOWN COMPANY ANALYSIS:")
    remaining_unknowns = df[df['company_name'] == 'Unknown Company']
    
    print(f"Sample subjects from remaining unknowns:")
    for subject in remaining_unknowns['subject_line'].head(5):
        print(f"  '{str(subject)[:70]}...'")
    
    print(f"Top sender domains for remaining unknowns:")
    domain_counts = remaining_unknowns['sender_domain'].value_counts().head(5)
    for domain, count in domain_counts.items():
        print(f"  {domain}: {count}")

print(f"\n🏁 Comprehensive cleanup completed at: {datetime.now()}")
print(f"\n💡 Ready for Power BI dashboard development!")