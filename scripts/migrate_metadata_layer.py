#!/usr/bin/env python3
"""Metadata-layer migration (BBNJ / High Seas corpus).
Adds binding_force + issuing_authority + administering_authority to every record.
Metadata-only; never touches text or hashes. Idempotent. See migration plan."""
from __future__ import annotations
import glob, json, os
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = os.path.join(ROOT, "schema", "authoritative-metadata.schema.json")

BINDING = {"treaty":"binding","convention":"binding","implementing_agreement":"binding",
           "resolution":"non_binding","decision":"non_binding","prepcom_document":"non_binding"}
ISSUER_BY_TYPE = {
    "treaty":"Intergovernmental Conference on Marine Biological Diversity of Areas Beyond National Jurisdiction (United Nations)",
    "convention":"Third United Nations Conference on the Law of the Sea",
    "resolution":"United Nations General Assembly",
    "decision":"United Nations General Assembly",
    "prepcom_document":"BBNJ Preparatory Commission (United Nations)"}
ISSUER_BY_ID = {
    "un/agreement-partxi-1994":"United Nations General Assembly",
    "un/fish-stocks-agreement-1995":"United Nations Conference on Straddling Fish Stocks and Highly Migratory Fish Stocks"}
ADMIN_BY_ID = {}

def patch_schema():
    txt = open(SCHEMA, encoding="utf-8").read()
    if "binding_force" in txt:
        print("schema: already patched"); return
    req = '    "provenance_note"\n  ],'
    if req not in txt: raise SystemExit("required-array anchor not found")
    txt = txt.replace(req, '    "provenance_note",\n    "binding_force",\n    "issuing_authority"\n  ],', 1)
    anchor = '    "provenance_note": {\n      "type": "string",\n      "minLength": 1\n    },\n'
    if anchor not in txt: raise SystemExit("provenance_note property anchor not found")
    add = (anchor +
      '    "binding_force": {\n      "type": "string",\n      "enum": [\n        "binding",\n        "non_binding"\n      ],\n'
      '      "description": "Legal force of the instrument on its own accord: binding or non_binding (recommendatory soft law). Orthogonal to authoritative_status; tier is DERIVED from jurisdiction downstream."\n    },\n'
      '    "issuing_authority": {\n      "type": "string",\n      "description": "Body that made/adopted the instrument. Distinct from source_publisher (where the text was obtained)."\n    },\n'
      '    "administering_authority": {\n      "type": [\n        "string",\n        "null"\n      ],\n      "description": "Body that administers/enforces the instrument where different from the issuer; null if not applicable."\n    },\n')
    txt = txt.replace(anchor, add, 1)
    json.loads(txt)
    open(SCHEMA, "w", encoding="utf-8").write(txt)
    print("schema: patched")

def yq(v): return '"' + v.replace('\\','\\\\').replace('"','\\"') + '"'

def backfill():
    changed = skipped = 0
    for f in sorted(glob.glob(os.path.join(ROOT,"authoritative","**","metadata.yaml"), recursive=True)):
        raw = open(f, encoding="utf-8").read()
        d = yaml.safe_load(raw)
        if "binding_force" in d and "issuing_authority" in d:
            skipped += 1; continue
        cid, dt = d.get("corpus_id"), d.get("document_type")
        bf = BINDING.get(dt)
        issuer = ISSUER_BY_ID.get(cid) or ISSUER_BY_TYPE.get(dt)
        admin = ADMIN_BY_ID.get(cid)
        if not bf or not issuer: raise SystemExit(f"no mapping for {dt} / {cid}")
        new = raw if raw.endswith("\n") else raw + "\n"
        new += f"binding_force: {bf}\n"
        new += f"issuing_authority: {yq(issuer)}\n"
        new += f"administering_authority: {yq(admin) if admin else 'null'}\n"
        d2 = yaml.safe_load(new)
        assert d2["binding_force"] == bf and d2["issuing_authority"] == issuer
        open(f, "w", encoding="utf-8").write(new)
        changed += 1
        print(f"  {cid:34} {dt:22} | {bf:11} | {issuer[:44]}")
    print(f"backfill: {changed} changed, {skipped} skipped")

if __name__ == "__main__":
    patch_schema(); backfill()
