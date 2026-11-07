# study-pack — kit 3 (contains the "Mapa" update, kit 2)

**FR, en bref.** Ce zip contient ta mise à jour Mapa (kit 2) plus cinq améliorations :
1. **Explications compréhensibles** dans le Resumo et la Revisão : bloc « Em palavras simples » obligatoire sur chaque définition, théorème, formule (et méthode), règles d'écriture strictes, et une relecture par un sous-agent « élève » qui n'a pas vu la source.
2. **Correction complète** de chaque exercice et de chaque exemple : « Como abordar » (la méthode et pourquoi), toutes les étapes avec leur justification, le résultat et une « Verificação ». Le générateur refuse un pack qui ne les a pas.
3. **Notes du tuteur** : enregistrées sur l'exercice ou le bloc dont parle la conversation (sinon sur le thème), affichées repliées **au début** de ce bloc, et enregistrées toutes seules quand l'élève le demande (« guarda isto numa nota », « écris une note », « save a note »).
4. **Page Testes** (optionnelle) : un test du jour à la fin de chaque jour du plan sur les thèmes de ce jour, des tests par blocs de thèmes et 1–2 tests généraux. On répond à tout, puis on corrige : correction complète de chaque question, score par thème, résultat enregistré.
5. **Plano adaptatif** : les séances non faites passent aux jours suivants, la charge suit le rythme réel de l'élève (4 derniers jours), un thème raté à un test (< 60 %) reçoit une révision de renfort le lendemain ; seules les révisions simples peuvent sauter. Un encadré dit ce qui a été ajusté, et « Plano original » montre le plan de départ.

## How to apply

1. Copy the contents of `study-pack/` over `study-pack/` in github.com/CAFEERON21br18/claude-skills (it replaces `SKILL.md` and the kit files, and adds the new ones).
2. Run `python3 kit/build.py kit/example && python3 kit/check.py kit/example/out` from `study-pack/` — must print ALL CHECKS PASSED (needs Python 3, Node/npm and Playwright; optional).
3. Storage keys are unchanged: existing packs keep their progress. A pack made with an older kit has to be brought up to the new quality gate when it is updated (that is the point: better explanations and full corrections).

## What changed in kit 3

| File | Change |
|---|---|
| `kit/build.py` | Quality gate (`validate_block`, `validate_solution`, `validate_exercise`): `explain` on def/thm/formula(/method), `method` on every example and key, ≥ 2 justified steps, full MCQ `why`, word floors per topic. Renders "Em palavras simples", "Como abordar", "Verificação". New page `testes` (`validate_tests`, `page_testes`), tab + tools; Plano gets "Plano original" and the adapt box; `kit` stamp → `study-pack kit 3`. |
| `kit/assets/testes.js` (new) | Tests: answer without feedback, "Terminar e corrigir" shows every full correction, score by topic, free answers self-assessed or graded by Claude, results in `<slug>-testes`. |
| `kit/assets/plano.js` | Live adaptation (carry-over, pace, extra reviews from tests, cut only plain reviews), daily-test sessions linked to the Testes page, "Plano original". |
| `kit/assets/core.js` | Tutor notes: target = the exercise/block of the chat, else the topic; shown folded at the top of the block; auto-saved when the student asks for a note; "Nota guardada em …" message. |
| `kit/assets/core.css` | Styles for the new parts (theme tokens only). |
| `kit/plan.py` | With `features.tests`, a 15-min `quiz` (daily test) at the end of each day but the last. |
| `kit/tests.py` (new) | Skeleton of `tests.json` from the plan (daily, topic blocks, mocks) with `need`; keeps written questions. |
| `kit/check.py` | Checks the Testes page, complete corrections on every exercise, tutor note at the top of its exercise, carry-over / extra review / "Plano original" on the Plano. |
| `kit/extract.py` | Round-trips `tests.json`. |
| `kit/questions.py` | New feature pill "Testes tipo e teste do dia (página extra)" at the end of the features list (order of the questions unchanged). |
| `kit/i18n.json` | Texts for all of the above in pt / fr / en. |
| `kit/SCHEMA.md`, `kit/README.md`, `SKILL.md` | New fields, quality gate, tests.json, adaptive plan; SKILL: Explanations and Complete corrections rules, comprehension check, Testes, adaptive Plano. |
| `kit/example/` | Demo pack rewritten to the new rules, with tests; its plan starts on 2 Nov 2026. |

## Not tested here

Account storage (`db`) and grading by Claude (`sample`) don't run in the headless browser; the browser fallback and everything else were tested.
