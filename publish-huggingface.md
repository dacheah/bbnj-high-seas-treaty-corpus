# publish-huggingface.md — publish the dataset to Hugging Face (run on your machine)

The dataset is already generated at `hf-dataset/` (2 JSONL configs + the dataset card):
- `hf-dataset/data/documents.jsonl` — 6 rows, one per authentic language (full text + provenance).
- `hf-dataset/data/provisions.jsonl` — 317 rows, one per provision + neutral concept tags.
- `hf-dataset/README.md` — the dataset card (all six languages, honest fidelity flags).

HF upload needs a real network (it was blocked inside Cowork), so run these locally.

## 1. Install + upload — PATH-independent (recommended on Windows)
`huggingface-cli` often isn't on PATH after `pip install`. Skip it — upload straight from Python:
```powershell
python -m pip install -U huggingface_hub
$env:HF_TOKEN = "hf_xxx_your_WRITE_token"     # from https://huggingface.co/settings/tokens
python scripts/export_hf_dataset.py --push dacheah/bbnj-high-seas-treaty-corpus
```
`--push` regenerates the dataset, **creates the HF dataset repo if needed**, and uploads it. Done.

(The env var lasts for this PowerShell session only; it is not written to disk or Git.)

---

## Alternative — the CLI (if you prefer)
### Install + log in (once)
```powershell
pip install huggingface_hub
huggingface-cli login        # paste a WRITE token from https://huggingface.co/settings/tokens
```

## 2. (Optional) refresh the dataset if the corpus changed
```powershell
python scripts/export_hf_dataset.py
```

## 3. Upload
```powershell
huggingface-cli upload dacheah/bbnj-high-seas-treaty-corpus ./hf-dataset . --repo-type dataset
```
This creates the dataset repo if it doesn't exist and pushes the files. (Newer CLI: `hf upload …`.)
Or push directly from the export script: `python scripts/export_hf_dataset.py --push dacheah/bbnj-high-seas-treaty-corpus`

## 4. Verify
- Open https://huggingface.co/datasets/dacheah/bbnj-high-seas-treaty-corpus — the card renders and
  the Data Studio previews `documents` / `provisions`.
- Smoke-test loading:
```python
from datasets import load_dataset
docs = load_dataset("dacheah/bbnj-high-seas-treaty-corpus", "documents")
prov = load_dataset("dacheah/bbnj-high-seas-treaty-corpus", "provisions")
print(docs["train"][0]["language"], len(prov["train"]))
```

## Notes
- The card links back to the GitHub repo as the source of truth; keep both in sync by re-running the
  export after corpus changes (it's deterministic).
- `hf-dataset/` is gitignored — it's a generated distribution artifact, not part of the Git history.
- Licensing/disclaimer travel in the card: derived layer CC BY 4.0; source texts keep their own terms;
  fidelity flags (`extracted_verified` / `extracted_unverified` / `ocr_unverified`) are per row.
