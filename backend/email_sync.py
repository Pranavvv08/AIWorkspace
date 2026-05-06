import imaplib
import email
from email.header import decode_header
import os
import json
from openai import AsyncOpenAI
import traceback

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# IMAP settings
IMAP_SERVER = "imap.gmail.com"

def get_text_from_email(msg):
    text = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            try:
                body = part.get_payload(decode=True)
                if body and content_type == "text/plain" and "attachment" not in content_disposition:
                    text += body.decode(errors='replace')
            except Exception:
                pass
    else:
        content_type = msg.get_content_type()
        try:
            body = msg.get_payload(decode=True)
            if body and content_type == "text/plain":
                text = body.decode(errors='replace')
        except Exception:
            pass
    return text

async def fetch_and_process_emails():
    email_user = os.getenv("EMAIL_ADDRESS")
    email_pass = os.getenv("EMAIL_APP_PASSWORD")
    
    if not email_user or not email_pass:
        print("Email credentials not set. Skipping sync.")
        return []

    try:
        # Connect to server
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(email_user, email_pass)
        mail.select("inbox")

        # Search for unread emails
        status, messages = mail.search(None, "UNSEEN")
        if status != "OK":
            return []
            
        email_ids = messages[0].split()
        if not email_ids:
            return []
            
        all_tasks = []
        
        # Limit to processing maximum of 10 recent unread emails to avoid timeout/cost
        for e_id in email_ids[-10:]:
            res, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Get Subject
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8", errors="replace")
                        
                    # Get From
                    sender = msg.get("From")
                    
                    print(f"Analyzing Unread Email -> Subject: {subject} | From: {sender}")
                    
                    # Get Body
                    body = get_text_from_email(msg)
                    
                    # Minimal body length to save tokens
                    body = body[:2000] if body else ""
                    
                    if not subject and not body:
                        continue
                        
                    # Send to OpenAI for task extraction
                    prompt = f"""
                    You are an intelligent email assistant. Read the following email and extract any actionable tasks, important notifications, or meeting invites (especially Google Meet or Zoom).
                    
                    Sender: {sender}
                    Subject: {subject}
                    Body: {body}
                    
                    Rules:
                    1. If there is a meeting, create a task like "Attend Meeting: [Topic] with [Sender]". Priority: High.
                    2. If there is an action item, create a task describing it.
                    3. If the email is just an ad, newsletter, or not actionable, return an empty array [].
                    4. ALWAYS return a raw JSON array. DO NOT include markdown formatting like ```json.
                    
                    Example Output:
                    [
                        {{"title": "Review project proposal from Alice", "priority": "High"}},
                        {{"title": "Attend Google Meet: Q3 Planning", "priority": "Medium"}}
                    ]
                    """
                    
                    completion = await client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0
                    )
                    
                    ai_text = completion.choices[0].message.content.strip()
                    if ai_text.startswith("```json"):
                        ai_text = ai_text[7:-3]
                    elif ai_text.startswith("```"):
                        ai_text = ai_text[3:-3]
                        
                    try:
                        tasks = json.loads(ai_text)
                        if isinstance(tasks, list):
                            all_tasks.extend(tasks)
                    except json.JSONDecodeError:
                        pass
                        
        mail.close()
        mail.logout()
        return all_tasks
    except Exception as e:
        print(f"Failed to sync emails: {e}")
        traceback.print_exc()
        raise e
