import pandas as pd

# Load the data
df = pd.read_csv('processed_data/POWERBI_WITH_METRICS_20250613_1043.csv')

# Find the "offers"
offers = df[df['status'] == 'offer']

print(f"🎁 OFFER ANALYSIS - Found {len(offers)} offers")
print("\nLet's see what got classified as offers:")

for i, row in offers.iterrows():
    print(f"\n--- Offer {i+1} ---")
    print(f"Company: {row['company_name']}")
    print(f"Subject: {row['subject_line']}")
    print(f"Confidence: {row['status_confidence']}")
    print(f"Body preview: {row['body_preview'][:150]}...")
    print(f"Date: {row['email_date']}")