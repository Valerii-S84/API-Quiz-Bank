# Visual Mode Examples

Generated: `2026-05-17`
Prompt policy: `visual_prompt_policy_v4_visual_modes`

## target_action

| item_id | theme | level | old behavior | new behavior | reason | stem |
|---|---|---|---|---|---|---|
| gmb_administrative_documents_bank_a2_expanded_v01_100_ad_001 | T10 | A2 | visual_target = einen Termin buchen | target_action / einen Termin buchen | direct_visual_answer | Bevor ich morgen zum Amt gehe, muss ich noch ___. |
| gmb_administrative_documents_bank_a2_expanded_v01_100_ad_002 | T10 | A2 | visual_target = den Termin bestätigen | target_action / den Termin bestätigen | direct_visual_answer | Damit mein Platz frei bleibt, muss ich heute noch ___. |
| gmb_administrative_documents_bank_a2_expanded_v01_100_ad_003 | T10 | A2 | visual_target = den Termin verschieben | target_action / den Termin verschieben | direct_visual_answer | Wenn ich morgen schon einen Arzttermin habe, muss ich ___. |
| gmb_administrative_documents_bank_a2_expanded_v01_100_ad_004 | T10 | A2 | visual_target = den Termin absagen | target_action / den Termin absagen | direct_visual_answer | Weil ich seit dem Morgen Fieber habe, muss ich ___. |
| gmb_administrative_documents_bank_a2_expanded_v01_100_ad_009 | T10 | A2 | visual_target = die Unterlagen kopieren | target_action / die Unterlagen kopieren | direct_visual_answer | Wenn das Amt ein Blatt behält, muss ich die Unterlagen noch ___. |

## target_object

| item_id | theme | level | old behavior | new behavior | reason | stem |
|---|---|---|---|---|---|---|
| gmb_administrative_legal_procedures_implicit_paraphrase_bank_c1_300_alpip_009 | T10 | C1 | visual_target = deutlich eingegrenzt werden soll | target_object / deutlich eingegrenzt werden soll | direct_visual_answer | Auch wenn Beteiligung betont wird, zeigt die Notiz, dass der Pfad fuer die Erklaerung _... |
| gmb_administrative_legal_procedures_implicit_paraphrase_bank_c1_300_alpip_010 | T10 | C1 | visual_target = deutlich erweitert werden soll | target_object / deutlich erweitert werden soll | direct_visual_answer | Auch wenn Ruhe betont wird, zeigt die Mail, dass der Pfad fuer die Erklaerung ___, weil... |
| gmb_administrative_legal_procedures_implicit_paraphrase_bank_c1_300_alpip_011 | T10 | C1 | visual_target = deutlich festgelegt werden soll | target_object / deutlich festgelegt werden soll | direct_visual_answer | Auch wenn Flexibilitaet betont wird, zeigt der Hinweis, dass der Pfad fuer die Erklaeru... |
| gmb_administrative_legal_procedures_implicit_paraphrase_bank_c1_300_alpip_012 | T10 | C1 | visual_target = deutlich offengehalten werden soll | target_object / deutlich offengehalten werden soll | direct_visual_answer | Auch wenn Verbindlichkeit betont wird, zeigt die Stellungnahme, dass der Pfad fuer die ... |
| gmb_administrative_legal_procedures_implicit_paraphrase_bank_c1_300_alpip_021 | T10 | C1 | visual_target = klar eingegrenzt werden soll | target_object / klar eingegrenzt werden soll | direct_visual_answer | Obwohl Offenheit betont wird, zeigt die Stellungnahme, dass die Vorgabe fuer die Begrue... |

## context_only

| item_id | theme | level | old behavior | new behavior | reason | stem |
|---|---|---|---|---|---|---|
| gmb_adjektivendungen_beginner_bank_a1_a2_210_adj_001 | T02 | A1 | visual_target = kleine | context_only / Kommentar | context_only_anchor | Im Gruppenchat wirkt der ___ Kommentar heute besonders sympathisch. |
| gmb_adjektivendungen_beginner_bank_a1_a2_210_adj_002 | T02 | A2 | visual_target = praktischer | context_only / Filter | context_only_anchor | Im Team sagt jeder, dass ein ___ Filter richtig stark ist. |
| gmb_adjektivendungen_beginner_bank_a1_a2_210_adj_003 | T02 | A2 | visual_target = starker | context_only / Trick | context_only_anchor | Beim Lernen merken wir schnell, dass kein ___ Trick hilft. |
| gmb_adjektivendungen_beginner_bank_a1_a2_210_adj_004 | T06 | A1 | visual_target = direkte | context_only / Pitch | context_only_anchor | In der Story klingt der ___ Pitch direkt ueberzeugend. |
| gmb_adjektivendungen_beginner_bank_a1_a2_210_adj_005 | T09 | A1 | visual_target = typischer | context_only / Titel | context_only_anchor | Im Reel kommt ein ___ Titel bei allen gut an. |

## document_form

| item_id | theme | level | old behavior | new behavior | reason | stem |
|---|---|---|---|---|---|---|
| gmb_administrative_documents_bank_a2_expanded_v01_100_ad_005 | T10 | A2 | visual_target = das Formular herunterladen | document_form / Formular | document_form_anchor | Bevor ich morgen losgehe, muss ich das Formular noch ___. |
| gmb_administrative_documents_bank_a2_expanded_v01_100_ad_006 | T10 | A2 | visual_target = das Formular ausdrucken | document_form / Formular | document_form_anchor | Wenn ich nur die Datei habe, muss ich das Formular noch ___. |
| gmb_administrative_documents_bank_a2_expanded_v01_100_ad_007 | T10 | A2 | visual_target = das Formular ausfüllen | document_form / Formular | document_form_anchor | Weil meine Adresse fehlt, muss ich das Formular noch ___. |
| gmb_administrative_documents_bank_a2_expanded_v01_100_ad_008 | T10 | A2 | visual_target = das Formular unterschreiben | document_form / Formular | document_form_anchor | Damit der Antrag gültig ist, muss ich das Formular noch ___. |
| gmb_administrative_documents_bank_a2_expanded_v01_100_ad_013 | T10 | A2 | visual_target = eine Kopie beilegen | document_form / Brief | document_form_anchor | Wenn ich den Brief heute schicke, muss ich noch ___. |

## symbolic_abstract

| item_id | theme | level | old behavior | new behavior | reason | stem |
|---|---|---|---|---|---|---|
| gmb_analysis_interpretation_argumentation_implicit_paraphrase_bank_c1_300_aiaip_001 | T18 | C1 | visual_target = klar eingegrenzt werden soll | symbolic_abstract / klar eingegrenzt werden soll | symbolic_abstract_anchor | Trotz offener Rahmung zeigt der Vermerk, dass der Deutungsrahmen des Essays ___, weil v... |
| gmb_analysis_interpretation_argumentation_implicit_paraphrase_bank_c1_300_aiaip_002 | T18 | C1 | visual_target = klar erweitert werden soll | symbolic_abstract / klar erweitert werden soll | symbolic_abstract_anchor | Trotz vorsichtiger Rahmung zeigt der Kommentar, dass der Deutungsrahmen des Essays ___,... |
| gmb_analysis_interpretation_argumentation_implicit_paraphrase_bank_c1_300_aiaip_003 | T18 | C1 | visual_target = klar festgelegt werden soll | symbolic_abstract / klar festgelegt werden soll | symbolic_abstract_anchor | Trotz behaupteter Offenheit zeigt die Passage, dass der Deutungsrahmen des Essays ___, ... |
| gmb_analysis_interpretation_argumentation_implicit_paraphrase_bank_c1_300_aiaip_004 | T18 | C1 | visual_target = klar offengehalten werden soll | symbolic_abstract / klar offengehalten werden soll | symbolic_abstract_anchor | Trotz versprochener Klarheit zeigt der Vermerk, dass der Deutungsrahmen des Essays ___,... |
| gmb_analysis_interpretation_argumentation_implicit_paraphrase_bank_c1_300_aiaip_005 | T18 | C1 | visual_target = deutlich eingegrenzt werden soll | symbolic_abstract / deutlich eingegrenzt werden soll | symbolic_abstract_anchor | Trotz betonter Transparenz zeigt der Kommentar, dass die Belegkette im Gutachten ___, w... |

## Article / Preposition Examples

| item_id | theme | level | old behavior | new behavior | reason | stem |
|---|---|---|---|---|---|---|
| gmb_artikel_sprint_bank_a1_b2_1000_as_001 | T09 | A1 | visual_target = der | context_only / Laptop | non_visual_answer_context_anchor | Heute ist ___ Laptop im Technik-Chat ein wichtiges Thema. |
| gmb_artikel_sprint_bank_a1_b2_1000_as_002 | T08 | A1 | visual_target = der | context_only / Bahnhof | non_visual_answer_context_anchor | Im Alltag bleibt ___ Bahnhof bei der Reiseplanung sehr relevant. |
| gmb_artikel_sprint_bank_a1_b2_1000_as_003 | T06 | A1 | visual_target = der | context_only / Vertrag | non_visual_answer_context_anchor | Gerade ist ___ Vertrag im Büroteam klar im Fokus. |
| gmb_artikel_sprint_bank_a1_b2_1000_as_004 | T02 | A1 | visual_target = der | context_only / Wecker | non_visual_answer_context_anchor | Am Morgen ist ___ Wecker im Tagesablauf schon präsent. |
| gmb_artikel_sprint_bank_a1_b2_1000_as_005 | T02 | A1 | visual_target = der | context_only / Schlüssel | non_visual_answer_context_anchor | Diese Woche ist ___ Schlüssel im Tagesablauf besonders wichtig. |
| gmb_akkusativ_dativ_bank_a1_b1_210_ad_001 | T02 | A1 | visual_target = für den | context_only / Arzt | non_visual_answer_context_anchor | Ich kaufe Blumen ___ Arzt. |
| gmb_akkusativ_dativ_bank_a1_b1_210_ad_002 | T02 | A1 | visual_target = für den | context_only / Arzt | non_visual_answer_context_anchor | Für die Sprechstunde bringe ich Blumen ___ Arzt. |
| gmb_akkusativ_dativ_bank_a1_b1_210_ad_003 | T07 | A1 | visual_target = für die | context_only / Lehrerin | non_visual_answer_context_anchor | Wir haben eine kleine Karte ___ Lehrerin. |
| gmb_akkusativ_dativ_bank_a1_b1_210_ad_004 | T07 | A1 | visual_target = für die | context_only / Lehrerin | non_visual_answer_context_anchor | Zum Abschied schreiben wir eine Karte ___ Lehrerin. |
| gmb_akkusativ_dativ_bank_a1_b1_210_ad_005 | T01 | A1 | visual_target = für das | context_only / Kind | non_visual_answer_context_anchor | Sie bestellt Saft ___ Kind. |
