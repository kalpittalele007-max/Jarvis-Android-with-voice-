#!/usr/bin/env python3
"""Jarvis Termux companion: safe local controller for Android actions.

This MVP intentionally does not send email or messages automatically. It creates
approval records and requires an explicit `approve` command before a send action.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
PENDING = DATA / "pending"
LOG = DATA / "activity.log"
CONFIG = ROOT / "config.json"


def ensure_dirs() -> None:
    PENDING.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(exist_ok=True)


def log(event: str, **fields: object) -> None:
    ensure_dirs()
    record = {"time": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "event": event, **fields}
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def run_android(command: list[str], *, check: bool = False) -> str:
    """Run a Termux:API command when available; return empty text otherwise."""
    try:
        result = subprocess.run(command, text=True, capture_output=True, check=check)
        return result.stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        log("android_command_failed", command=command, error=str(exc))
        return ""


def speak(text: str) -> None:
    print(f"JARVIS: {text}")
    run_android(["termux-tts-speak", text])
    log("speak", text=text)


def call(number: str) -> None:
    if not number or not number.startswith("+"):
        raise ValueError("Use an international phone number beginning with +, e.g. +919876543210")
    print(f"Calling {number} …")
    run_android(["termux-telephony-call", number])
    log("call_requested", number=number)


def notify(title: str, content: str) -> None:
    run_android(["termux-notification", "--title", title, "--content", content, "--priority", "high"])
    log("notification", title=title, content=content)


def new_approval(kind: str, payload: dict[str, object]) -> str:
    ensure_dirs()
    approval_id = uuid.uuid4().hex[:10]
    record = {"id": approval_id, "kind": kind, "payload": payload, "status": "pending", "created": time.time()}
    (PENDING / f"{approval_id}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    log("approval_created", approval_id=approval_id, kind=kind)
    return approval_id


def list_pending() -> None:
    ensure_dirs()
    files = sorted(PENDING.glob("*.json"))
    if not files:
        print("No pending approvals.")
        return
    for file in files:
        record = json.loads(file.read_text(encoding="utf-8"))
        print(f"{record['id']}  {record['kind']}  {record['payload']}")


def approve(approval_id: str) -> None:
    path = PENDING / f"{approval_id}.json"
    if not path.exists():
        raise SystemExit(f"Approval not found: {approval_id}")
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("status") != "pending":
        raise SystemExit("This approval is no longer pending.")
    print(json.dumps(record, indent=2))
    answer = input("Type APPROVE to execute this action: ").strip()
    if answer != "APPROVE":
        print("Cancelled.")
        log("approval_cancelled", approval_id=approval_id)
        return
    record["status"] = "approved"
    record["approved"] = time.time()
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    log("approval_approved", approval_id=approval_id, kind=record["kind"])
    print("Approved and recorded. Connect the relevant provider adapter before enabling delivery.")


def create_email_draft(to: str, subject: str, body: str) -> None:
    approval_id = new_approval("email_send", {"to": to, "subject": subject, "body": body})
    notify("Jarvis draft ready", f"Approval required: {approval_id}")
    speak(f"I drafted an email to {to}. Approval ID is {approval_id}.")
    print(f"Draft created. Review with: python jarvis.py approvals; approve with: python jarvis.py approve {approval_id}")


def read_notifications() -> None:
    raw = run_android(["termux-notification-list"])
    if not raw:
        print("No notification data returned. Install Termux:API and grant notification access.")
        return
    try:
        items = json.loads(raw)
    except json.JSONDecodeError:
        print(raw)
        return
    for item in items:
        print(f"[{item.get('packageName', 'unknown')}] {item.get('title', '')}: {item.get('content', '')}")


def main() -> int:
    ensure_dirs()
    parser = argparse.ArgumentParser(prog="jarvis", description="Safe Jarvis Termux companion")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("speak").add_argument("text")
    call_parser = sub.add_parser("call", help="Call your own configured number")
    call_parser.add_argument("number", nargs="?", default=os.getenv("JARVIS_OWNER_NUMBER"))
    sub.add_parser("notifications")
    sub.add_parser("approvals")
    approve_parser = sub.add_parser("approve")
    approve_parser.add_argument("approval_id")
    draft = sub.add_parser("draft-email")
    draft.add_argument("to")
    draft.add_argument("subject")
    draft.add_argument("body")
    args = parser.parse_args()

    if args.command == "speak":
        speak(args.text)
    elif args.command == "call":
        if not args.number:
            raise SystemExit("Set JARVIS_OWNER_NUMBER or pass a phone number explicitly.")
        call(args.number)
    elif args.command == "notifications":
        read_notifications()
    elif args.command == "approvals":
        list_pending()
    elif args.command == "approve":
        approve(args.approval_id)
    elif args.command == "draft-email":
        create_email_draft(args.to, args.subject, args.body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
