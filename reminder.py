import requests
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("CONFLUENCE_BASE_URL")
SPACE_KEY = os.getenv("CONFLUENCE_SPACE_KEY")
API_EMAIL = os.getenv("CONFLUENCE_API_EMAIL")
API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
CC_EMAIL = os.getenv("CC_EMAIL")

def get_old_pages():
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    url = f"{BASE_URL}/rest/api/content?spaceKey={SPACE_KEY}&expand=version,history&limit=100"
    headers = {"Accept": "application/json"}

    response = requests.get(url, headers=headers, auth=(API_EMAIL, API_TOKEN))
    response.raise_for_status()
    pages = response.json().get("results", [])

    old_pages = []
    for page in pages:
        last_updated_str = page["version"]["when"]
        last_updated = datetime.strptime(last_updated_str.split(".")[0], "%Y-%m-%dT%H:%M:%S")

        if last_updated < six_months_ago:
            author_name = page["version"]["by"]["displayName"]
            name_parts = author_name.lower().split()
            if len(name_parts) >= 2:
                email = f"{name_parts[0]}{name_parts[1][0]}@pac-air.com"
                title = page["title"]
                link = BASE_URL + page["_links"]["webui"]
                old_pages.append((author_name, email, title, link))
    return old_pages

def send_email(to_email, author_name, title, link):
    msg = EmailMessage()
    msg["Subject"] = f'Review needed: "{title}" is 6+ months old'
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg["Cc"] = CC_EMAIL

    body = f"""Hi {author_name},

"[{title}]({link})" was last updated 6 months ago. 
Please take a look and see if it needs to be archived or updated. 

Thank you!
"""
    msg.set_content(body)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

def main():
    old_pages = get_old_pages()
    for author_name, author_email, title, link in old_pages:
        print(f"Sending reminder to {author_email} for page '{title}'")
        send_email(author_email, author_name, title, link)

if __name__ == "__main__":
    main()
