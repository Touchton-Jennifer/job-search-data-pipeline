import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

print("📊 Starting business metrics calculation...")
print(f"Started at: {datetime.now()}")

def calculate_days_between(start_date, end_date=None):
    """Calculate days between dates, handling various formats"""
    if pd.isna(start_date):
        return np.nan
    
    if end_date is None:
        end_date = datetime.now()
    
    try:
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)
        
        return (end_date - start_date).days
    except:
        return np.nan

def classify_pipeline_status(row, current_date):
    """Business rule for pipeline health classification"""
    status = row['status']
    last_contact = row.get('email_date', '')
    days_since = calculate_days_between(last_contact, current_date)
    
    if pd.isna(days_since):
        return 'unknown_timeline'
    
    # Closed statuses (no follow-up needed)
    if status in ['rejected', 'offer', 'withdrawn']:
        return 'closed'
    
    # Active pipeline rules
    if status in ['applied', 'interview_scheduled', 'follow_up']:
        if days_since <= 7:
            return 'hot'
        elif days_since <= 14:
            return 'warm'
        elif days_since <= 21:
            return 'cooling'
        elif days_since <= 30:
            return 'cold'
        else:
            return 'ghosted'
    
    # Default
    return 'unknown_status'

def calculate_priority_score(row):
    """Calculate priority score for follow-up (1-100)"""
    score = 50  # Base score
    
    # Status impact
    status_weights = {
        'interview_scheduled': 40,
        'offer': 50,
        'applied': 20,
        'follow_up': 15,
        'on_hold': -10,
        'rejected': -50,
        'unknown': 0
    }
    score += status_weights.get(row['status'], 0)
    
    # Confidence impact
    if pd.notna(row.get('status_confidence')):
        if row['status_confidence'] >= 80:
            score += 15
        elif row['status_confidence'] >= 60:
            score += 5
        else:
            score -= 10
    
    # Recency impact (based on email_date)
    days_since = calculate_days_between(row.get('email_date'))
    if pd.notna(days_since):
        if days_since <= 3:
            score += 20
        elif days_since <= 7:
            score += 10
        elif days_since <= 14:
            score += 0
        elif days_since <= 21:
            score -= 10
        else:
            score -= 20
    
    # Company known/unknown impact
    if row.get('company_name') not in ['Unknown Company', '']:
        score += 10
    
    # Role clarity impact  
    if row.get('role_title') not in ['Unknown Role', '']:
        score += 10
    
    # Thread engagement (more emails = more engagement)
    thread_count = row.get('thread_email_count', 1)
    if thread_count > 3:
        score += 15
    elif thread_count > 1:
        score += 5
    
    return max(0, min(100, score))  # Bound between 0-100

def calculate_response_metrics(row):
    """Calculate response time and patterns"""
    thread_count = row.get('thread_email_count', 1)
    
    # Basic response indicators
    if thread_count > 1:
        return 'multi_exchange'
    elif row['status'] in ['applied', 'interview_scheduled', 'offer']:
        return 'responded'
    elif row['status'] == 'rejected':
        return 'responded_negative'
    else:
        return 'no_response'

def classify_opportunity_type(row):
    """Classify the type of opportunity"""
    subject = str(row.get('subject_line', '')).lower()
    body = str(row.get('body_preview', '')).lower()
    sender = str(row.get('sender_email', '')).lower()
    
    # Direct application
    if any(word in subject for word in ['application', 'applied', 'thank you for applying']):
        return 'direct_application'
    
    # Recruiter outreach
    if any(word in sender for word in ['recruiting', 'talent', 'hr']) or \
       any(word in subject for word in ['opportunity', 'role for you', 'interested in']):
        return 'recruiter_outreach'
    
    # Interview process
    if 'interview' in subject:
        return 'interview_process'
    
    # Follow-up
    if any(word in subject for word in ['update', 'follow', 'checking', 're:']):
        return 'follow_up'
    
    # Networking
    if any(word in subject for word in ['connection', 'networking', 'coffee', 'chat']):
        return 'networking'
    
    return 'other'

def calculate_conversion_metrics(df):
    """Calculate conversion rates and funnel metrics"""
    total_applications = len(df[df['status'].isin(['applied', 'interview_scheduled', 'offer', 'rejected'])])
    interviews = len(df[df['status'] == 'interview_scheduled'])
    offers = len(df[df['status'] == 'offer'])
    
    # Application to interview rate
    interview_rate = (interviews / total_applications * 100) if total_applications > 0 else 0
    
    # Interview to offer rate  
    offer_rate = (offers / interviews * 100) if interviews > 0 else 0
    
    # Overall conversion rate
    overall_rate = (offers / total_applications * 100) if total_applications > 0 else 0
    
    return {
        'total_applications': total_applications,
        'total_interviews': interviews,
        'total_offers': offers,
        'interview_rate': round(interview_rate, 1),
        'offer_rate': round(offer_rate, 1),
        'overall_conversion': round(overall_rate, 1)
    }

def calculate_activity_metrics(df):
    """Calculate activity patterns and velocity"""
    # Convert dates
    df_with_dates = df[df['email_date'].notna()].copy()
    df_with_dates['email_date_dt'] = pd.to_datetime(df_with_dates['email_date'], errors='coerce')
    df_with_dates = df_with_dates[df_with_dates['email_date_dt'].notna()]
    
    if len(df_with_dates) == 0:
        return {}
    
    # Date range
    min_date = df_with_dates['email_date_dt'].min()
    max_date = df_with_dates['email_date_dt'].max()
    total_days = (max_date - min_date).days + 1
    
    # Weekly activity
    df_with_dates['week'] = df_with_dates['email_date_dt'].dt.isocalendar().week
    weekly_activity = df_with_dates.groupby('week').size()
    
    # Monthly activity
    df_with_dates['month'] = df_with_dates['email_date_dt'].dt.to_period('M')
    monthly_activity = df_with_dates.groupby('month').size()
    
    return {
        'date_range_days': total_days,
        'avg_weekly_activity': round(weekly_activity.mean(), 1),
        'peak_weekly_activity': weekly_activity.max(),
        'avg_monthly_activity': round(monthly_activity.mean(), 1),
        'most_active_month': str(monthly_activity.idxmax()) if len(monthly_activity) > 0 else None
    }

# Load the refined dataset
print("📊 Loading refined dataset...")
df = pd.read_csv('processed_data/job_emails_REFINED_20250613_1041.csv')

current_date = datetime.now()
print(f"Analysis date: {current_date.strftime('%Y-%m-%d')}")
print(f"Total records: {len(df)}")

# Calculate business metrics
print("\n🔢 Calculating business metrics...")

# 1. Pipeline status classification
print("  - Pipeline status classification...")
df['pipeline_status'] = df.apply(lambda row: classify_pipeline_status(row, current_date), axis=1)

# 2. Days since last contact
print("  - Time-based calculations...")
df['days_since_contact'] = df.apply(lambda row: calculate_days_between(row.get('email_date')), axis=1)

# 3. Priority scoring
print("  - Priority scoring...")
df['priority_score'] = df.apply(calculate_priority_score, axis=1)

# 4. Response classification
print("  - Response patterns...")
df['response_type'] = df.apply(calculate_response_metrics, axis=1)

# 5. Opportunity classification
print("  - Opportunity classification...")
df['opportunity_type'] = df.apply(classify_opportunity_type, axis=1)

# 6. Business priority levels
print("  - Business priority levels...")
def assign_priority_level(score):
    if score >= 80:
        return 'Critical'
    elif score >= 65:
        return 'High'
    elif score >= 50:
        return 'Medium'
    elif score >= 35:
        return 'Low'
    else:
        return 'Inactive'

df['priority_level'] = df['priority_score'].apply(assign_priority_level)

# 7. Follow-up recommendations
print("  - Follow-up recommendations...")
def recommend_action(row):
    pipeline = row['pipeline_status']
    status = row['status']
    days = row['days_since_contact']
    
    if pipeline == 'closed':
        return 'No action needed'
    elif pipeline == 'ghosted':
        return 'Send follow-up or mark inactive'
    elif pipeline == 'hot' and status == 'interview_scheduled':
        return 'Prepare for interview'
    elif pipeline == 'cooling' and status in ['applied', 'follow_up']:
        return 'Send polite follow-up'
    elif pipeline == 'cold':
        return 'Final follow-up attempt'
    elif pipeline in ['warm', 'hot']:
        return 'Monitor - no action needed'
    else:
        return 'Review status'

df['recommended_action'] = df.apply(recommend_action, axis=1)

# Calculate summary metrics
print("\n📈 Calculating summary metrics...")
conversion_metrics = calculate_conversion_metrics(df)
activity_metrics = calculate_activity_metrics(df)

# Create summary statistics
summary_stats = {
    'total_records': len(df),
    'active_opportunities': len(df[df['pipeline_status'].isin(['hot', 'warm', 'cooling'])]),
    'ghosted_opportunities': len(df[df['pipeline_status'] == 'ghosted']),
    'high_priority_items': len(df[df['priority_level'].isin(['Critical', 'High'])]),
    'companies_engaged': df[df['company_name'] != 'Unknown Company']['company_name'].nunique(),
    'avg_priority_score': round(df['priority_score'].mean(), 1)
}

# Combine all metrics
all_metrics = {**summary_stats, **conversion_metrics, **activity_metrics}

# Save enhanced dataset
output_file = f"processed_data/job_emails_WITH_METRICS_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
df.to_csv(output_file, index=False)

# Create Power BI optimized version with clean metrics
powerbi_df = df[df['company_name'] != 'Unknown Company'].copy()
powerbi_metrics_file = f"processed_data/POWERBI_WITH_METRICS_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
powerbi_df.to_csv(powerbi_metrics_file, index=False)

# Display results
print(f"\n📊 BUSINESS METRICS SUMMARY:")
print(f"Total Records: {all_metrics['total_records']}")
print(f"Active Opportunities: {all_metrics['active_opportunities']}")
print(f"Ghosted Opportunities: {all_metrics['ghosted_opportunities']}")
print(f"High Priority Items: {all_metrics['high_priority_items']}")
print(f"Companies Engaged: {all_metrics['companies_engaged']}")
print(f"Average Priority Score: {all_metrics['avg_priority_score']}")

print(f"\n🎯 CONVERSION METRICS:")
print(f"Total Applications: {conversion_metrics['total_applications']}")
print(f"Interview Rate: {conversion_metrics['interview_rate']}%")
print(f"Offer Rate: {conversion_metrics['offer_rate']}%")
print(f"Overall Conversion: {conversion_metrics['overall_conversion']}%")

print(f"\n📈 PIPELINE BREAKDOWN:")
pipeline_breakdown = df['pipeline_status'].value_counts()
for status, count in pipeline_breakdown.items():
    percentage = round(count / len(df) * 100, 1)
    print(f"  {status}: {count} ({percentage}%)")

print(f"\n🚨 HIGH PRIORITY OPPORTUNITIES:")
high_priority = df[df['priority_level'].isin(['Critical', 'High'])].copy()
high_priority_sorted = high_priority.sort_values('priority_score', ascending=False)

for _, row in high_priority_sorted.head(10).iterrows():
    company = row['company_name'][:25]
    role = str(row['role_title'])[:30] if pd.notna(row['role_title']) else 'Unknown Role'
    score = int(row['priority_score'])
    action = row['recommended_action']
    print(f"  • {company} - {role} (Score: {score}) → {action}")

print(f"\n🎯 OUTPUTS:")
print(f"Complete dataset with metrics: {output_file}")
print(f"Power BI optimized dataset: {powerbi_metrics_file}")
print(f"  - Clean records: {len(powerbi_df)}")
print(f"  - Active pipeline: {len(powerbi_df[powerbi_df['pipeline_status'].isin(['hot', 'warm', 'cooling'])])}")

print(f"\n🏁 Business metrics calculation completed at: {datetime.now()}")