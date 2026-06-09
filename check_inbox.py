import sys, os
sys.path.insert(0, 'src')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from src.gmail_reader import _get_service

service = _get_service()
result = service.users().messages().list(userId="me", maxResults=15).execute()
messages = result.get("messages", [])
print(f"{len(messages)} mails gevonden in inbox\n")

for msg in messages:
    detail = service.users().messages().get(
        userId="me", id=msg["id"], format="metadata",
        metadataHeaders=["Subject", "From", "Date"]
    ).execute()
    headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
    print(f"Van:       {headers.get('From','?')}")
    print(f"Onderwerp: {headers.get('Subject','?')}")
    print(f"Datum:     {headers.get('Date','?')}")
    print("---")
