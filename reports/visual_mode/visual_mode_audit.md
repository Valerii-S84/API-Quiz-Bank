# Visual Mode Audit

Generated: `2026-05-17`
Source: top-level `QuizBank/*.csv`; service template and `QuizBank/staging/` are excluded.
Prompt policy: `visual_prompt_policy_v4_visual_modes`

Total active items: `30974`

## Mode Distribution

| visual_mode | count |
|---|---:|
| target_action | `11100` |
| target_object | `8920` |
| context_only | `2908` |
| document_form | `3249` |
| symbolic_abstract | `4797` |

## Breakdown By Theme

| theme | target_action | target_object | context_only | document_form | symbolic_abstract |
|---|---:|---:|---:|---:|---:|
| T01 - Person / Identität / Familie | `883` | `1364` | `469` | `184` | `0` |
| T02 - Alltag / Zeit / Organisation | `597` | `1497` | `1245` | `62` | `0` |
| T03 - Wohnen / Haushalt / Verträge | `695` | `530` | `82` | `589` | `0` |
| T04 - Einkaufen / Geld / Konsum | `1343` | `325` | `22` | `161` | `0` |
| T05 - Essen / Gesundheit / Pflege | `1197` | `352` | `72` | `31` | `0` |
| T06 - Arbeit / Beruf / Karriere | `828` | `573` | `262` | `189` | `0` |
| T07 - Schule / Bildung / Weiterbildung | `1024` | `525` | `186` | `66` | `0` |
| T08 - Verkehr / Reise / Orientierung | `724` | `751` | `118` | `95` | `0` |
| T09 - Kommunikation / Telefon / Nachricht / E-Mail | `672` | `894` | `282` | `376` | `0` |
| T10 - Termine / Formulare / Behörden / Recht | `821` | `400` | `49` | `921` | `0` |
| T11 - Freizeit / Kultur / Service / soziale Kontakte | `1231` | `606` | `43` | `30` | `0` |
| T12 - Medien / Digitales / Nachrichten | `574` | `606` | `9` | `20` | `0` |
| T13 - Gesellschaft / Integration / Werte | `0` | `0` | `3` | `0` | `1224` |
| T14 - Umwelt / Nachhaltigkeit / Alltagssysteme | `0` | `0` | `1` | `9` | `1191` |
| T15 - Wirtschaft / Finanzen / Arbeitswelt | `511` | `497` | `51` | `198` | `0` |
| T16 - Wissenschaft / Technik / Forschung | `0` | `0` | `4` | `10` | `890` |
| T17 - Politik / Öffentlichkeit / Debatte | `0` | `0` | `10` | `300` | `600` |
| T18 - Analyse / Interpretation / Argumentation | `0` | `0` | `0` | `8` | `892` |

## Breakdown By Level

| level | target_action | target_object | context_only | document_form | symbolic_abstract |
|---|---:|---:|---:|---:|---:|
| A1 | `1282` | `1699` | `1660` | `196` | `0` |
| A2 | `2153` | `897` | `749` | `418` | `0` |
| B1 | `3010` | `838` | `411` | `665` | `620` |
| B2 | `3527` | `80` | `86` | `387` | `1185` |
| C1 | `0` | `3383` | `2` | `527` | `1496` |
| C2 | `1128` | `2023` | `0` | `1056` | `1496` |

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
