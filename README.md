# Lead Follow-Up

A follow-up operating system that runs on your machine, drafts in your voice, and never sends anything without you.

Why does most AI output feel generic? Because the AI has no idea who you are. No idea what you sell. No idea how you sound. This repo fixes that: you give it your business knowledge, your lead data, and your real voice — it gives you follow-up drafts that answer what each lead actually asked. And it keeps learning from every edit you make.

You don't need to move your CRM. Maybe you don't even need a CRM. A Sheet, a CSV, an inbox export, or your existing CRM is enough.

## Quick start

You need [Claude Code](https://claude.com/claude-code) (or Claude Cowork) and Python 3. Nothing else — no packages, no cloud, no accounts.

```bash
git clone https://github.com/kimwwk/lead-followup.git
cd lead-followup
```

Open Claude Code in the folder. [CLAUDE.md](CLAUDE.md) teaches it how to operate everything, so you drive the whole system in plain English:

| You say | It does |
|---|---|
| `pull my leads` | pulls your CRM or file sources into the local data lake |
| `snapshot my leads` | builds a one-line picture of every lead from your notes and tags |
| `draft follow-ups` | writes one draft per lead — grounded in your business facts, in your voice |
| `start the dashboard` | serves the review deck at http://localhost:8787/app/ |
| `learn from my edits` | turns your edits into voice rules and redrafts what's left |

Want to see it before adding any data? Run `bash app/serve.sh` and open the dashboard — it ships with five sample leads, so the review deck works on first clone.

## Make it yours: three inputs

The whole system runs on three things only you have. Drop them into `raw_data/` — each folder has a README telling you what goes in:

1. **`raw_data/business/`** — who you are and what you sell: positioning, offers, FAQ, your story. Drafts only quote facts that exist here.
2. **`raw_data/lead_sources/`** — where your leads live: CSV, Excel, inbox exports. Or connect a CRM (GoHighLevel works out of the box — see below).
3. **`raw_data/voice/`** — how you sound. Don't describe it, show it: a few real emails and chats beat any style description.

This is the step nobody can do for you — and it's exactly why the drafts stop feeling generic.

## Review, don't babysit

The dashboard is a swipe deck: one lead per card, the bland mail-merge template on the left, the AI draft on the right, the AI's one-line reasoning always visible.

- `→` approve · `←` reject · `↑` full client detail
- Click the draft to edit it. Add one line on *why* you changed it — optional, but it's the deepest signal you can give.
- Nothing is ever sent. "Export decisions" downloads the full audit trail as JSON.

## It learns your voice — for real

Every edit you make is training data:

1. Edit a few drafts in the deck, then hit **Export decisions**.
2. Tell the AI: `learn from my edits`.
3. It appends your edit triples — AI draft, your version, your why, all verbatim — to `raw_data/voice/edit_triples.json`. Append-only evidence, never rewritten.
4. Patterns that repeat across 2+ edits (or that you stated in a *why*) get promoted to `data_lake/voice_rules.md`. One-offs stay on a watch list. Once is noise; repeated is voice.
5. Every lead you haven't decided yet gets redrafted under the new rules. Refresh the dashboard: v2 drafts, and the Style rules button shows exactly what it learned.

The rules file is small and human-readable — open it, argue with it, delete anything you disagree with. You own the voice; the system just keeps the receipts.

## What it deliberately does NOT do

It stops before sending. That's not a limitation, that's the feature. Your name is on that message: you review, you edit, you send, from wherever you normally send. Once you trust the drafts, approving takes seconds.

It also never writes to your CRM unless you explicitly ask, and a lead marked Do-Not-Disturb never gets a draft.

## Connect a CRM

GoHighLevel is wired in:

```bash
cp config/ghl.env.example config/ghl.env
# fill in your private-integration token — ghl.env is gitignored and never leaves your machine
```

Then say `pull my leads`. Other sources plug into `integrations/` the same way: one pull script per source, all normalizing into the same `data_lake/leads.json` profile, merged by email or phone.

## Layout

```
CLAUDE.md            the operator manual — how the AI runs this repo (data contracts live here)
raw_data/            LAYER 1 · your knowledge: business/ · lead_sources/ · voice/
config/              CRM credentials (gitignored)
integrations/        LAYER 2 · pull scripts — GoHighLevel today, yours next
data_lake/           the unified view: every lead one profile, plus drafts and learned voice rules
app/                 LAYER 3 · dashboard + review deck — single file, zero dependencies, offline
.claude/skills/      the learn-from-edits skill (the learning loop, spelled out)
```

Your leads, your voice, and your drafts stay on your machine.

## License

[MIT](LICENSE) — clone it, adapt it, make it yours.
