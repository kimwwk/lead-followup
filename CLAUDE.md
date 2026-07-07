# CLAUDE.md — how to operate this repo

You are the operator of a local lead follow-up system. The human owns every decision; you do the mechanical work. Operate only inside this folder.

## Hard rules

1. NEVER send anything: no emails, no DMs, no messages. You draft; the human sends.
2. NEVER write to the CRM unless the human explicitly asks for a write-back.
3. Credentials live in `config/ghl.env` (gitignored). Never print, commit, or copy the token anywhere else.
4. A lead with `crm.dnd: true` gets NO draft. Record the refusal in `reasoning` instead.
5. Never invent facts about the business. If a price or offer is not in `raw_data/business/`, don't quote one.
6. Leave git alone: never stage, commit, or re-init unless the human explicitly asks. New files are meant to stay visible as uncommitted changes.

## The flow

```
raw_data (human fills) -> integrations pull -> data_lake -> AI drafts -> review deck -> human edits -> AI learns
```

## Playbook

### "pull my leads" / "pull my data"

- **GoHighLevel:** confirm `config/ghl.env` exists; if not, tell the human to copy `config/ghl.env.example` and fill it in. Then run:
  ```bash
  python3 integrations/gohighlevel/pull.py
  ```
  Takes ~10-20s for ~40 contacts, survives GHL rate limiting, prints progress. Report the final counts to the human.
- **File sources** (CSV / Excel / WhatsApp / inbox exports in `raw_data/lead_sources/`): read them and normalize into the same `leads.json` schema below. Merge by email or phone when a lead exists in more than one source.

### "snapshot my leads"

Build the lead snapshots: from each lead's notes, tags, and source in `data_lake/leads.json`, write `data_lake/snapshots.json`. Stay faithful to what the notes say; do not embellish. The dashboard needs this file: it loads contacts + snapshots + drafts all-or-nothing and falls back to embedded sample data if any one is missing.

### "draft follow-ups"

1. Read the knowledge layer first: everything in `raw_data/business/` and `raw_data/voice/`, plus `data_lake/voice_rules.md` if it exists (the accumulated learned voice).
2. From the voice samples, extract how the human actually writes: greeting, sentence length, sign-off, words they use, words they never use.
3. For every lead in `data_lake/leads.json`, write `data_lake/drafts.json` (schema below):
   - `rule_template`: ONE fixed mail-merge template stored ONCE at the top of `drafts.json`, with `{name}` as the only merge field (the dashboard fills it per lead). Do NOT re-generate or copy it into each lead — write it once, leave it. Keep it bland on purpose; it is the side-by-side contrast.
   - `ai_draft`: answers the lead's ACTUAL words (their inquiry and notes), quotes real facts from `raw_data/business/`, written in the human's voice.
   - Channel-aware: DM replies <= 80 words; emails get a subject line; public comment replies never contain prices (invite to DM instead); if the lead is a minor, address the parent.
   - `reasoning`: one line on why this angle. Always visible to the human.
4. The dashboard reads `contacts.json` + `snapshots.json` + `drafts.json` directly, all-or-nothing: if `snapshots.json` is missing, snapshot the leads first (see "snapshot my leads"), or the app silently falls back to its embedded sample data (banner shown). `leads.json` picks up the merged ai/draft layers on the next pull.

### "start the dashboard"

```bash
bash app/serve.sh   # run in background
```
Open http://localhost:8787/app/ — review deck keys: left = reject, right = approve, up = detail. Drafts are inline-editable. "Export decisions" downloads the audit JSON.

### "learn from my edits"

The crazy part. Follow `.claude/skills/learn-from-edits/SKILL.md` — it is the canonical procedure. In short:

1. Find the human's exported decisions JSON (`lead-decisions-*.json`, usually in Downloads).
2. Append one edit triple per edited draft (AI original / human edited / their optional `why`, all verbatim) to `raw_data/voice/edit_triples.json` — append-only raw evidence.
3. Promote ONLY patterns that repeat across 2+ independent edits (or that the human stated in a `why`) into `data_lake/voice_rules.md`. Single sightings stay in its Watching section.
4. Redraft the still-pending leads in `drafts.json` with the promoted rules, bumping each lead's `version`. Approved/rejected leads and the `rule_template` stay untouched.
5. Tell the human to refresh the dashboard.

Never promote a pattern from a single edit. Once is noise; repeated is voice.

## data_lake schemas

`leads.json` — array, one object per lead (written by pull):
```
id, name, first_name, last_name
contact:  { email, phone }
location: { city, province, country }
crm:      { source, tags, added_at, updated_at, type, dnd }
inquiry:  first CRM note body ("" if none)
notes:    all CRM note bodies, newest first
ai:       { snapshot, inquiry, channel, stage, last_touch, why_cold, notes } | null
draft:    { ai_draft, reasoning, version? } | null   # rule_based is global, not per-lead
```

`snapshots.json` / `drafts.json` — objects keyed by lead id:
```
snapshots: { "<leadId>": { snapshot, inquiry, channel, stage, last_touch, why_cold, notes } }
drafts:    { "rule_template": "Hi {name}, …",                # ONE fixed template, {name} merged per lead
             "<leadId>": { ai_draft, reasoning, version? } } # version >= 2 = redrafted from learned voice rules
```

Voice-learning files (the "learn from my edits" loop):
```
raw_data/voice/edit_triples.json   append-only raw evidence: {lead_id, lead_name, channel, date,
                                   context, original, edited, why, verdict, draft_version}
data_lake/voice_rules.md           learned rules the agent applies when drafting; the dashboard
                                   renders it ("## Section" headings + one "- " bullet per rule)
```
