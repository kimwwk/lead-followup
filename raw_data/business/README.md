# raw_data/business — who you are, what you sell

The follow-up AI reads **everything** in this folder as ground truth. It knows nothing
about your business except what's here, and it quotes these files directly — so real
offer names, real prices, and real client results matter. Never leave blank templates
or someone else's examples loose in here: the AI can't tell a placeholder from a fact.

Voice and tone don't belong here — those live in `../voice/`.

## What to put here (roughly in order of impact on drafts)

- **offer + prices** — every offer, exact price, what's included. Drafts quote these verbatim.
- **objections** — why leads stall, in their words, and what each one *actually* means. A follow-up usually has to answer the objection that went cold.
- **proof** — specific client results and testimonials. Turns vague claims into proof.
- **FAQ** — the questions you answer over and over.
- **story** — your origin and why you're the one to help; used for credibility beats.

Plain files only (`.md`, `.txt`, `.pdf`); one topic per file is easiest to maintain.

## Starting from scratch?

`_templates/` holds two fill-in guides — `1-positioning-core.md` (who you help, story,
language) and `2-offer-core.md` (offer, proof, objections, CTAs). Copy what's useful into
real files here, **strip the scaffolding and examples**, and delete anything you left blank.
Files under `_templates/` are references only — keep them there so the AI never reads them as facts.
