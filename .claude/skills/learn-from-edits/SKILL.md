---
name: learn-from-edits
description: Learn the human's voice from their review-deck edits. Run whenever they say "learn from my edits" (or hand you an exported decisions JSON). Appends edit triples to raw_data/voice/edit_triples.json, promotes ONLY repeating patterns into data_lake/voice_rules.md, then redrafts the still-pending leads with the learned rules.
---

# Learn from my edits

You are closing the loop that makes drafts sound like the human: their real edits are the training data. Everything below is file I/O plus judgment — no server, no network.

## 1. Find the decisions export

The dashboard's "Export decisions" button downloads `lead-decisions-*.json`.

1. If the human gave a path, use it.
2. Otherwise take the NEWEST `lead-decisions-*.json` from, in order: `~/Downloads/`, `/mnt/c/Users/*/Downloads/` (WSL), `~/Desktop/`, the repo root.
3. If none found, ask the human to export from the dashboard (Style rules panel or header button) and tell you where it landed.

Confirm which file you picked (name + exported_at) before using it.

## 2. Append edit triples to the voice folder (raw evidence)

For every entry in `decisions[]` where `edited` is true, append one triple to `raw_data/voice/edit_triples.json` (create the file with `[]` if missing):

```json
{
  "lead_id": "<contact_id>",
  "lead_name": "<name>",
  "channel": "<channel>",
  "date": "<edit.ts, date part>",
  "context": "<one line: stage + what the lead asked>",
  "original": "<edit.original — the AI draft, verbatim>",
  "edited": "<edit.edited — the human's version, verbatim>",
  "why": "<edit.why verbatim, or null if they didn't say>",
  "verdict": "<decision: approved | rejected | pending>",
  "draft_version": "<edit.draft_version>"
}
```

Rules for this step:

- Read → extend → rewrite the whole array, then validate: `python3 -c "import json; json.load(open('raw_data/voice/edit_triples.json'))"`.
- **Append-only.** Never rewrite or delete existing triples — they are the audit trail.
- Skip duplicates: a triple with the same `lead_id` + same `edit.ts` as an existing one is already ingested.
- `original`, `edited`, `why` are verbatim. Never paraphrase the human's words.

## 3. Distill: promote only what repeats (the evidence bar)

Compare `original` → `edited` across ALL triples in the file (old + new), and read every `why`. Derive candidate patterns (greeting changes, length cuts, punctuation, sign-off, word swaps, structure, facts they add or remove — whatever the diffs actually show).

Promotion bar — apply strictly:

- **Promote** a candidate to a rule only if it appears in **2 or more independent edits**, OR the human stated it explicitly in a `why`.
- A pattern seen once with no `why` goes to **Watching**, not rules. Once is noise; repeated is voice.
- Rules come ONLY from what the human's edited text proves. Never invent a rule because it would be good writing advice, and never derive one from AI-drafted text they didn't touch.
- A `why` is the strongest signal — quote it verbatim inside the rule's evidence.

## 4. Write `data_lake/voice_rules.md`

The dashboard renders this file, so keep the format contract exactly: `## ` section headings, **one rule per top-level `- ` bullet, one line each**. No nested bullets, no paragraphs between bullets.

```markdown
# Voice rules — learned from your edits

> Written by the agent. Evidence: raw_data/voice/edit_triples.json (N triples). Updated YYYY-MM-DD.

## Voice rules
- Open with the first name — no "Hi" (evidence: 3 edits)
- Keep it under 60 words (evidence: 2 edits; your words: "too long, nobody reads this")

## Watching (seen once — not yet a rule)
- Swapped "athletes" for "kids" in one youth draft (1 edit)
```

- Update in place on later runs: a Watching item that repeats moves up to rules; evidence counts refresh.
- Hard cap ~25 rule bullets. If you'd exceed it, consolidate overlapping rules instead of appending.
- If an old rule is contradicted by newer edits, rewrite it and note the reversal in its evidence.

## 5. Redraft the pending leads

For every lead whose `decision` is `"pending"` in the export:

1. Load the knowledge layer: `raw_data/business/`, `raw_data/voice/` samples, and the fresh `data_lake/voice_rules.md`.
2. Rewrite its `ai_draft` in `data_lake/drafts.json` applying the promoted rules (Watching items don't apply — they're not rules yet). Same grounding discipline as "draft follow-ups" in CLAUDE.md: answer the lead's actual words, quote only real facts, respect channel limits and DND.
3. Bump that lead's `version` (absent or 1 → 2, 2 → 3, …) and refresh its `reasoning` line.
4. Do NOT touch approved or rejected leads, the `rule_template`, or DND refusals.

Validate `drafts.json` with `python3 -c "import json; json.load(open('data_lake/drafts.json'))"` after writing.

## 6. Report back

Tell the human, briefly:

- Triples ingested (new / total), and how many carried a `why`.
- Rules promoted, each with its evidence count — and what stayed in Watching.
- How many drafts were redrafted to which version.
- Finish with: **"Refresh the dashboard — the pending drafts are redrafted, and the Style rules button now shows what I learned."**

## Hard rules

- Never send anything, never write to the CRM. This skill touches only `raw_data/voice/edit_triples.json`, `data_lake/voice_rules.md`, `data_lake/drafts.json`.
- No edits in the export → say so and write nothing.
- The human's words stay verbatim everywhere they're quoted.
