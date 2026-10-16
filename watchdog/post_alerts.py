"""Post Payflows Watchdog alerts to Slack through an Incoming Webhook.

Usage:
    python3 post_alerts.py alerts_demo.json            # post every alert
    python3 post_alerts.py alerts_demo.json --only 0   # post one alert by index
    python3 post_alerts.py alerts_demo.json --dry-run  # print the Block Kit payload
    echo '{...one alert...}' | python3 post_alerts.py -   # post one alert from stdin (used by the live loop)

The webhook URL is read from SLACK_WEBHOOK_URL, or from a .env file next to this script.
Standard library only, nothing to install.
"""

import json
import os
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent


def webhook_url():
    url = os.environ.get("SLACK_WEBHOOK_URL")
    env = HERE / ".env"
    if not url and env.exists():
        for line in env.read_text().splitlines():
            if line.strip().startswith("SLACK_WEBHOOK_URL="):
                url = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not url:
        sys.exit("SLACK_WEBHOOK_URL is missing: put it in watchdog/.env")
    return url


def blocks_for(alert):
    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": f"{alert['emoji']} {alert['title']}", "emoji": True}},
        {"type": "section", "text": {"type": "mrkdwn", "text": alert["text"]}},
    ]
    if alert.get("fields"):
        blocks.append({
            "type": "section",
            "fields": [{"type": "mrkdwn", "text": f"*{k}*\n{v}"} for k, v in alert["fields"].items()],
        })
    if alert.get("buttons"):
        elements = []
        for i, b in enumerate(alert["buttons"]):
            button = {
                "type": "button",
                "action_id": f"open_{i}",
                "text": {"type": "plain_text", "text": b["text"], "emoji": True},
                "url": b["url"],
            }
            if b.get("style"):
                button["style"] = b["style"]
            elements.append(button)
        blocks.append({"type": "actions", "elements": elements})
    blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": alert.get("footer", "Payflows Watchdog")}]})
    return blocks


def post(url, alert):
    if "raw_text" in alert:
        payload = {"text": alert["raw_text"]}
    else:
        payload = {"text": f"{alert['emoji']} {alert['title']}", "blocks": blocks_for(alert)}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, resp.read().decode()


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    raw = sys.stdin.read() if args[0] == "-" else Path(args[0]).read_text()
    alerts = json.loads(raw)
    if isinstance(alerts, dict):
        alerts = [alerts]
    if "--only" in args:
        alerts = [alerts[int(args[args.index("--only") + 1])]]
    if "--dry-run" in args:
        print(json.dumps([blocks_for(a) for a in alerts], indent=2, ensure_ascii=False))
        return
    url = webhook_url()
    for alert in alerts:
        status, body = post(url, alert)
        print(f"{status} {body} - {alert.get('title') or alert.get('name')}")


if __name__ == "__main__":
    main()
