# STATUS: all five PDFs received & processed on 2026-07-03 (es/fr/ru ingested as text; zh/ar captured, text pending — see GAPS G-2c).

# Awaiting: the five non-English authentic PDFs (for GAPS.md G-2)

Download each official UN PDF and save it into this `capture/` folder with the EXACT filename
below (so the ingest step is turnkey). Source: the UN BBNJ Agreement "Text of the Agreement" page.

| Language | Save as (in capture/) | Official URL |
|---|---|---|
| Arabic (ar)  | `Text of the Agreement in Arabic.pdf`  | https://www.un.org/bbnjagreement/sites/default/files/2024-08/Text%20of%20the%20Agreement%20in%20Arabic.pdf |
| Chinese (zh) | `Text of the Agreement in Chinese.pdf` | https://www.un.org/bbnjagreement/sites/default/files/2024-08/Text%20of%20the%20Agreement%20in%20Chinese.pdf |
| French (fr)  | `Text of the Agreement in French.pdf`  | https://www.un.org/bbnjagreement/sites/default/files/2024-08/Text%20of%20the%20Agreement%20in%20French.pdf |
| Russian (ru) | `Text of the Agreement in Russian.pdf` | https://www.un.org/bbnjagreement/sites/default/files/2024-08/Text%20of%20the%20Agreement%20in%20Russian.pdf |
| Spanish (es) | `Text of the Agreement in Spanish.pdf` | https://www.un.org/bbnjagreement/sites/default/files/2024-08/Text%20of%20the%20Agreement%20in%20Spanish.pdf |

## Model (how each is ingested)
The Agreement is ONE instrument authentic in six UN languages (Art. 76). Each language is a
sibling authoritative record so the tooling can show each text with its own provenance:
- English  → `corpus_id: un/bbnj-agreement-2023`      (primary; already ingested)
- Arabic   → `corpus_id: un/bbnj-agreement-2023-ar`
- Chinese  → `corpus_id: un/bbnj-agreement-2023-zh`
- French   → `corpus_id: un/bbnj-agreement-2023-fr`
- Russian  → `corpus_id: un/bbnj-agreement-2023-ru`
- Spanish  → `corpus_id: un/bbnj-agreement-2023-es`
All: `version_id: 2023-06-19`, `authoritative_status: authentic_text`, `authentic_languages:
[ar,zh,en,fr,ru,es]`, cross-linked via `related_documents`. Each captured byte-exact as
`original.pdf`, extracted with `pdftotext -raw`, cleaned per language, and verified against the PDF.
