# Data Schema & Field Definitions

**Comprehensive field definitions, data types, and business rules for the job search data pipeline.**

*Note: This schema was developed collaboratively with Claude AI, demonstrating modern AI-assisted data architecture design.*

## 📋 Core Data Schema

### Email Source Fields

| Field Name | Data Type | Description | Example | Business Rules |
|------------|-----------|-------------|---------|----------------|
| `email_id` | String | Unique identifier for each email | `email_00001` | Auto-generated, 5-digit zero-padded |
| `subject_line` | String | Email subject as received | `"Thank you for applying to Salesforce"` | Decoded from email headers |
| `sender_email` | String | Full sender email address | `recruiting@salesforce.com` | Validated email format |
| `sender_domain` | String | Domain portion of sender email | `salesforce.com` | Extracted from sender_email |
| `email_date` | DateTime | Timestamp when email was sent | `2025-06-13 14:30:25` | ISO format, timezone normalized |
| `body_preview` | String | First 200 characters of email body | `"Hi Jennifer, Thank you for your..."` | Text only, HTML stripped |
| `body_length` | Integer | Total character count of email body | `1250` | Used for email complexity analysis |

### Company & Role Classification

| Field Name | Data Type | Description | Example | Business Rules |
|------------|-----------|-------------|---------|----------------|
| `company_name` | String | Extracted company name | `"Salesforce"` | Title case, artifacts removed |
| `company_confidence` | Integer | Confidence in company extraction (0-100) | `85` | Algorithm-generated, manual override possible |
| `role_title` | String | Job role/position title | `"Senior Business Analyst"` | Title case, standardized format |
| `role_confidence` | Integer | Confidence in role extraction (0-100) | `90` | Algorithm-generated, manual override possible |

### Application Status & Classification

| Field Name | Data Type | Description | Example | Business Rules |
|------------|-----------|-------------|---------|----------------|
| `status` | Enum | Current application status | `"interview_scheduled"` | See Status Values below |
| `status_confidence` | Integer | Confidence in status classification (0-100) | `95` | Algorithm-generated, manual override possible |
| `pipeline_status` | Enum | Pipeline health classification | `"hot"` | See Pipeline Status Values below |
| `opportunity_type` | Enum | Type of interaction | `"recruiter_outreach"` | See Opportunity Types below |

### Thread & Communication Analysis

| Field Name | Data Type | Description | Example | Business Rules |
|------------|-----------|-------------|---------|----------------|
| `thread_id` | String | Unique identifier for email thread | `thread_001` | Groups related emails |
| `thread_email_count` | Integer | Number of emails in thread | `3` | Indicates engagement level |
| `thread_emails` | String | Summary of thread timeline | `"2025-06-01: Application received; 2025-06-03: Interview scheduled"` | Semicolon-separated chronological list |
| `first_email_date` | DateTime | Earliest email in thread | `2025-06-01 09:15:00` | Used for timeline analysis |
| `last_email_date` | DateTime | Most recent email in thread | `2025-06-03 16:45:00` | Used for recency calculations |

### Business Intelligence Metrics

| Field Name | Data Type | Description | Example | Business Rules |
|------------|-----------|-------------|---------|----------------|
| `days_since_contact` | Integer | Days since last email | `12` | Calculated from current date |
| `priority_score` | Integer | Priority ranking (0-100) | `78` | Weighted algorithm, see Priority Scoring below |
| `priority_level` | Enum | Priority classification | `"High"` | Derived from priority_score |
| `recommended_action` | String | Suggested next step | `"Send polite follow-up"` | Business logic recommendation |
| `response_type` | Enum | Communication pattern | `"multi_exchange"` | See Response Types below |

### Data Quality & Metadata

| Field Name | Data Type | Description | Example | Business Rules |
|------------|-----------|-------------|---------|----------------|
| `extraction_date` | DateTime | When record was processed | `2025-06-13 11:45:30` | Processing timestamp |
| `requires_review` | Boolean | Flagged for manual review | `false` | Based on confidence scores |
| `review_flags` | String | Reasons for manual review | `"Low company confidence; Unclear status"` | Semicolon-separated list |

### Compensation & Location Data

| Field Name | Data Type | Description | Example | Business Rules |
|------------|-----------|-------------|---------|----------------|
| `salary_info` | String | Extracted salary information | `"$80,000-$95,000"` | Normalized format when possible |
| `salary_confidence` | Integer | Confidence in salary extraction (0-100) | `70` | Algorithm-generated |
| `location_type` | Enum | Work arrangement type | `"remote"` | See Location Types below |
| `location_confidence` | Integer | Confidence in location extraction (0-100) | `80` | Algorithm-generated |

## 📚 Enumerated Values

### Status Values
| Value | Description | Typical Triggers |
|-------|-------------|------------------|
| `applied` | Application submitted | "Thank you for applying", "Application received" |
| `interview_scheduled` | Interview confirmed | "Your interview", "Interview scheduled" |
| `interviewed` | Interview completed | Manual entry typically |
| `follow_up` | General follow-up communication | "Update on your application", "Checking in" |
| `rejected` | Application declined | "Unfortunately", "Not moving forward" |
| `offer` | Job offer received | "Pleased to extend", "Offer of employment" |
| `withdrawn` | Candidate withdrew | Manual entry typically |
| `on_hold` | Process paused | "On hold", "Temporarily suspended" |
| `unknown` | Status unclear | Low confidence classification |

### Pipeline Status Values
| Value | Description | Time Since Contact | Action Required |
|-------|-------------|-------------------|-----------------|
| `hot` | Very recent activity | ≤ 7 days | Monitor, prepare |
| `warm` | Recent activity | 8-14 days | Monitor |
| `cooling` | Moderate delay | 15-21 days | Consider follow-up |
| `cold` | Significant delay | 22-30 days | Send follow-up |
| `ghosted` | Extended silence | > 30 days | Final attempt or archive |
| `closed` | Completed process | N/A | No action needed |
| `unknown_timeline` | No date information | N/A | Review manually |
| `unknown_status` | Status unclear | N/A | Review manually |

### Opportunity Types
| Value | Description | Typical Source |
|-------|-------------|----------------|
| `direct_application` | Applied directly to company | Company website, job posting |
| `recruiter_outreach` | Recruiter contacted candidate | LinkedIn, recruiting firm |
| `interview_process` | Interview-related communication | Scheduling, feedback, next steps |
| `follow_up` | Follow-up communication | Updates, checking in |
| `networking` | Networking or referral-based | Coffee chats, referrals |
| `other` | Unclassified interaction | Miscellaneous |

### Priority Levels
| Value | Score Range | Description | Typical Actions |
|-------|-------------|-------------|-----------------|
| `Critical` | 80-100 | Immediate attention required | Interview prep, urgent follow-up |
| `High` | 65-79 | High priority follow-up | Active monitoring, follow-up |
| `Medium` | 50-64 | Standard priority | Regular monitoring |
| `Low` | 35-49 | Low priority | Periodic check |
| `Inactive` | 0-34 | Minimal activity | Archive consideration |

### Response Types
| Value | Description | Engagement Level |
|-------|-------------|------------------|
| `multi_exchange` | Multiple back-and-forth emails | High engagement |
| `responded` | Company responded to application | Medium engagement |
| `responded_negative` | Company responded with rejection | Closure achieved |
| `no_response` | No response received | Low/no engagement |

### Location Types
| Value | Description | Work Arrangement |
|-------|-------------|------------------|
| `remote` | Fully remote work | Work from anywhere |
| `hybrid` | Mix of remote and office | Flexible arrangement |
| `onsite` | Full-time office presence | Traditional office work |

## 🎯 Priority Scoring Algorithm

### Scoring Components
| Component | Weight | Score Range | Description |
|-----------|--------|-------------|-------------|
| **Status Impact** | 40% | -50 to +50 | Interview scheduled = +40, Rejected = -50 |
| **Recency** | 25% | -20 to +20 | Recent activity = +20, Old activity = -20 |
| **Confidence** | 15% | -10 to +15 | High confidence = +15, Low confidence = -10 |
| **Engagement** | 10% | 0 to +15 | Multiple emails = +15, Single email = +5 |
| **Data Quality** | 10% | 0 to +10 | Clean data = +10, Missing data = 0 |

### Calculation Formula
```
Priority Score = Base Score (50) + Status Impact + Recency + Confidence + Engagement + Data Quality
Bounded between 0 and 100
```

## 🔍 Data Quality Standards

### Confidence Score Thresholds
| Confidence Level | Score Range | Action Required |
|------------------|-------------|-----------------|
| High Confidence | 80-100 | Use as-is |
| Medium Confidence | 60-79 | Monitor for accuracy |
| Low Confidence | 40-59 | Flag for review |
| Very Low Confidence | 0-39 | Require manual validation |

### Review Flag Triggers
- Company confidence < 60
- Role confidence < 60  
- Status confidence < 60
- Missing critical fields (company_name, email_date)
- Suspicious patterns (HTML artifacts, user name as company)

## 🔄 Data Lineage & Processing History

### AI-Assisted Development Notes
This schema was developed through iterative collaboration with Claude AI, demonstrating:
- **Rapid prototyping** of data structures
- **Business logic validation** through real-world testing
- **Quality improvement** through systematic iteration
- **Documentation standards** for knowledge transfer

### Processing History Tracking
Each record maintains:
- **Original extraction timestamp**
- **Cleanup version applied** (comprehensive_cleanup1.py)
- **Manual override indicators**
- **Confidence score evolution**

### Audit Trail
- All major field changes logged
- Algorithm improvements tracked via version control
- Manual corrections documented
- Data quality metrics preserved across iterations

## ⚠️ Current Limitations

### Platform-Specific Considerations
- **Gmail format:** Schema optimized for Gmail .mbox structure
- **English language:** Text processing assumes English email content
- **Date formats:** Various email date formats normalized to ISO standard
- **Time zones:** Converted to local timezone for consistency

### Future Schema Enhancements
- **Multi-language support** for international job searches
- **Additional email platforms** (Outlook, Yahoo, etc.)
- **Enhanced metadata** for tracking manual interventions
- **Integration fields** for external data sources (LinkedIn, Calendar)

---

**This schema ensures consistent, high-quality data across all processing stages while maintaining transparency and auditability of the AI-assisted development process.**

*Schema Version: 1.0 | Developed with Claude AI | Last Updated: June 2025*