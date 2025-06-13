import pandas as pd

# Load the super clean dataset
df = pd.read_csv('processed_data/job_emails_SUPER_CLEAN_20250613_1141.csv')

print("🔍 INVESTIGATING ODD COMPANY RECORDS")
print("=" * 50)

# Categories of odd records to investigate
odd_companies = [
    'Xmlns="Http://Www.W3.Org/1999/Xhtml',
    'Business Analyst', 
    'One', 
    'Se',
    'Careers'
]

print(f"\n1. INVESTIGATING SPECIFIC ODD COMPANIES:")
for odd_company in odd_companies:
    records = df[df['company_name'] == odd_company]
    if len(records) > 0:
        print(f"\n--- '{odd_company}' ({len(records)} emails) ---")
        for i, row in records.head(3).iterrows():  # Show first 3
            print(f"Subject: {row['subject_line']}")
            print(f"Sender: {row['sender_email']}")
            print(f"Body: {row['body_preview'][:150]}...")
            print()

print(f"\n2. INVESTIGATING UNKNOWN COMPANY RECORDS BY DOMAIN:")

unknown_records = df[df['company_name'] == 'Unknown Company']

# Group by sender domain
domains = ['myworkday.com', 'linkedin.com', 'gmail.com', 'icims.com', 'hello.tealhq.com']

for domain in domains:
    domain_records = unknown_records[unknown_records['sender_domain'] == domain]
    if len(domain_records) > 0:
        print(f"\n--- {domain} ({len(domain_records)} emails) ---")
        for i, row in domain_records.head(3).iterrows():  # Show first 3
            print(f"Subject: {row['subject_line']}")
            print(f"Sender: {row['sender_email']}")
            print(f"Body: {row['body_preview'][:150]}...")
            print()

print(f"\n3. INVESTIGATING VERY SHORT COMPANY NAMES:")
short_names = df[df['company_name'].str.len() <= 3]['company_name'].value_counts()
if len(short_names) > 0:
    print("Companies with ≤3 characters:")
    for company, count in short_names.head(10).items():
        print(f"\n--- '{company}' ({count} emails) ---")
        records = df[df['company_name'] == company]
        for i, row in records.head(2).iterrows():  # Show first 2
            print(f"Subject: {row['subject_line']}")
            print(f"Body: {row['body_preview'][:100]}...")

print(f"\n4. INVESTIGATING COMPANIES THAT LOOK LIKE JOB TITLES:")
job_title_companies = [
    'Business Analyst', 'Product Manager', 'Software Engineer', 
    'Data Analyst', 'Project Manager', 'Developer'
]

actual_job_titles = df[df['company_name'].isin(job_title_companies)]
if len(actual_job_titles) > 0:
    print("Companies that look like job titles:")
    for company in job_title_companies:
        records = df[df['company_name'] == company]
        if len(records) > 0:
            print(f"\n--- '{company}' ({len(records)} emails) ---")
            for i, row in records.head(2).iterrows():
                print(f"Subject: {row['subject_line']}")
                print(f"Body: {row['body_preview'][:120]}...")

print(f"\n5. RANDOM SAMPLE OF UNKNOWN RECORDS:")
unknown_sample = unknown_records.sample(min(5, len(unknown_records)))
for i, row in unknown_sample.iterrows():
    print(f"\nSubject: {row['subject_line']}")
    print(f"Sender: {row['sender_email']}")
    print(f"Body: {row['body_preview'][:150]}...")

print(f"\n🎯 INVESTIGATION COMPLETE!")
print(f"Total unknown companies: {len(unknown_records)}")
print(f"Total unique companies: {df['company_name'].nunique()}")