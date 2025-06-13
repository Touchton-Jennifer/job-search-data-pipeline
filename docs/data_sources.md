# Data Sources & Input Specifications

**Comprehensive guide to data inputs, formats, and requirements for replicating the job search data pipeline.**

*Note: Current implementation focuses on Gmail exports. Other email platforms have not yet been tested.*

## 📊 Primary Data Source: Gmail Export

### Overview
**Status:** ✅ Fully Implemented and Tested  
**Source:** Google Takeout  
**Format:** .mbox files  
**Tested Volume:** 1,911 emails processed successfully  
**Processing Time:** <1 minute extraction + 2-3 minutes cleanup

### Export Process - Step by Step

#### 1. Access Google Takeout
- Navigate to [takeout.google.com](https://takeout.google.com)
- Sign in with your Gmail account
- You'll see a list of Google services available for export

#### 2. Select Mail Data
- Click **"Deselect all"** to clear default selections
- Find and select **"Mail"** checkbox
- Click **"All Mail data included"** to modify selection
- Choose **"Select labels"** instead of all mail

#### 3. Configure Export Settings
- **Uncheck "Include all messages"**
- **Check only your job search label** (e.g., "applications", "job-search", "career")
- **Recommended:** Create a dedicated Gmail label before export for better organization
  - *[Notion guide for Gmail label management coming soon]*

#### 4. Set Export Parameters
- **File type:** .zip (recommended over .tgz)
- **File size:** 2GB (optimal for processing)
- **Delivery method:** "Add to Drive" (recommended for reliability)

#### 5. Complete Export
- Click **"Next step"** → **"Create export"**
- Export processing time: 2-6 hours for typical job search volumes
- You'll receive email notification when ready

### Technical Specifications

#### File Format Details
```
Format: .mbox (RFC 4155 standard mailbox format)
Encoding: UTF-8
Structure: 
  ├── Headers: From, To, Subject, Date, Message-ID
  ├── Body: Plain text and HTML variants
  └── Attachments: Present but not processed by current pipeline

Expected File Structure:
├── takeout-[timestamp].zip
└── Takeout/
    └── Mail/
        └── [label-name].mbox
```

#### Data Volume Expectations
| Job Search Duration | Typical Email Count | Expected File Size | Processing Time |
|---------------------|--------------------|--------------------|-----------------|
| 3-6 months | 500-1,000 emails | 100-300 MB | <2 minutes |
| 6-12 months | 1,000-2,000 emails | 300-600 MB | 2-4 minutes |
| 12+ months | 2,000+ emails | 600MB+ | 4-6 minutes |

### Data Quality Characteristics

#### What Gmail Export Includes ✅
- **Complete email headers** (sender, date, subject)
- **Full message content** (text and HTML)
- **Thread relationships** (via Message-ID and References headers)
- **Timestamp accuracy** (precise send/receive times)
- **Attachment indicators** (presence detected, content not extracted)

#### What Gmail Export Lacks ❌
- **In-person interactions** (coffee chats, networking events, career fairs)
- **Phone call records** (screening calls, interviews not scheduled via email)
- **Text message communications** (SMS with recruiters)
- **Social media interactions** (LinkedIn messages, Twitter DMs)
- **Manual status updates** (verbal offers, in-person rejections)

### Known Data Quality Challenges

#### HTML Artifacts
- **Issue:** Email content may include HTML formatting artifacts
- **Impact:** Company names like "Vonage Logo Hi Jennifer" instead of "Vonage"
- **Solution:** Comprehensive cleanup pipeline handles these systematically

#### Platform Confusion
- **Issue:** ATS platforms (Greenhouse, Workday) create domain extraction challenges
- **Impact:** "Us" instead of real company names from us.greenhouse-mail.io
- **Solution:** Platform-specific extraction logic implemented

#### Thread Detection
- **Issue:** Related emails may be counted as separate opportunities
- **Impact:** Inflated interview counts (572 vs. actual ~15)
- **Solution:** Thread consolidation logic groups conversations

---

## 🔄 Future Data Sources (Planned)

### Manual Tracking Overlay
**Status:** 📋 Planned for Version 2.0  
**Purpose:** Capture non-email interactions and status updates

#### Proposed Manual Data Schema
```csv
opportunity_id,company_name,role_title,interaction_type,interaction_date,status_update,notes,source,contact_name,contact_title,next_action,priority_override
```

#### Manual Interaction Types
| Type | Description | When to Use |
|------|-------------|-------------|
| `phone_screen` | Initial phone interview | Recruiter or hiring manager call |
| `video_interview` | Virtual interview session | Zoom, Teams, WebEx meetings |
| `in_person_interview` | Face-to-face interview | On-site visits, coffee meetings |
| `networking_event` | Career fair, meetup, conference | Industry events, job fairs |
| `verbal_offer` | Offer communicated verbally | Phone calls, in-person conversations |
| `verbal_rejection` | Rejection communicated verbally | Phone calls, in-person feedback |
| `status_correction` | Manual status override | Correcting algorithm errors |
| `follow_up_call` | Proactive follow-up contact | Phone calls, personal outreach |

### LinkedIn Data Integration
**Status:** 🔮 Future Enhancement  
**Challenges:** LinkedIn data export limitations, API restrictions

#### Potential LinkedIn Data Points
- **Connection history** with recruiters and hiring managers
- **InMail conversations** not captured in email
- **Job application tracking** through LinkedIn's platform
- **Company research activity** (profile views, company follows)
- **Network relationship mapping** (mutual connections, referral paths)

### Calendar Integration
**Status:** 🔮 Future Enhancement  
**Purpose:** Interview scheduling and networking event tracking

#### Calendar Data Applications
- **Interview scheduling patterns** (optimal times, duration analysis)
- **Preparation time tracking** (time blocked before interviews)
- **Follow-up scheduling** (systematic post-interview outreach)
- **Networking event attendance** (ROI analysis for different events)

---

## ⚠️ Current Limitations & Requirements

### Platform Restrictions
- **Gmail Only:** Current pipeline tested exclusively with Gmail exports
- **English Content:** Text processing assumes English-language emails
- **Label Organization:** Requires pre-organized Gmail labels for optimal results
- **.mbox Format:** Other export formats (.pst, .eml) not currently supported

### Email Platform Variations (Untested)
| Platform | Export Format | Potential Challenges |
|----------|---------------|---------------------|
| **Outlook** | .pst files | Different metadata structure |
| **Yahoo Mail** | Various formats | Limited export capabilities |
| **Apple Mail** | .mbox support | Potentially compatible |
| **Thunderbird** | .mbox native | Likely compatible |

### Data Privacy Considerations
- **Personal Information:** Pipeline processes personal communications
- **Company Confidentiality:** Email content may include confidential information
- **Contact Details:** Recruiter and hiring manager contact information included
- **Salary Information:** Compensation discussions captured in processing

### Technical Requirements
- **Python 3.11+** with required libraries (pandas, spacy, nltk)
- **RAM:** Minimum 4GB for processing large email volumes
- **Storage:** 2-3x email file size for temporary processing files
- **Processing Time:** Allow 5-10 minutes for complete pipeline execution

---

## 🛠️ Replication Guide for Other Platforms

### For Job Seekers Using Different Email Providers

#### Outlook Users
1. **Export to .pst:** File → Open & Export → Import/Export → Export to PST
2. **Convert to .mbox:** Use tools like Aid4Mail or similar converters
3. **Test compatibility:** Current pipeline may require modification

#### Apple Mail Users
1. **Export mailboxes:** Mailbox → Export Mailbox
2. **Format verification:** Apple Mail exports in .mbox format
3. **Compatibility testing:** Should work with current pipeline

#### Yahoo Mail Users
1. **Limited export options:** Yahoo provides limited bulk export
2. **Forward to Gmail:** Consider forwarding job search emails to Gmail account
3. **Manual extraction:** May require custom solutions

### Adaptation Strategy
1. **Start with current Gmail pipeline** to understand methodology
2. **Identify platform-specific challenges** in your email format
3. **Modify extraction patterns** for your platform's unique characteristics
4. **Test iteratively** with small data samples before full processing
5. **Document modifications** for community sharing

---

## 📋 Data Preparation Best Practices

### Pre-Export Organization
- **Create dedicated labels** for job search emails before export
- **Clean up irrelevant emails** to improve processing efficiency
- **Organize by time period** if managing very large volumes
- **Document your labeling system** for consistent future exports

### Quality Optimization Tips
- **Use descriptive Gmail labels:** "job-applications", "recruiter-outreach", "interviews"
- **Maintain consistent email habits:** Keep job search emails in dedicated folders
- **Regular cleanup:** Archive or delete irrelevant emails before export
- **Backup original exports:** Preserve original .mbox files before processing

### Processing Preparation
- **Verify file integrity:** Check that .mbox files open correctly
- **Note email volume:** Estimate processing time based on volume
- **Prepare workspace:** Ensure adequate storage and processing power
- **Plan for iteration:** Expect multiple cleanup passes for optimal results

---

**This data source specification enables replication of the methodology while being honest about current limitations and untested platforms.**

*Data Sources Guide | Developed through AI collaboration | Last Updated: June 2025*