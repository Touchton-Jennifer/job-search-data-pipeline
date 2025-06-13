import pandas as pd

# Load the data
df = pd.read_csv('processed_data/POWERBI_WITH_METRICS_20250613_1043.csv')

# Find the "Us" company records
us_records = df[df['company_name'] == 'Us']

print(f"🔍 'US' COMPANY ANALYSIS - Found {len(us_records)} records")
print("\nLet's see what got classified as company 'Us':")

# Look at patterns
print(f"\nSender domains:")
print(us_records['sender_domain'].value_counts().head(10))

print(f"\nSubject line patterns:")
for i, row in us_records.head(10).iterrows():
    print(f"• {row['subject_line'][:80]}...")

print(f"\nSender email patterns:")
print(us_records['sender_email'].value_counts().head(10))

print(f"\nBody preview samples:")
for i, row in us_records.head(5).iterrows():
    print(f"• {row['body_preview'][:100]}...")

print(f"\nDate range:")
us_with_dates = us_records[us_records['email_date'].notna()]
if len(us_with_dates) > 0:
    print(f"From: {us_with_dates['email_date'].min()}")
    print(f"To: {us_with_dates['email_date'].max()}")