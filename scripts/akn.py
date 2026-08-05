#!/usr/bin/env python3
"""Mint Akoma Ntoso Naming Convention Work-level identifiers — or honestly decline to.

WHY THIS FILE DECLINES MORE OFTEN THAN YOU MIGHT EXPECT
------------------------------------------------------
The country slot in AKN Naming Convention v1.0 is REQUIRED, and the spec is explicit
that it is "a two-letter or code according to ISO 3166-1 ... or a short and unique
alphanumeric code[] according to ISO 3166-2", and that it MUST equal <FRBRcountry>.
Every worked example in the specification is a nation-state (kn, dz, sl, ng, mg, ke, uy).
There is NO provision in the base convention for intergovernmental organisations.

Two published domain profiles extend the country slot to bodies that are not countries:

  AKN4UN  /akn/un/<doctype>/<subtype>/<author>/<date>/<number>
          with the ORGAN in the author slot, e.g.
          /akn/un/collection/publication/un-ga/2012-01-13/A-RES-66-1/eng
  AKN4EU  /akn/eu/...   ("eu" is exceptionally reserved in ISO 3166-1, so this is
          spec-legal independently of the profile.)

That leaves a real gap. The International Seabed Authority, ITLOS, the Antarctic
Treaty Secretariat and CCAMLR are autonomous treaty bodies — established BY treaties,
not organs of the UN — and none has an ISO 3166 code of any kind.

ISO 3166-1 does reserve AA, QM-QZ, XA-XZ and ZZ for private use, and we could simply
declare XA = ISA and mint away. This module deliberately does NOT do that:

  * A private code resolves for nobody. The entire value of a standard identifier is
    that a third party can act on it without holding our mapping table. /akn/xa/ has
    exactly the reach of our own corpus_id, which already exists.
  * AKN4EU, AKN4UN and AKN4Africa all exist, so a profile covering non-UN treaty
    bodies is a plausible future. If it lands and it is not our letters, we would be
    holding published identifiers we know to be wrong. Changing a published identifier
    is worse than never having minted one.

So: where a conformant code exists we mint deterministically; where it does not we
return (None, "none", <reason>) and the reason is recorded in the record. An absence
that explains itself is a stronger claim than a fabrication that validates.

Nothing here is a judgement call at runtime. Every mapping is declared in
schema/akn-registry.json, and an unmapped input yields "none" rather than a guess.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

REGISTRY_DEFAULT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "schema", "akn-registry.json"
)

# Basis values. These are recorded per record so a reader can tell WHY an identifier
# looks the way it does — or why it is absent.
BASIS_AKN4UN = "akn4un"      # UN body; country slot "un", organ in the author slot
BASIS_AKN4EU = "akn4eu"      # EU institution; country slot "eu"
BASIS_ISO3166 = "iso3166"    # ordinary nation-state, alpha-2 from ISO 3166-1
BASIS_NONE = "none"          # NO conformant code exists — structural, akn_uri MUST be null
BASIS_UNMAPPED = "unmapped"  # the registry does not cover this yet — a GAP, akn_uri null

# 'none' and 'unmapped' both yield a null URI but mean opposite things, and collapsing
# them would hide the only one you can act on:
#
#   none      The ISA, ITLOS, the ATS Secretariat and CCAMLR have no ISO 3166 code and no
#             published AKN profile covers them. Nothing we do fixes this. It is a
#             permanent, declared property of the body, recorded once in the registry.
#   unmapped  We simply have not written the mapping — an unlisted issuing authority, or a
#             document_type not yet translated to an AKN doctype. This is our backlog.
#
# A corpus can honestly ship with 'none' records forever. 'unmapped' should trend to zero,
# and validate_corpus.py can be told to hold you to that.
DECLINED_BASES = (BASIS_NONE, BASIS_UNMAPPED)
VALID_BASES = (BASIS_AKN4UN, BASIS_AKN4EU, BASIS_ISO3166, BASIS_NONE, BASIS_UNMAPPED)

# Work-level grammar we emit and validate against:
#   /akn/<country>/<doctype>[/<subtype>][/<author>]/<date>/<number>
# Country is 2 alpha (ISO 3166-1) optionally with an ISO 3166-2 subdivision suffix.
AKN_WORK_RE = re.compile(
    r"^/akn/"
    r"(?P<country>[a-z]{2}(?:-[a-z0-9]{1,3})?)/"
    r"(?P<doctype>[a-zA-Z][a-zA-Z0-9]*)"
    r"(?:/(?P<rest>[A-Za-z0-9._\-/]+))?"
    r"/(?P<date>\d{4}(?:-\d{2}-\d{2})?)"
    r"/(?P<number>[A-Za-z0-9._\-]+)$"
)

ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
YEAR_RE = re.compile(r"^\d{4}$")


class MintError(ValueError):
    """Raised only for malformed registries or malformed output — never for 'no code exists',
    which is a legitimate result and returns basis 'none' instead."""


def load_registry(path: str = REGISTRY_DEFAULT) -> dict:
    with open(path, encoding="utf-8") as fh:
        return _index(json.load(fh), path)


def _index(reg: dict, path: str = "<inline>") -> dict:
    """Validate and index a registry. Split out from load_registry so the selftest exercises
    the identical code path — a selftest that skipped validation would be testing a registry
    shape that can never occur in production."""
    for key in ("alpha3_to_alpha2", "authorities", "doctypes"):
        if key not in reg:
            raise MintError(f"registry {path} is missing required key {key!r}")
        # "$"-prefixed keys are documentation ($comment, $unmapped_note). Strip them so a
        # note can never be mistaken for a mapping.
        if isinstance(reg[key], dict):
            reg[key] = {k: v for k, v in reg[key].items() if not k.startswith("$")}
    for name, entry in reg["authorities"].items():
        basis = entry.get("basis")
        if basis not in VALID_BASES:
            raise MintError(f"authority {name!r} has invalid basis {basis!r}")
        if basis == BASIS_NONE and entry.get("country"):
            raise MintError(
                f"authority {name!r} declares basis 'none' but also a country code "
                f"{entry['country']!r} — that combination is exactly the fabrication this "
                f"module exists to prevent"
            )
        if basis != BASIS_NONE and not entry.get("country"):
            raise MintError(f"authority {name!r} has basis {basis!r} but no country code")

    # Case-insensitive doctype index, built once. Collisions that differ only by case would
    # make lookup order-dependent, so they are an error rather than a coin toss.
    ci = {}
    for k, v in reg["doctypes"].items():
        lk = k.lower()
        if lk in ci and ci[lk] != v:
            raise MintError(
                f"doctype {k!r} collides case-insensitively with another entry mapping to a "
                f"different result — resolve it in the registry rather than leaving lookup "
                f"dependent on dict order"
            )
        ci[lk] = v
    reg["_doctypes_ci"] = ci
    return reg


def _match_authority(meta: dict, reg: dict):
    """Resolve the issuing body to (country, basis, author_slot, reason).

    Matching is on issuing_authority first (the body that MADE the instrument), because
    jurisdiction alone cannot distinguish a UN treaty from an ISA regulation — in this
    portfolio both carry jurisdiction 'international'.
    """
    authority = (meta.get("issuing_authority") or "").strip()
    juris = (meta.get("jurisdiction") or "").strip()

    for name, entry in reg["authorities"].items():
        for pat in entry.get("match", []):
            if re.search(pat, authority, re.IGNORECASE) or re.search(pat, juris, re.IGNORECASE):
                return (
                    entry.get("country"),
                    entry["basis"],
                    entry.get("author"),
                    entry.get("reason", ""),
                )

    # Fall back to a plain nation-state code. Note the guard: 'international' and
    # 'international/UN' are NOT country codes and must never fall through to here.
    key = juris.upper()
    if key in reg["alpha3_to_alpha2"]:
        return reg["alpha3_to_alpha2"][key], BASIS_ISO3166, None, ""

    # Not in the registry at all. That is a GAP in our mapping, not a statement that no
    # code exists — only the registry may declare the latter, and only deliberately.
    return (
        None,
        BASIS_UNMAPPED,
        None,
        f"issuing authority {authority!r} (jurisdiction {juris!r}) is not in the AKN "
        f"registry; add it there, declaring basis 'none' if the body genuinely has no code",
    )


def _doctype(meta: dict, reg: dict):
    """Case-insensitive: the same concept appears as 'Act' in one corpus and 'act' in another,
    and a registry that missed 69 records purely on capitalisation would be reporting our own
    formatting as a property of the law."""
    dt = (meta.get("document_type") or "").strip()
    entry = reg["doctypes"].get(dt) or reg["_doctypes_ci"].get(dt.lower())
    if not entry:
        return None, None, f"document_type {dt!r} is not mapped in the AKN registry"
    return entry["doctype"], entry.get("subtype"), ""


def _declared_lang(meta: dict) -> str:
    """The record's own language tag, which may be BCP 47 with a script or region subtag
    ('zh-Hant', 'zh-Hans', 'pt-BR'), not just a bare ISO 639-1 code."""
    return (meta.get("language") or "").strip().lower()


def _strip_lang_suffix(value: str, meta: dict):
    """Remove a trailing language tag from version_id or corpus_id.

    THIS IS THE FRBR FIX. Records in this portfolio encode the language in the identifier
    ('1972-03-29-fr', 'bbnj-agreement-2023-ar', '2026-01-01_de'). Akoma Ntoso does not:
    language is a property of the EXPRESSION, and all language versions of one instrument
    share a single Work URI. Left alone, the Arabic and Spanish texts of one treaty would
    get two different Work identifiers — a claim that they are different instruments.

    The suffix is only stripped when it matches the record's OWN declared `language`, so
    this reads metadata rather than pattern-matching hopefully. An unverifiable suffix is
    reported, not guessed at.
    """
    lang = _declared_lang(meta)
    if not lang:
        return value, None, ""
    # Match the declared tag EXACTLY rather than guessing at a shape. A shape-based pattern
    # ([A-Za-z]{2,3}) silently missed every BCP 47 tag with a subtag — 'zh-Hant', 'pt-BR' —
    # and would also have happily stripped a real trailing token that merely looked like a
    # language code.
    for sep in ("-", "_"):
        suffix = sep + lang
        if value.lower().endswith(suffix) and len(value) > len(suffix):
            return value[: -len(suffix)], lang, ""
    return value, None, ""


def _date(meta: dict):
    """AKN wants the Work date. version_id is a date in this corpus pattern; a bare year is
    accepted because some instruments are identified only by year."""
    v = str(meta.get("version_id") or "").strip()
    if ISO_DATE_RE.match(v) or YEAR_RE.match(v):
        return v, ""
    stem, _lang, _ = _strip_lang_suffix(v, meta)
    if ISO_DATE_RE.match(stem) or YEAR_RE.match(stem):
        return stem, ""
    return None, (
        f"version_id {v!r} is not an ISO date or year (and any trailing tag does not match "
        f"the record's declared language {_declared_lang(meta)!r}), so no AKN Work date "
        f"can be derived"
    )


def _number(meta: dict):
    """Last segment of corpus_id, with any language tag removed so language variants of one
    instrument collapse onto a single Work. AKN permits an alphanumeric number slot, and
    corpus_id is stable and unique by construction, so this is deterministic rather than
    parsed out of free-text citations."""
    cid = (meta.get("corpus_id") or "").strip().strip("/")
    if not cid:
        return None, "corpus_id is empty"
    seg = cid.split("/")[-1]
    seg, _lang, _ = _strip_lang_suffix(seg, meta)
    seg = re.sub(r"[^A-Za-z0-9._\-]", "-", seg).strip("-")
    if not seg:
        return None, f"corpus_id {cid!r} yields no usable number segment"
    return seg, ""


def _expression_lang(meta: dict, reg: dict):
    """AKN Expression URIs use ISO 639-2 alpha-3 ('eng', 'fra', 'ara'); our records carry
    ISO 639-1, sometimes with a BCP 47 subtag.

    CAUTION, and it is a real limitation rather than a rounding error: ISO 639-2 has no way
    to express a script or region subtag. Traditional and Simplified Chinese are both 'zho';
    Brazilian and European Portuguese are both 'por'. Two records that differ only by script
    therefore produce the SAME Expression URI. That is a collision, not a merge, and
    check_collisions() below exists to make it fail loudly rather than quietly overwrite.
    """
    lang = _declared_lang(meta)
    if not lang:
        return None, "record has no `language`, so no Expression URI can be built"
    primary = lang.split("-")[0].split("_")[0]
    if len(primary) == 3:
        return primary, ""
    code = reg.get("lang2_to_lang3", {}).get(primary)
    if not code:
        return None, f"language {lang!r} is not in the registry's lang2_to_lang3 map"
    return code, ""


def check_collisions(records):
    """records: iterable of (identity, work_uri, expression_uri).

    Returns a list of error strings. Two DIFFERENT records sharing an Expression URI means
    the identifier is not identifying — most often a script/region variant flattened by
    ISO 639-2 (zh-Hant vs zh-Hans -> zho). Surfacing it is the point: an identifier scheme
    that silently maps two texts onto one name is worse than no identifier at all.

    Note that a shared WORK URI is expected and correct — that is exactly what language
    versions of one instrument should do.
    """
    seen = {}
    errs = []
    for ident, _work, expr in records:
        if not expr:
            continue
        if expr in seen:
            errs.append(
                f"Expression URI collision: {seen[expr]!r} and {ident!r} both resolve to "
                f"{expr!r} — ISO 639-2 cannot distinguish their language subtags, so this "
                f"identifier does not identify"
            )
        else:
            seen[expr] = ident
    return errs


def mint(meta: dict, reg: dict):
    """Return (work_uri, expression_uri, basis, note).

    Both URIs are None whenever basis is 'none' or 'unmapped'. The note always says why —
    it is never left empty on a decline, because an unexplained absence is indistinguishable
    from an oversight.

    The Work URI is shared by every language version of an instrument; the Expression URI
    appends the ISO 639-2 language. That is what makes the Arabic and Spanish texts of one
    treaty resolve as one instrument rather than two.
    """
    country, basis, author, reason = _match_authority(meta, reg)
    if basis in DECLINED_BASES:
        return None, None, basis, reason

    # Past this point the body HAS a code, so any remaining failure is a gap in our
    # mapping rather than a fact about the world — hence 'unmapped', never 'none'.
    doctype, subtype, err = _doctype(meta, reg)
    if err:
        return None, None, BASIS_UNMAPPED, err
    date, err = _date(meta)
    if err:
        return None, None, BASIS_UNMAPPED, err
    number, err = _number(meta)
    if err:
        return None, None, BASIS_UNMAPPED, err

    parts = ["/akn", country, doctype]
    if subtype:
        parts.append(subtype)
    if author:
        parts.append(author)
    parts += [date, number]
    work = "/".join(parts)

    if not AKN_WORK_RE.match(work):
        raise MintError(
            f"minted URI {work!r} does not match the AKN Work grammar — refusing to emit a "
            f"malformed identifier"
        )

    lang3, err = _expression_lang(meta, reg)
    expression = None if err else f"{work}/{lang3}"
    return work, expression, basis, ""


def check(uri, basis, note):
    """Validate an already-recorded triple. Returns a list of error strings (empty == OK).

    This is the fail-closed half: it is what stops a record drifting into a state the
    minting path would never have produced.
    """
    errs = []
    if basis not in VALID_BASES:
        errs.append(f"akn_uri_basis {basis!r} is not one of {VALID_BASES}")
        return errs
    if basis in DECLINED_BASES:
        if uri:
            errs.append(f"akn_uri_basis is {basis!r} but akn_uri is set to {uri!r}")
        if not (note or "").strip():
            errs.append(
                f"akn_uri_basis is {basis!r} but akn_uri_note is empty — a decline must state "
                f"its reason, otherwise it is indistinguishable from an oversight"
            )
        return errs
    if not uri:
        errs.append(f"akn_uri_basis is {basis!r} but akn_uri is empty")
        return errs
    m = AKN_WORK_RE.match(uri)
    if not m:
        errs.append(f"akn_uri {uri!r} does not match the AKN Work grammar")
        return errs
    country = m.group("country").split("-")[0]
    if basis == BASIS_AKN4UN and country != "un":
        errs.append(f"basis 'akn4un' requires country slot 'un', found {country!r}")
    if basis == BASIS_AKN4EU and country != "eu":
        errs.append(f"basis 'akn4eu' requires country slot 'eu', found {country!r}")
    if basis == BASIS_ISO3166 and country in ("un", "eu"):
        errs.append(
            f"country {country!r} is a reserved code, not an ordinary ISO 3166-1 country — "
            f"use basis 'akn4un'/'akn4eu'"
        )
    return errs


def _selftest():
    reg = {
        "alpha3_to_alpha2": {"USA": "us", "LUX": "lu", "AUS": "au"},
        "authorities": {
            "un-ga": {
                "match": [r"United Nations General Assembly"],
                "country": "un",
                "author": "un-ga",
                "basis": BASIS_AKN4UN,
            },
            "isa": {
                "match": [r"International Seabed Authority"],
                "basis": BASIS_NONE,
                "reason": "the ISA is an autonomous body established by UNCLOS, not a UN organ; "
                          "it has no ISO 3166 code and no published AKN profile covers it",
            },
            "eu": {
                "match": [r"European (Parliament|Commission|Council|Union)"],
                "country": "eu",
                "basis": BASIS_AKN4EU,
            },
        },
        "doctypes": {
            "treaty": {"doctype": "doc", "subtype": "treaty"},
            "statute": {"doctype": "act"},
            "isa_regulation": {"doctype": "act", "subtype": "regulation"},
        },
        "lang2_to_lang3": {"en": "eng", "fr": "fra", "es": "spa", "ar": "ara"},
    }
    reg = _index(reg)

    # 1. UN treaty -> AKN4UN, organ in the author slot.
    uri, expr, basis, note = mint(
        {
            "corpus_id": "un/treaty/ost-1967",
            "version_id": "1967-01-27",
            "jurisdiction": "international",
            "issuing_authority": "United Nations General Assembly",
            "document_type": "treaty",
            "language": "en",
        },
        reg,
    )
    assert uri == "/akn/un/doc/treaty/un-ga/1967-01-27/ost-1967", uri
    assert expr == "/akn/un/doc/treaty/un-ga/1967-01-27/ost-1967/eng", expr
    assert basis == BASIS_AKN4UN and note == "", (basis, note)
    assert check(uri, basis, note) == []

    # 2. Ordinary nation-state -> plain ISO 3166-1 alpha-2.
    uri, expr, basis, note = mint(
        {
            "corpus_id": "nat/usa/space-resources-2015",
            "version_id": "2015-11-25",
            "jurisdiction": "USA",
            "issuing_authority": "United States Congress",
            "document_type": "statute",
            "language": "en",
        },
        reg,
    )
    assert uri == "/akn/us/act/2015-11-25/space-resources-2015", uri
    assert basis == BASIS_ISO3166, basis

    # 3. THE POINT OF THIS MODULE: an IGO with no code mints nothing, and says why.
    uri, expr, basis, note = mint(
        {
            "corpus_id": "isa/regulation/exploration-nodules",
            "version_id": "2013-07-25",
            "jurisdiction": "international",
            "issuing_authority": "International Seabed Authority",
            "document_type": "isa_regulation",
        },
        reg,
    )
    assert uri is None, uri
    assert basis == BASIS_NONE, basis
    assert "no ISO 3166" in note or "autonomous body" in note, note
    assert check(uri, basis, note) == []

    # 4. 'international' must NEVER fall through to a country code. An unlisted body is a
    #    registry GAP ('unmapped'), not a claim that no code exists ('none') — only the
    #    registry may make that claim, and only on purpose.
    uri, expr, basis, note = mint(
        {
            "corpus_id": "x/y/z",
            "version_id": "2020-01-01",
            "jurisdiction": "international",
            "issuing_authority": "Some Unlisted Treaty Body",
            "document_type": "treaty",
        },
        reg,
    )
    assert uri is None and basis == BASIS_UNMAPPED, (uri, basis)
    assert note, "a decline with no reason would be an oversight in disguise"

    # 4b. A body that DOES have a code but an unmapped document_type is also a gap,
    #     never 'none' — otherwise our own backlog would masquerade as a fact of the world.
    uri, expr, basis, note = mint(
        {
            "corpus_id": "un/x/y",
            "version_id": "2020-01-01",
            "jurisdiction": "international",
            "issuing_authority": "United Nations General Assembly",
            "document_type": "some-type-we-have-not-mapped",
        },
        reg,
    )
    assert uri is None and basis == BASIS_UNMAPPED, (uri, basis)
    assert "not mapped" in note, note

    # 4c. THE FRBR CASE: two language versions of ONE instrument must share a Work URI and
    #     differ only at the Expression. Language lives in version_id/corpus_id in this
    #     portfolio; AKN puts it on the Expression.
    base = {
        "corpus_id": "un/treaty/bbnj-2023",
        "jurisdiction": "international",
        "issuing_authority": "United Nations General Assembly",
        "document_type": "treaty",
    }
    ar_w, ar_e, ar_b, _ = mint({**base, "corpus_id": "un/treaty/bbnj-2023-ar",
                                "version_id": "2023-06-19", "language": "ar"}, reg)
    es_w, es_e, es_b, _ = mint({**base, "corpus_id": "un/treaty/bbnj-2023-es",
                                "version_id": "2023-06-19-es", "language": "es"}, reg)
    assert ar_w == es_w == "/akn/un/doc/treaty/un-ga/2023-06-19/bbnj-2023", (ar_w, es_w)
    assert ar_e == ar_w + "/ara" and es_e == es_w + "/spa", (ar_e, es_e)
    assert ar_b == es_b == BASIS_AKN4UN

    # 4d. A trailing tag that does NOT match the declared language is left alone, not
    #     stripped on a hunch.
    w, _e, b, note = mint({**base, "corpus_id": "un/treaty/thing-2023-zz",
                           "version_id": "2023-06-19", "language": "en"}, reg)
    assert w.endswith("/thing-2023-zz"), w

    # 4e. Case-insensitive document_type: 'Treaty' and 'treaty' are the same concept.
    w2, _e2, b2, _n2 = mint({**base, "corpus_id": "un/treaty/x-2023",
                             "version_id": "2023-06-19", "language": "en",
                             "document_type": "Treaty"}, reg)
    assert w2 == "/akn/un/doc/treaty/un-ga/2023-06-19/x-2023", w2

    # 5. check() must fail closed on every inconsistent combination.
    assert check("/akn/un/doc/treaty/un-ga/1967-01-27/ost", BASIS_NONE, "why") != []
    assert check("/akn/un/doc/treaty/un-ga/1967-01-27/ost", BASIS_UNMAPPED, "why") != []
    assert check(None, BASIS_NONE, "") != []                      # decline with no reason
    assert check(None, BASIS_UNMAPPED, "") != []                  # ditto
    assert check(None, BASIS_ISO3166, "") != []                   # basis claims a URI, none present
    assert check("not-a-uri", BASIS_ISO3166, "") != []            # malformed
    assert check("/akn/us/act/2015-11-25/x", BASIS_AKN4UN, "") != []   # basis/country mismatch
    assert check("/akn/un/doc/treaty/un-ga/1967-01-27/x", BASIS_ISO3166, "") != []  # reserved code
    assert check(None, "made-up-basis", "x") != []

    # 6. A malformed registry is an error, not a silently-degraded mint.
    # Written to the OS temp dir, never beside the script: a selftest must not create
    # files inside the corpus it is checking.
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        for i, bad in enumerate((
            {"alpha3_to_alpha2": {}, "doctypes": {}},
            {"alpha3_to_alpha2": {}, "doctypes": {},
             "authorities": {"x": {"basis": "none", "country": "xa"}}},
            {"alpha3_to_alpha2": {}, "doctypes": {},
             "authorities": {"x": {"basis": "iso3166"}}},
        )):
            path = os.path.join(td, f"bad{i}.json")
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(bad, fh)
            try:
                load_registry(path)
            except MintError:
                pass
            else:
                raise AssertionError(f"malformed registry accepted: {bad}")

    print("akn selftest: OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--registry", default=REGISTRY_DEFAULT)
    ap.add_argument("--explain", metavar="METADATA_YAML",
                    help="mint for one record and print the result and reason")
    args = ap.parse_args()

    if args.selftest:
        _selftest()
        return 0

    if args.explain:
        try:
            import yaml
        except ImportError:
            print("PyYAML is required for --explain", file=sys.stderr)
            return 2
        with open(args.explain, encoding="utf-8") as fh:
            meta = yaml.safe_load(fh)
        uri, expr, basis, note = mint(meta, load_registry(args.registry))
        print(f"corpus_id : {meta.get('corpus_id')}")
        print(f"authority : {meta.get('issuing_authority')}")
        print(f"akn_uri   : {uri if uri else '(none — not minted)'}")
        print(f"basis     : {basis}")
        if note:
            print(f"reason    : {note}")
        return 0

    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
