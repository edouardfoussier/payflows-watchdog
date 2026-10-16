"""State helper for the live Watchdog loop.

    python3 watchdog_state.py seed <retrieve_form_instances.json>   # mark every invoice in the file as seen
    python3 watchdog_state.py new <retrieve_form_instances.json>    # print new invoices as JSON (not yet seen)
    python3 watchdog_state.py mark <invoice_id> [draft_po_id]       # mark one invoice handled (+ record a draft)
    python3 watchdog_state.py status                                # show counters
"""

import json
import sys
from pathlib import Path

STATE = Path(__file__).parent / "state.json"
MAX_DRAFTS = 5


def load():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"seen": [], "drafts": [], "max_drafts": MAX_DRAFTS}


def save(state):
    STATE.write_text(json.dumps(state, indent=2))


def invoices(path):
    raw = json.loads(Path(path).read_text())
    return raw.get("form_instances", raw)


def summary(f):
    details = f.get("form_type_details") or {}
    values = f.get("predefined_step_values") or {}
    vendor = values.get("counterparty") or {}
    amount = values.get("amount") or {}
    ht = abs(amount.get("amount_before_tax") or details.get("amount_before_tax") or 0) / 100
    tax = abs(amount.get("tax") or 0) / 100
    return {
        "id": f["id"],
        "status": f["status"],
        "invoice_number": details.get("invoice_number"),
        "vendor": vendor.get("display_name"),
        "counterparty_id": vendor.get("counterparty_id"),
        "amount_ht": ht,
        "tax_rate": round(tax / ht, 4) if ht else None,
        "currency": amount.get("currency"),
        "period": [details.get("period_start_date"), details.get("period_end_date")],
        "invoice_date": details.get("delivery_date"),
        "due_at": details.get("due_at"),
        "entity_id": f.get("entity_id"),
        "requestor_id": f.get("requestor_id"),
        "description": f.get("form_instance_description"),
        "has_po": bool((details.get("links") or {}).get("purchase_orders")),
        "ready": bool(vendor.get("counterparty_id")) and ht > 0,
    }


def main():
    cmd, *args = sys.argv[1:] or ["status"]
    state = load()
    if cmd == "seed":
        ids = {f["id"] for f in invoices(args[0])}
        state["seen"] = sorted(set(state["seen"]) | ids)
        save(state)
        print(f"seeded {len(ids)} invoices, {len(state['seen'])} seen in total")
    elif cmd == "new":
        fresh = [summary(f) for f in invoices(args[0]) if f["id"] not in set(state["seen"])]
        print(json.dumps({"new": fresh, "drafts_left": state["max_drafts"] - len(state["drafts"])}, indent=2, ensure_ascii=False))
    elif cmd == "check":
        seen = set(state["seen"])
        fresh = [int(i) for i in args if int(i) not in seen]
        print(json.dumps({"new_ids": fresh, "drafts_left": state["max_drafts"] - len(state["drafts"])}))
    elif cmd == "mark":
        state["seen"] = sorted(set(state["seen"]) | {int(args[0])})
        if len(args) > 1:
            state["drafts"].append({"invoice_id": int(args[0]), "draft_po_id": int(args[1])})
        save(state)
        print(f"marked {args[0]}, drafts used {len(state['drafts'])}/{state['max_drafts']}")
    else:
        print(json.dumps({"seen": len(state["seen"]), "drafts": state["drafts"]}, indent=2))


if __name__ == "__main__":
    main()
