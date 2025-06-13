import os
import mailbox
from datetime import datetime

print("🔍 Starting email data inspection...")

# Update these paths to match your extracted files
# Look in your extracted_emails folder to find the exact paths
mbox_paths = [
    'extracted_emails/Takeout/Mail/applications.mbox',
    # If you have a second file, add it here like:
    # 'extracted_emails/Takeout/Mail/applications(1).mbox',
]

total_all_files = 0

for mbox_path in mbox_paths:
    if os.path.exists(mbox_path):
        print(f"\n📧 Analyzing: {mbox_path}")
        
        try:
            mbox = mailbox.mbox(mbox_path)
            total_emails = len(mbox)
            total_all_files += total_emails
            print(f"✅ Total emails found: {total_emails}")
            
            # Sample a few emails to understand structure
            sample_count = min(3, total_emails)
            print(f"\n📋 First {sample_count} email samples:")
            
            for i, message in enumerate(mbox):
                if i >= sample_count:
                    break
                    
                print(f"\n--- Email {i+1} ---")
                print(f"From: {message.get('From', 'Unknown')}")
                print(f"Subject: {message.get('Subject', 'No Subject')}")
                print(f"Date: {message.get('Date', 'No Date')}")
                
                # Preview first 150 chars of body
                body = ""
                if message.is_multipart():
                    for part in message.walk():
                        if part.get_content_type() == "text/plain":
                            try:
                                body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                break
                            except:
                                body = "Could not decode body"
                else:
                    try:
                        body = message.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except:
                        body = "Could not decode body"
                
                print(f"Body preview: {body[:150]}...")
                
        except Exception as e:
            print(f"❌ Error reading {mbox_path}: {e}")
            
    else:
        print(f"❌ File not found: {mbox_path}")
        print("💡 Check these common locations:")
        print("   - extracted_emails/Takeout/Mail/")
        print("   - extracted_emails/Mail/")
        print("   - Look for any folder with .mbox files")

print(f"\n🎯 SUMMARY:")
print(f"Total emails across all files: {total_all_files}")
print(f"Inspection completed at {datetime.now()}")

if total_all_files == 0:
    print("\n🔧 TROUBLESHOOTING:")
    print("1. Check that you extracted the .zip files")
    print("2. Look for .mbox files in your extracted_emails folder")
    print("3. Update the mbox_paths in this script to match your file locations")