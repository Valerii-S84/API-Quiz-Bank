# Visual Mode Audit

Generated: `2026-05-17`
Source: top-level `QuizBank/*.csv`; service template and `QuizBank/staging/` are excluded.
Prompt policy: `visual_prompt_policy_v4_visual_modes`

Total active items: `30974`

## Mode Distribution

| visual_mode | count |
|---|---:|
| target_action | `12805` |
| target_object | `9255` |
| context_only | `2908` |
| document_form | `882` |
| symbolic_abstract | `5124` |

## Breakdown By Theme

| theme | target_action | target_object | context_only | document_form | symbolic_abstract |
|---|---:|---:|---:|---:|---:|
| T01 - Person / Identität / Familie | `977` | `1454` | `469` | `0` | `0` |
| T02 - Alltag / Zeit / Organisation | `603` | `1553` | `1245` | `0` | `0` |
| T03 - Wohnen / Haushalt / Verträge | `927` | `530` | `82` | `357` | `0` |
| T04 - Einkaufen / Geld / Konsum | `1504` | `325` | `22` | `0` | `0` |
| T05 - Essen / Gesundheit / Pflege | `1228` | `352` | `72` | `0` | `0` |
| T06 - Arbeit / Beruf / Karriere | `896` | `694` | `262` | `0` | `0` |
| T07 - Schule / Bildung / Weiterbildung | `1082` | `533` | `186` | `0` | `0` |
| T08 - Verkehr / Reise / Orientierung | `778` | `792` | `118` | `0` | `0` |
| T09 - Kommunikation / Telefon / Nachricht / E-Mail | `912` | `904` | `282` | `126` | `0` |
| T10 - Termine / Formulare / Behörden / Recht | `1449` | `400` | `49` | `293` | `0` |
| T11 - Freizeit / Kultur / Service / soziale Kontakte | `1256` | `611` | `43` | `0` | `0` |
| T12 - Medien / Digitales / Nachrichten | `590` | `610` | `9` | `0` | `0` |
| T13 - Gesellschaft / Integration / Werte | `0` | `0` | `3` | `0` | `1224` |
| T14 - Umwelt / Nachhaltigkeit / Alltagssysteme | `0` | `0` | `1` | `0` | `1200` |
| T15 - Wirtschaft / Finanzen / Arbeitswelt | `603` | `497` | `51` | `106` | `0` |
| T16 - Wissenschaft / Technik / Forschung | `0` | `0` | `4` | `0` | `900` |
| T17 - Politik / Öffentlichkeit / Debatte | `0` | `0` | `10` | `0` | `900` |
| T18 - Analyse / Interpretation / Argumentation | `0` | `0` | `0` | `0` | `900` |

## Breakdown By Level

| level | target_action | target_object | context_only | document_form | symbolic_abstract |
|---|---:|---:|---:|---:|---:|
| A1 | `1435` | `1733` | `1660` | `9` | `0` |
| A2 | `2509` | `949` | `749` | `10` | `0` |
| B1 | `3646` | `845` | `411` | `18` | `624` |
| B2 | `3892` | `80` | `86` | `7` | `1200` |
| C1 | `0` | `3449` | `2` | `457` | `1500` |
| C2 | `1323` | `2199` | `0` | `381` | `1800` |

## High-Risk Examples

| item_id | theme | level | old behavior | new behavior | reason | stem |
|---|---|---|---|---|---|---|
| gmb_adjektivendungen_beginner_bank_a1_a2_210_adj_001 | T02 | A1 | visual_target = kleine | context_only / Kommentar | context_only_anchor | Im Gruppenchat wirkt der ___ Kommentar heute besonders sympathisch. |
| gmb_adjektivendungen_beginner_bank_a1_a2_210_adj_002 | T02 | A2 | visual_target = praktischer | context_only / Filter | context_only_anchor | Im Team sagt jeder, dass ein ___ Filter richtig stark ist. |
| gmb_adjektivendungen_beginner_bank_a1_a2_210_adj_003 | T02 | A2 | visual_target = starker | context_only / Trick | context_only_anchor | Beim Lernen merken wir schnell, dass kein ___ Trick hilft. |
| gmb_adjektivendungen_beginner_bank_a1_a2_210_adj_004 | T06 | A1 | visual_target = direkte | context_only / Pitch | context_only_anchor | In der Story klingt der ___ Pitch direkt ueberzeugend. |
| gmb_adjektivendungen_beginner_bank_a1_a2_210_adj_005 | T09 | A1 | visual_target = typischer | context_only / Titel | context_only_anchor | Im Reel kommt ein ___ Titel bei allen gut an. |
| gmb_adjektivendungen_beginner_bank_a1_a2_210_adj_006 | T09 | A1 | visual_target = beliebter | context_only / Stream | context_only_anchor | Bei uns im Kurs faellt kein ___ Stream sofort positiv auf. |
| gmb_adjektivendungen_beginner_bank_a1_a2_210_adj_007 | T02 | A2 | visual_target = kleine | context_only / Termin | context_only_anchor | Beim Treffen finden alle, dass der ___ Termin total passt. |
| gmb_adjektivendungen_beginner_bank_a1_a2_210_adj_008 | T02 | A1 | visual_target = praktischer | context_only / Post | context_only_anchor | Im Gruppenchat wirkt ein ___ Post heute besonders sympathisch. |
| gmb_adjektivendungen_beginner_bank_a1_a2_210_adj_009 | T02 | A1 | visual_target = starker | context_only / Trend | context_only_anchor | Im Team sagt jeder, dass kein ___ Trend richtig stark ist. |
| gmb_adjektivendungen_beginner_bank_a1_a2_210_adj_010 | T02 | A2 | visual_target = direkte | context_only / Plan | context_only_anchor | Beim Lernen merken wir schnell, dass der ___ Plan hilft. |
| gmb_adjektivendungen_beginner_bank_a1_a2_210_adj_011 | T06 | A1 | visual_target = typischer | context_only / Entwurf | context_only_anchor | In der Story klingt ein ___ Entwurf direkt ueberzeugend. |
| gmb_adjektivendungen_beginner_bank_a1_a2_210_adj_012 | T09 | A1 | visual_target = beliebter | context_only / Kanal | context_only_anchor | Im Reel kommt kein ___ Kanal bei allen gut an. |
| gmb_adjektivendungen_beginner_bank_a1_a2_210_adj_013 | T07 | A1 | visual_target = kleine | context_only / Hinweis | context_only_anchor | Bei uns im Kurs faellt der ___ Hinweis sofort positiv auf. |
| gmb_adjektivendungen_beginner_bank_a1_a2_210_adj_014 | T06 | A1 | visual_target = praktischer | context_only / Bericht | context_only_anchor | Beim Treffen finden alle, dass ein ___ Bericht total passt. |
| gmb_adjektivendungen_beginner_bank_a1_a2_210_adj_015 | T02 | A1 | visual_target = starker | context_only / Clip | context_only_anchor | Im Gruppenchat wirkt kein ___ Clip heute besonders sympathisch. |
| gmb_adjektivendungen_beginner_bank_a1_a2_210_adj_016 | T02 | A2 | visual_target = direkte | context_only / Hashtag | context_only_anchor | Im Team sagt jeder, dass der ___ Hashtag richtig stark ist. |
| gmb_adjektivendungen_beginner_bank_a1_a2_210_adj_017 | T09 | A1 | visual_target = typischer | context_only / Screenshot | context_only_anchor | Beim Lernen merken wir schnell, dass ein ___ Screenshot hilft. |
| gmb_adjektivendungen_beginner_bank_a1_a2_210_adj_018 | T09 | A1 | visual_target = beliebter | context_only / Satz | context_only_anchor | In der Story klingt kein ___ Satz direkt ueberzeugend. |
| gmb_adjektivendungen_beginner_bank_a1_a2_210_adj_019 | T02 | A1 | visual_target = kleine | context_only / Song | context_only_anchor | Im Reel kommt der ___ Song bei allen gut an. |
| gmb_adjektivendungen_beginner_bank_a1_a2_210_adj_020 | T09 | A1 | visual_target = praktischer | context_only / Laptop | context_only_anchor | Bei uns im Kurs faellt ein ___ Laptop sofort positiv auf. |
