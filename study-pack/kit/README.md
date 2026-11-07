# study-pack kit

The fixed generator behind the `study-pack` skill. Same options ⇒ same pages for every course.

| File | What it does |
|---|---|
| `questions.py` | The personalization form (always the same questions, same order, themes shown with their colors). `--text` for the plain-text fallback. |
| `SCHEMA.md` | The JSON Claude writes (`pack.json`, `topics/<n>.json`, `map.json`, `tests.json`) and the quality gate (explanations, complete corrections). |
| `plan.py` | Makes `plan.json` (first pass, reviews at +1/+3/+7 days, a daily test at the end of each day when Testes is on, mixed test the day before, ~10 % free). The Plano page then adapts it live to the student's pace and test results. |
| `tests.py` | Makes the skeleton of `tests.json` from the plan: daily tests, topic tests, full mock tests, with how many questions each needs. |
| `build.py` | Builds `silabo.html`, `resumo.html`, `revisao.html`, `testes.html`, `mapa.html`, `plano.html` (the last three optional) from the JSON. Stops on schema errors and on thin content (quality gate). |
| `check.py` | Render check (Playwright): overflow, clipped maths, KaTeX errors, JS errors, fixed header and tool order, interactions. Must pass before publishing. |
| `extract.py` | Update mode: rebuilds the JSON from published kit pages (lossless round trip). |
| `check_contrast.py` | Contrast check for the themes or a custom theme. |
| `themes.json` · `i18n.json` | 6 themes (light + dark tokens) · interface text in pt / fr / en. |
| `assets/` | The one stylesheet and the scripts (layout taken from the CDI pack). `testes.js`: tests answered first, corrected at the end, results saved and read by the Plano. `mapa.js` + `mapa.css`: the generic idea-map engine (kinds causal / prereq / process, layouts timeline / layers). |
| `example/` | A 2-topic demo pack (with a `prereq` / `layers` map of maths and its tests): `python3 build.py example && python3 check.py example/out --shots`. Its plan starts on 2 Nov 2026 (re-run `plan.py` and `tests.py` for new dates), so the adaptive plan has past days to show. |

Maths: KaTeX 0.16.9 (fonts embedded as data URIs, since artifacts only load scripts from cdnjs), auto-render + copy-tex. Graph calculator: math.js 12.4.1.
