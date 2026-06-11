import os
import base64
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

BASE_DIR = Path(__file__).parent.parent
CREDENTIALS_FILE = BASE_DIR / os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
TOKEN_FILE = BASE_DIR / os.getenv("GMAIL_TOKEN_FILE", "token.json")

ALERT_SENDERS = [s.strip() for s in os.getenv(
    "ALERT_SENDERS",
    "noreply@pararius.nl,no-reply@funda.nl,noreply@huurwoningen.nl"
).split(",")]


def _get_service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def haal_alert_mails_op(max_results=50):
    """Haalt recente alert-mails op van de bekende afzenders.

    Let op: filtert NIET op is:unread. Veel mailapps (telefoon-pushmeldingen)
    markeren mails al als gelezen voordat de pipeline draait, waardoor een
    is:unread-filter nieuwe woningen kan missen. In plaats daarvan kijken we
    naar de afgelopen dag en laten we de database (UNIQUE op bron+externe_id)
    de deduplicatie doen — al verwerkte listings worden dus nooit dubbel
    opgeslagen of gemeld."""
    service = _get_service()

    zoekopdracht = "(" + " OR ".join(f"from:{afzender}" for afzender in ALERT_SENDERS) + ") newer_than:1d"

    resultaat = service.users().messages().list(
        userId="me",
        q=zoekopdracht,
        maxResults=max_results
    ).execute()

    berichten = resultaat.get("messages", [])
    print(f"{len(berichten)} alert-mail(s) van de afgelopen dag gevonden.")
    return berichten


def haal_mail_inhoud_op(message_id):
    """Haalt de volledige inhoud op van een specifieke mail."""
    service = _get_service()

    bericht = service.users().messages().get(
        userId="me",
        id=message_id,
        format="full"
    ).execute()

    headers = {h["name"]: h["value"] for h in bericht["payload"]["headers"]}

    onderwerp = headers.get("Subject", "")
    afzender = headers.get("From", "")
    datum = headers.get("Date", "")

    # Haal de HTML of plain text body op
    body = _extraheer_body(bericht["payload"])

    return {
        "id": message_id,
        "onderwerp": onderwerp,
        "afzender": afzender,
        "datum": datum,
        "body": body
    }


def _extraheer_body(payload):
    """Haalt de tekstinhoud uit een Gmail payload (recursief)."""
    if "body" in payload and payload["body"].get("data"):
        data = payload["body"]["data"]
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    if "parts" in payload:
        # Geef voorkeur aan HTML, dan plain text
        for voorkeur_type in ["text/html", "text/plain"]:
            for part in payload["parts"]:
                if part.get("mimeType") == voorkeur_type:
                    if part["body"].get("data"):
                        data = part["body"]["data"]
                        return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                # Recursief door nested parts
                if "parts" in part:
                    resultaat = _extraheer_body(part)
                    if resultaat:
                        return resultaat
    return ""


def markeer_als_gelezen(message_id):
    """Markeert een mail als gelezen. Vereist gmail.modify scope.
    Als het token alleen leesrechten heeft, slaan we dit netjes over —
    de database-deduplicatie voorkomt toch al dubbele woningen."""
    try:
        service = _get_service()
        service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": ["UNREAD"]}
        ).execute()
    except Exception as e:
        print(f"   (mail niet als gelezen gemarkeerd — leesrechten only; geen probleem: {e})")


if __name__ == "__main__":
    print("Gmail verbinding testen...")
    mails = haal_alert_mails_op()
    if mails:
        print(f"\nEerste mail ophalen...")
        mail = haal_mail_inhoud_op(mails[0]["id"])
        print(f"Van: {mail['afzender']}")
        print(f"Onderwerp: {mail['onderwerp']}")
        print(f"Datum: {mail['datum']}")
        print(f"Body (eerste 200 tekens): {mail['body'][:200]}")
    else:
        print("Geen ongelezen alert-mails gevonden.")
        print("Tip: stel eerst een zoekopdracht in op Pararius of Funda!")
