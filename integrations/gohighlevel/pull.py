#!/usr/bin/env python3
"""GoHighLevel -> local data lake, normalized.

What it does (and prints, so you can watch):
  1. Pull all contacts from your GHL sub-account (paginated, parallel-safe)
  2. Pull every contact's notes (parallel)
  3. Normalize into the unified lead profile -> data_lake/leads.json
     (raw CRM copies kept in data_lake/contacts.json + contacts.csv)
  4. Merge the local AI layer (snapshots/drafts) into each profile when present

Normalized profile (data_lake/leads.json, one object per lead):
  id, name, first_name, last_name
  contact:   { email, phone }
  location:  { city, province, country }
  crm:       { source, tags, added_at, updated_at, type, dnd }
  inquiry:   first CRM note body ("" if none)
  notes:     all CRM note bodies, newest first
  ai:        { snapshot, inquiry, channel, stage, last_touch, why_cold, notes } | null
  draft:     { ai_draft, reasoning, ai_draft_v2, style_rules_applied } | null
             (rule_based is a single global "rule_template" at the top of drafts.json,
              not per-lead — merged by the dashboard, so it is not copied into each profile)

Setup: cp config/ghl.env.example config/ghl.env, fill in your values
       (or export GHL_PIT + GHL_LOCATION_ID).
Usage: python3 integrations/gohighlevel/pull.py
       Safe to re-run; overwrites data_lake outputs. Cron-friendly: schedule it
       and the lake stays fresh.
"""

import csv
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
LAKE = os.path.join(ROOT, "data_lake")
CONFIG = os.path.join(ROOT, "config", "ghl.env")

BASE = "https://services.leadconnectorhq.com"

CSV_FIELDS = ["id", "firstName", "lastName", "email", "phone", "companyName",
              "source", "tags", "city", "state", "dateAdded", "country"]


def load_credentials() -> tuple[str, str]:
    cfg = {}
    if os.path.exists(CONFIG):
        for line in open(CONFIG):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    pit = os.environ.get("GHL_PIT") or cfg.get("GHL_PIT", "")
    loc = os.environ.get("GHL_LOCATION_ID") or cfg.get("GHL_LOCATION_ID", "")
    if not pit or pit.startswith("pit-xxxx") or not loc or loc.startswith("your-"):
        raise SystemExit(
            "Missing GHL credentials.\n"
            "  cp config/ghl.env.example config/ghl.env\n"
            "then fill in GHL_PIT and GHL_LOCATION_ID (or export both as env vars)."
        )
    return pit, loc


PIT, LOCATION_ID = load_credentials()
# Cloudflare in front of GHL 403s the default Python-urllib UA — keep a real User-Agent
HDRS = {"Authorization": f"Bearer {PIT}", "Version": "2021-07-28", "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (lead-followup-blueprint)"}


def api_get(path: str, params: dict | None = None, tries: int = 5):
    url = f"{BASE}{path}" + (f"?{urllib.parse.urlencode(params)}" if params else "")
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=HDRS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if attempt < tries - 1 and e.code in (403, 429, 500, 502, 503):
                retry_after = e.headers.get("Retry-After")
                time.sleep(float(retry_after) if retry_after else 3.0 * (attempt + 1))
                continue
            raise SystemExit(f"GHL API failed after {tries} tries: {url} -> {e}")
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < tries - 1:
                time.sleep(2.0 * (attempt + 1))
                continue
            raise SystemExit(f"GHL API failed after {tries} tries: {url} -> {e}")


def pull_contacts() -> list[dict]:
    contacts, start_after, start_after_id = [], None, None
    while True:
        params = {"locationId": LOCATION_ID, "limit": 100}
        if start_after_id:
            params.update(startAfterId=start_after_id, startAfter=start_after)
        page = api_get("/contacts/", params)
        contacts.extend(page.get("contacts", []))
        meta = page.get("meta", {})
        total = meta.get("total", 0)
        if not page.get("contacts") or len(contacts) >= total:
            return contacts
        start_after_id, start_after = meta.get("startAfterId"), meta.get("startAfter")


def pull_notes(cid: str) -> list[dict]:
    return (api_get(f"/contacts/{cid}/notes").get("notes")) or []


def load_optional(name: str) -> dict:
    path = os.path.join(LAKE, name)
    return json.load(open(path)) if os.path.exists(path) else {}


def normalize(c: dict, notes: list[dict], ai: dict | None, draft: dict | None) -> dict:
    notes_sorted = sorted(notes, key=lambda n: n.get("dateAdded", ""), reverse=True)
    bodies = [n.get("body", "") for n in notes_sorted]
    return {
        "id": c["id"],
        "name": f"{c.get('firstNameRaw') or c.get('firstName') or ''} {c.get('lastNameRaw') or c.get('lastName') or ''}".strip(),
        "first_name": c.get("firstNameRaw") or c.get("firstName") or "",
        "last_name": c.get("lastNameRaw") or c.get("lastName") or "",
        "contact": {"email": c.get("email"), "phone": c.get("phone")},
        "location": {"city": c.get("city"), "province": c.get("state"), "country": c.get("country")},
        "crm": {
            "source": c.get("source"),
            "tags": c.get("tags", []),
            "added_at": c.get("dateAdded"),
            "updated_at": c.get("dateUpdated"),
            "type": c.get("type"),
            "dnd": bool(c.get("dnd")),
        },
        "inquiry": bodies[-1] if bodies else "",
        "notes": bodies,
        "ai": ai,
        "draft": draft,
    }


def main() -> None:
    os.makedirs(LAKE, exist_ok=True)

    t0 = time.time()
    contacts = pull_contacts()
    t1 = time.time()
    print(f"[1/3] pulled {len(contacts)} contacts from GHL in {t1-t0:.1f}s")

    with ThreadPoolExecutor(max_workers=4) as pool:
        notes_by_id = dict(zip(
            [c["id"] for c in contacts],
            pool.map(pull_notes, [c["id"] for c in contacts]),
        ))
    t2 = time.time()
    n_notes = sum(len(v) for v in notes_by_id.values())
    print(f"[2/3] pulled {n_notes} notes across {len(contacts)} contacts in {t2-t1:.1f}s")

    snapshots, drafts = load_optional("snapshots.json"), load_optional("drafts.json")
    leads = [normalize(c, notes_by_id[c["id"]], snapshots.get(c["id"]), drafts.get(c["id"]))
             for c in contacts]

    json.dump(contacts, open(os.path.join(LAKE, "contacts.json"), "w"), indent=2)
    json.dump(leads, open(os.path.join(LAKE, "leads.json"), "w"), indent=2)
    with open(os.path.join(LAKE, "contacts.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        for c in contacts:
            row = {k: c.get(k, "") for k in CSV_FIELDS}
            row["tags"] = ";".join(row["tags"]) if isinstance(row["tags"], list) else row["tags"]
            w.writerow(row)

    with_ai = sum(1 for l in leads if l["ai"])
    print(f"[3/3] normalized {len(leads)} lead profiles -> data_lake/leads.json "
          f"({with_ai} with AI layer, {len(leads)-with_ai} CRM-only) — total {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
