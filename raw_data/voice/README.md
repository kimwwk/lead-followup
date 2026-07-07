# raw_data/voice — how you sound

Don't describe your voice. Show it. Drop in:

- a few real emails you wrote (the everyday ones, not the polished ones)
- chat or DM conversations showing how you actually talk to clients

The AI extracts your points and your style from these samples. The more real samples, the more the drafts sound like you.

And it keeps learning: every draft you edit in the review deck teaches the system more. When you tell the agent "learn from my edits", your edits land here as `edit_triples.json` (append-only evidence: what the AI wrote, what you changed it to, and — if you filled in the one-line "why" — your reason in your own words). Patterns that repeat get promoted into `data_lake/voice_rules.md` and every future draft uses them. See "learn from my edits" in CLAUDE.md.

Optional: `_templates/3-voice-core.md` is a fill-in worksheet for *describing* your voice in words (traits, guardrails, banned/power phrases). Real samples above teach the AI more than any description — the worksheet stays in `_templates/` so the AI never reads the blank form as your voice.
