# raw_data/lead_sources — where your leads live

Two kinds of sources:

1. **File exports** — drop them here: CSV, Excel, inbox export, WhatsApp export. Then ask the AI to normalize them into the data lake.
2. **Live CRMs** (GoHighLevel today) — nothing goes in this folder. Copy `config/ghl.env.example` to `config/ghl.env`, fill in your credentials, and ask the AI to pull.

Your leads can live anywhere. The AI sees one unified customer context: `data_lake/leads.json`.
