import pandas as pd
import re
from difflib import SequenceMatcher

def normalize_subject(subject):
    """Normalize subject for thread matching"""
    if not subject or pd.isna(subject):
        return ""
    
    # Remove Re:, RE:, Fwd:, etc.
    subject = re.sub(r'^(re|RE|fwd|FWD|fw|FW):\s*', '', str(subject), flags=re.IGNORECASE)
    
    # Remove extra whitespace
    subject = re.sub(r'\s+', ' ', subject.strip())
    
    # Remove common variations
    subject = re.sub(r'\s*--\s*.*$', '', subject)  # Remove everything after --
    subject = re.sub(r'\s*\|\s*.*$', '', subject)  # Remove everything after |
    
    return subject.lower()

def safe_lower(text):
    """Safely convert to lowercase, handling NaN values"""
    if pd.isna(text) or text is None:
        return ""
    return str(text).lower()

def calculate_similarity(text1, text2):
    """Calculate similarity between two strings"""
    if not text1 or not text2:
        return 0.0
    return SequenceMatcher(None, text1, text2).ratio()

def group_email_threads(df):
    """Group emails into conversation threads"""
    print("🧵 Grouping email threads...")
    
    # Focus on interviews first
    interviews = df[df['status'] == 'interview_scheduled'].copy()
    
    if len(interviews) == 0:
        print("No interviews found to group")
        return df
    
    # Fill NaN values and normalize subjects for matching
    interviews['company_name'] = interviews['company_name'].fillna('Unknown')
    interviews['normalized_subject'] = interviews['subject_line'].apply(normalize_subject)
    
    print(f"Processing {len(interviews)} interview emails...")
    
    # Group by normalized subject and company
    thread_groups = {}
    thread_id = 0
    
    for idx, row in interviews.iterrows():
        subject_norm = row['normalized_subject']
        company = safe_lower(row['company_name'])
        
        # Look for existing thread
        found_thread = False
        
        for existing_thread_id, thread_info in thread_groups.items():
            # Check if this email belongs to an existing thread
            for existing_subject, existing_company in thread_info['subjects']:
                subject_sim = calculate_similarity(subject_norm, existing_subject)
                company_match = (company == existing_company)
                
                if subject_sim > 0.8 and company_match:
                    thread_groups[existing_thread_id]['emails'].append(idx)
                    thread_groups[existing_thread_id]['subjects'].append((subject_norm, company))
                    found_thread = True
                    break
            
            if found_thread:
                break
        
        # If no existing thread found, create new one
        if not found_thread:
            thread_groups[thread_id] = {
                'emails': [idx],
                'subjects': [(subject_norm, company)]
            }
            thread_id += 1
    
    print(f"Found {len(thread_groups)} interview threads")
    
    # Create consolidated interview records
    consolidated_interviews = []
    
    for thread_id, thread_info in thread_groups.items():
        email_indices = thread_info['emails']
        thread_emails = interviews.loc[email_indices]
        
        # Get the most recent email as primary
        if len(thread_emails) > 0:
            # Sort by date if available, otherwise use first
            thread_emails_with_dates = thread_emails[thread_emails['email_date'].notna()]
            
            if len(thread_emails_with_dates) > 0:
                # Convert email_date to datetime for proper sorting
                thread_emails_with_dates['email_date_dt'] = pd.to_datetime(thread_emails_with_dates['email_date'], errors='coerce')
                valid_dates = thread_emails_with_dates[thread_emails_with_dates['email_date_dt'].notna()]
                
                if len(valid_dates) > 0:
                    primary_email = valid_dates.loc[valid_dates['email_date_dt'].idxmax()]
                else:
                    primary_email = thread_emails.iloc[0]
            else:
                primary_email = thread_emails.iloc[0]
            
            # Create consolidated record
            consolidated = primary_email.copy()
            consolidated['thread_id'] = f"thread_{thread_id:03d}"
            consolidated['thread_email_count'] = len(email_indices)
            
            # Create thread summary
            thread_summary = []
            for _, row in thread_emails.iterrows():
                date_str = row['email_date'][:10] if pd.notna(row['email_date']) and len(str(row['email_date'])) >= 10 else "No date"
                subject_str = str(row['subject_line'])[:50] if pd.notna(row['subject_line']) else "No subject"
                thread_summary.append(f"{date_str}: {subject_str}")
            
            consolidated['thread_emails'] = "; ".join(thread_summary)
            
            # Use highest confidence values from thread
            consolidated['status_confidence'] = thread_emails['status_confidence'].max()
            consolidated['company_confidence'] = thread_emails['company_confidence'].max()
            consolidated['role_confidence'] = thread_emails['role_confidence'].max()
            
            # Add thread statistics
            consolidated['first_email_date'] = thread_emails['email_date'].min()
            consolidated['last_email_date'] = thread_emails['email_date'].max()
            
            consolidated_interviews.append(consolidated)
    
    # Convert back to DataFrame
    if consolidated_interviews:
        interviews_df = pd.DataFrame(consolidated_interviews)
        
        # Remove original interview records from main df
        df_no_interviews = df[df['status'] != 'interview_scheduled']
        
        # Combine with consolidated interviews
        result_df = pd.concat([df_no_interviews, interviews_df], ignore_index=True)
        
        print(f"Consolidated {len(interviews)} interview emails into {len(interviews_df)} threads")
    else:
        result_df = df
        print("No threads could be consolidated")
    
    return result_df

# Load the improved dataset
print("📊 Loading improved dataset...")
df = pd.read_csv('processed_data/job_emails_IMPROVED_20250613_1034.csv')

print(f"Original interviews: {len(df[df['status'] == 'interview_scheduled'])}")

# Group threads
df_consolidated = group_email_threads(df)

print(f"Consolidated interviews: {len(df_consolidated[df_consolidated['status'] == 'interview_scheduled'])}")

# Save consolidated dataset
output_file = f"processed_data/job_emails_CONSOLIDATED_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv"
df_consolidated.to_csv(output_file, index=False)

print(f"\n📈 CONSOLIDATED RESULTS:")
print(f"Total emails: {len(df_consolidated)}")

# Interview analysis
interviews = df_consolidated[df_consolidated['status'] == 'interview_scheduled']
high_conf_interviews = interviews[interviews['status_confidence'] >= 70]

print(f"\nConsolidated interview analysis:")
print(f"  Total interview threads: {len(interviews)}")
print(f"  High confidence threads: {len(high_conf_interviews)}")

if len(high_conf_interviews) > 0:
    print(f"\nHigh confidence interview threads:")
    for _, row in high_conf_interviews.head(15).iterrows():
        count = row.get('thread_email_count', 1)
        company = row.get('company_name', 'Unknown')[:20]
        role = str(row.get('role_title', 'Unknown'))[:30]
        print(f"  • {company} - {role} ({count} emails)")

# Show thread consolidation examples
print(f"\nThread consolidation examples:")
multi_email_threads = interviews[interviews.get('thread_email_count', 1) > 1]
for _, row in multi_email_threads.head(5).iterrows():
    count = row.get('thread_email_count', 1)
    print(f"\n{count} emails consolidated for: {row['company_name']} - {row['subject_line'][:60]}")
    if 'thread_emails' in row and pd.notna(row['thread_emails']):
        thread_details = str(row['thread_emails']).split(';')
        for detail in thread_details[:3]:  # Show first 3
            print(f"    {detail.strip()}")

print(f"\n🎯 Consolidated dataset: {output_file}")
print(f"🏁 Thread consolidation completed!")