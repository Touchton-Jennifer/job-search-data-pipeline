import pandas as pd
import re
import spacy
from datetime import datetime

print("🔧 Starting Greenhouse company name cleanup...")
print(f"Started at: {datetime.now()}")

# Load spaCy for better company extraction
try:
    nlp = spacy.load("en_core_web_sm")
    print("✅ spaCy language model loaded")
except:
    print("❌ spaCy model not found - using pattern matching only")
    nlp = None

def extract_company_from_greenhouse_email(subject, body_preview):
    """Extract real company name from Greenhouse application emails"""
    
    # Pattern 1: "Thank you for applying to [COMPANY]"
    patterns = [
        r'(?:thank you for applying to|application received @|applying to)\s+([^!,\n.]+?)(?:\!|$|,|\.|\.)',
        r'(?:your application to|interest in)\s+([^!,\n.]+?)(?:\!|$|,|\.|for)',
        r'(?:opportunity at|role at|position at)\s+([^!,\n.]+?)(?:\!|$|,|\.|\.)',
        r'(?:@ |at )\s*([A-Z][^!,\n.]{2,25}?)(?:\!|$|,|\.|\.)',
    ]
    
    search_text = f"{subject} {body_preview}"
    
    for pattern in patterns:
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            
            # Clean up common artifacts
            company = re.sub(r'\s+', ' ', company)  # normalize whitespace
            company = company.replace('!', '').replace('.', '').strip()
            
            # Validate length and format
            if 2 <= len(company) <= 50 and not company.lower().startswith(('the ', 'your ', 'our ')):
                return company.title()
    
    # Pattern 2: Use spaCy for organization detection
    if nlp:
        doc = nlp(search_text[:200])  # First 200 chars
        for ent in doc.ents:
            if ent.label_ == "ORG" and 2 <= len(ent.text) <= 30:
                candidate = ent.text.strip()
                # Filter out common false positives
                if candidate.lower() not in ['greenhouse', 'application', 'thank you', 'jennifer']:
                    return candidate.title()
    
    # Pattern 3: Look for capitalized words that might be company names
    words = search_text.split()
    for i, word in enumerate(words):
        if (word[0].isupper() and len(word) > 2 and 
            word.lower() not in ['thank', 'application', 'received', 'your', 'for', 'applying', 'to']):
            # Check if next word is also capitalized (might be multi-word company)
            if i + 1 < len(words) and words[i + 1][0].isupper() and len(words[i + 1]) > 2:
                return f"{word} {words[i + 1]}"
            else:
                return word
    
    return "Unknown Company"

def cleanup_greenhouse_companies(df):
    """Clean up company names for Greenhouse emails"""
    
    # Identify Greenhouse emails
    greenhouse_mask = df['sender_domain'] == 'us.greenhouse-mail.io'
    us_company_mask = df['company_name'] == 'Us'
    
    # Focus on the problematic records
    cleanup_mask = greenhouse_mask | us_company_mask
    cleanup_records = df[cleanup_mask].copy()
    
    print(f"Found {len(cleanup_records)} records to clean up")
    
    # Extract better company names
    print("Extracting company names from email content...")
    
    improved_companies = []
    for _, row in cleanup_records.iterrows():
        subject = str(row.get('subject_line', ''))
        body = str(row.get('body_preview', ''))
        
        new_company = extract_company_from_greenhouse_email(subject, body)
        improved_companies.append(new_company)
    
    # Update the dataframe
    df.loc[cleanup_mask, 'company_name'] = improved_companies
    
    # Also update confidence scores since we're more confident now
    df.loc[cleanup_mask, 'company_confidence'] = 75
    
    return df

# Load the complete dataset
print("📊 Loading complete dataset with metrics...")
df = pd.read_csv('processed_data/job_emails_WITH_METRICS_20250613_1043.csv')

print(f"Original records: {len(df)}")
original_us_count = len(df[df['company_name'] == 'Us'])
print(f"Records with company 'Us': {original_us_count}")

# Clean up the company names
df_cleaned = cleanup_greenhouse_companies(df)

# Check results
new_us_count = len(df_cleaned[df_cleaned['company_name'] == 'Us'])
unknown_count = len(df_cleaned[df_cleaned['company_name'] == 'Unknown Company'])

print(f"\n📈 CLEANUP RESULTS:")
print(f"Records with 'Us' after cleanup: {new_us_count}")
print(f"Records marked 'Unknown Company': {unknown_count}")
print(f"Successfully extracted: {original_us_count - new_us_count - unknown_count}")

# Show some examples of what was extracted
if original_us_count > new_us_count:
    print(f"\n🎯 EXAMPLES OF EXTRACTED COMPANIES:")
    
    # Find records that were cleaned up
    greenhouse_records = df_cleaned[df_cleaned['sender_domain'] == 'us.greenhouse-mail.io']
    
    # Show unique company names extracted
    extracted_companies = greenhouse_records['company_name'].value_counts()
    
    print("Top companies extracted from Greenhouse emails:")
    for company, count in extracted_companies.head(15).items():
        if company not in ['Us', 'Unknown Company']:
            print(f"  • {company}: {count} emails")

# Recalculate company statistics
print(f"\n📊 UPDATED COMPANY STATISTICS:")
total_companies = df_cleaned[df_cleaned['company_name'] != 'Unknown Company']['company_name'].nunique()
print(f"Total unique companies: {total_companies}")

# Save the cleaned complete dataset
output_file = f"processed_data/job_emails_FINAL_CLEAN_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
df_cleaned.to_csv(output_file, index=False)

# Also create a new Power BI optimized version from the cleaned data
powerbi_clean = df_cleaned[df_cleaned['company_name'] != 'Unknown Company'].copy()
powerbi_file = f"processed_data/POWERBI_FINAL_CLEAN_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
powerbi_clean.to_csv(powerbi_file, index=False)

print(f"\n🎯 CLEANED DATASETS SAVED:")
print(f"Complete dataset: {output_file}")
print(f"Power BI optimized: {powerbi_file}")
print(f"Complete records: {len(df_cleaned)}")
print(f"Power BI records: {len(powerbi_clean)}")
print(f"Unique companies: {total_companies}")

# Show before/after comparison for validation
print(f"\n🔍 BEFORE/AFTER SAMPLES:")
greenhouse_emails = df_cleaned[df_cleaned['sender_domain'] == 'us.greenhouse-mail.io']

for _, row in greenhouse_emails.head(5).iterrows():
    subject = row['subject_line'][:60]
    company = row['company_name']
    print(f"  '{subject}...' → Company: {company}")

print(f"\n🏁 Cleanup completed at: {datetime.now()}")
print(f"\n💡 Next steps:")
print(f"  - Use {output_file} for validation and spot checking")
print(f"  - Use {powerbi_file} for Power BI dashboard development")