# Source URL audit — 2026-10-14T13:14:12Z

7 ok · 0 need review · 0 broken · 0 manual (declared unfetchable)

Advisory only — nothing was changed. A REDIRECT is not automatically wrong (sites move pages legitimately) but must be confirmed to still be the intended target. A title mismatch means the page may not be what the source claims to watch.

**A clean audit means no broken plumbing — not that every source watches the right page.** A URL resolving cleanly to a real but wrong page passes this tool UNLESS the source declares an `expect_contains` anchor (a stable string the right page must carry). Without an anchor, only a human reading the page catches a wrong-page.

**Anchor coverage: 6/7 sources declare an `expect_contains` anchor.** The remaining 1 are checked for plumbing only (HTTP status, redirects, title) and would NOT be caught resolving to a wrong page. Adding anchors to those is the durable fix for the resolving-but-wrong-page class (see the source-verification task).

## ✅ OK (7)

- **UN BBNJ — Text of the Agreement**
    - `https://www.un.org/bbnjagreement/en/bbnj-agreement/text-bbnj-agreement`
    - 'Text of the BBNJ Agreement' ✓ anchored
- **UN Treaty Collection — XXI.10 status**
    - `https://treaties.un.org/doc/Publication/MTDSG/Volume%20II/Chapter%20XXI/XXI-10.en.pdf`
    - ''
- **UN BBNJ — GA resolutions and decisions**
    - `https://www.un.org/bbnjagreement/en/bbnj-agreement/general-assembly-resolutions-and-decisions`
    - 'General Assembly resolutions and decisions' ✓ anchored
- **UN BBNJ — Preparatory Commission (first session docs)**
    - `https://www.un.org/bbnjagreement/en/meetings/preparatory-commission/documents/first-session`
    - 'First session (14-25 April 2025)' ✓ anchored
- **UN BBNJ — Preparatory Commission (third session docs)**
    - `https://www.un.org/bbnjagreement/en/third-session-23-march-2-april-2026`
    - 'Third session (23 March - 2 April 2026)' ✓ anchored
- **UN BBNJ — Notifications**
    - `https://www.un.org/bbnjagreement/en/notifications`
    - 'Notifications' ✓ anchored
- **UN BBNJ — Notifications under article 12 (MGR)**
    - `https://www.un.org/bbnjagreement/en/mgr-notifications`
    - 'Notifications under article 12' ✓ anchored

