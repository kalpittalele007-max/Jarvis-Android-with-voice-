# Jarvis Android with Voice

A **Termux-first personal assistant scaffold** for Android. The project starts with local speech, phone-call hooks, notification reading, and approval-gated actions. It does not include credentials and does not silently send emails or messages.

## Current MVP

- `jarvis.py speak "hello"` uses Android text-to-speech when Termux:API is installed.
- `jarvis.py call +919876543210` requests a normal phone call through Termux:API.
- `jarvis.py notifications` reads notification previews exposed by Android.
- `jarvis.py draft-email ...` creates an approval record rather than sending mail.
- `jarvis.py approvals` lists pending approvals.
- `jarvis.py approve APPROVAL_ID` requires typing `APPROVE` before an action is marked approved.
- `data/activity.log` records local actions; `data/pending/` stores approval records.

## Install on Android

Install **Termux** and **Termux:API** from the same trusted source, then run:

```bash
pkg update
pkg install python termux-api git
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/kalpittalele007-max/Jarvis-Android-with-voice-.git
cd Jarvis-Android-with-voice-
chmod +x jarvis.py
```

Grant only the Android permissions you intend to use. Android battery optimization may need to be disabled for Termux if you want background work, but a phone-only process is not guaranteed to run continuously.

## Examples

```bash
python jarvis.py speak "Jarvis is ready"
python jarvis.py call +919876543210
python jarvis.py notifications
python jarvis.py draft-email vendor@example.com "Delivery update" "Please confirm delivery by Friday."
python jarvis.py approvals
python jarvis.py approve APPROVAL_ID
```

Set your own number locally instead of committing it:

```bash
export JARVIS_OWNER_NUMBER='+91XXXXXXXXXX'
```

## Planned integrations

The next adapters should be added separately and tested with least privilege:

1. Gmail or Outlook read/search and draft creation.
2. SMS access through Android permission.
3. WhatsApp notification-preview ingestion; reliable two-way WhatsApp requires the official Business Platform rather than private-app scraping.
4. Pune event, traffic, weather, and civic-information sources with source labels and timestamps.
5. Optional voice-provider calls for natural AI conversations. The local Termux call hook is not itself an AI voice conversation.

## Safety boundary

The assistant must never send vendor email, message another person, or make a consequential call without an explicit approval step. Never commit passwords, API keys, phone numbers, OAuth tokens, or private message content to GitHub. Use environment variables or a local untracked configuration file.
