"""
actions/action_router.py
─────────────────────────────────────────────────────────────────────
• Slot-filling state-machine for `send_email`
• Fuzzy contact lookup using RapidFuzz
• Returns either plain-text (speak immediately) OR a dict
  {response:str, action:{...}} when more info is needed.
"""

from __future__ import annotations
import os, json, re, smtplib
from email.mime.text import MIMEText
from difflib import get_close_matches
from dotenv import load_dotenv
from rapidfuzz import process, fuzz

# ── credentials (.env) ───────────────────────────────────────────────
load_dotenv()
EMAIL        = os.getenv("EMAIL_ADDRESS")
PASSWORD     = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER  = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT    = int(os.getenv("EMAIL_SMTP_PORT", 465))

# ── contacts ----------------------------------------------------------
def load_contacts(path="contacts.json") -> dict[str, str]:
    try:
        with open(path, encoding="utf-8") as f:
            # store keys lower-cased
            return {k.lower(): v for k, v in json.load(f).items()}
    except FileNotFoundError:
        return {}

CONTACTS: dict[str, str] = load_contacts()

# ── helper functions --------------------------------------------------
STOP_WORDS = {
    "my", "the", "contact", "friend", "wife", "husband",
    "mom", "dad", "sister", "brother", "daughter", "son"
}

def _clean_token(raw: str) -> str:
    """Lower-case, remove stop-words & punctuation."""
    words = [
        w for w in re.split(r"\W+", raw.lower())
        if w and w not in STOP_WORDS
    ]
    return " ".join(words)

def normalise_email(txt: str) -> str:
    """Turn 'john at g mail dot com' → 'john@gmail.com'"""
    txt = txt.lower()
    txt = txt.replace(" at ", "@").replace(" dot ", ".").replace(" underscore ", "_")
    txt = re.sub(r"\s+", "", txt)
    return txt

def resolve_email(name_or_addr: str) -> tuple[str | None, bool]:
    """
    Returns (email, needs_confirmation)
    • Already an address  → (norm, False)
    • Exact or fuzzy match in CONTACTS
    • needs_confirmation=True when matched via fuzzy rule
    """
    token_raw = name_or_addr.strip()
    if "@" in token_raw and "." in token_raw:
        return normalise_email(token_raw), False

    token = _clean_token(token_raw)
    if not token:
        return None, False

    # 1) exact key
    if token in CONTACTS:
        return CONTACTS[token], False

    # 2) fuzzy token_sort_ratio
    match, score, _ = process.extractOne(
        token, CONTACTS.keys(), scorer=fuzz.token_sort_ratio
    ) or (None, 0, None)
    if score >= 80:
        return CONTACTS[match], True

    # 3) fuzzy partial_ratio
    match, score, _ = process.extractOne(
        token, CONTACTS.keys(), scorer=fuzz.partial_ratio
    ) or (None, 0, None)
    if score >= 80:
        return CONTACTS[match], True

    # 4) try each component word separately
    for w in token.split():
        if w in CONTACTS:
            return CONTACTS[w], True
        match, score, _ = process.extractOne(
            w, CONTACTS.keys(), scorer=fuzz.partial_ratio
        ) or (None, 0, None)
        if score >= 85:
            return CONTACTS[match], True

    return None, False

# ── MAIN dispatcher ---------------------------------------------------
def execute_action(action: dict | None):
    """
    Return:
      • str  – say directly
      • dict – still slot-filling; pass back to LLM pipeline
    """
    if not isinstance(action, dict):
        return "I didn't understand that request."

    a_type = action.get("type")
    params = action.get("parameters", {})

    # Normalize alternate key names -------------------------
    if "recipient" in params and "to" not in params:
        params["to"] = params.pop("recipient")

    if a_type == "send_email":
        return send_email(**params)

    return f"I’m not set up for the action “{a_type}”."

# ── send_email slot-filling state-machine -----------------------------
def send_email(to=None, body=None, subject=None, confirm=False, step=None, **_):
    """
    Steps:
      0) resolve name → email
      1) confirm matched address  (if fuzzy)
      2) get message body
      3) send
    """

    # 0️⃣ resolve name (first turn)
    if to and "@" not in to and step is None:
        email, needs_conf = resolve_email(to)
        if email:
            if needs_conf:
                return {
                    "response": f"Did you mean {email}?",
                    "action": { "type": "send_email",
                                "parameters": { "to": email,
                                                "step": "awaiting_recipient_confirm"} }
                }
            # straight to body
            return {
                "response": f"What message should I send to {email}?",
                "action": { "type": "send_email",
                            "parameters": { "to": email, "step": "awaiting_body"} }
            }
        return "I couldn’t find that contact. Please say or spell the address."

    # 1️⃣ awaiting yes/no confirmation
    if step == "awaiting_recipient_confirm":
        if confirm and to:
            return {
                "response": f"What message should I send to {to}?",
                "action": { "type": "send_email",
                            "parameters": { "to": to, "step": "awaiting_body"} }
            }
        return "Okay, please give me the correct e-mail address."

    # 2️⃣ ask for body (still missing)
    if to and not body:
        return {
            "response": f"What message should I send to {to}?",
            "action": { "type": "send_email",
                        "parameters": { "to": to, "step": "awaiting_body"} }
        }

    # 3️⃣ send
    if to and body:
        try:
            to_norm = normalise_email(to)
            footer = "\n Regards, \n Uttam P. \n\n--\nMessage sent through VoiceAI powered by Deepgram!"
            full_body = f"{body}{footer}"          # ← add footer here

            msg = MIMEText(full_body)
            msg["Subject"] = subject or "Voice assistant message"
            msg["From"]    = EMAIL
            msg["To"]      = to_norm

            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as srv:
                srv.login(EMAIL, PASSWORD)
                srv.send_message(msg)

            return f"I’ve sent your message to {to_norm}."
        except Exception as e:
            return f"Sorry, I couldn’t send the email. {e}"

    # Fallback
    return "I’m missing some information to send that e-mail."
