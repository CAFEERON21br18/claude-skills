# study-pack kit

The fixed generator behind the `study-pack` skill. Same options ⇒ same pages for every course.

| File | What it does |
|---|---|
| `questions.py` | The personalization form (always the same questions, same order, themes shown with their colors). `--text` for the plain-text fallback. |
| `SCHEMA.md` | The JSON Claude writes (`pack.json`, `topics/<n>.json`). |
| `plan.py` | Makes `plan.json` (first pass, reviews at +1/+3/+7 days, mixed test the day before, ~10 % free). |
| `build.py` | Builds `silabo.html`, `resumo.html`, `revisao.html`, `plano.html` from the JSON. Stops on schema errors. |
| `check.py` | Render check (Playwright): overflow, clipped maths, KaTeX errors, JS errors, fixed header and tool order, interactions. Must pass before publishing. |
| `extract.py` | Update mode: rebuilds the JSON from published kit pages (lossless round trip). |
| `check_contrast.py` | Contrast check for the themes or a custom theme. |
| `themes.json` · `i18n.json` | 6 themes (light + dark tokens) · interface text in pt / fr / en. |
| `assets/` | The one stylesheet and the scripts (layout taken from the CDI pack). |
| `example/` | A 2-topic demo pack: `python3 plan.py example && python3 build.py example && python3 check.py example/out --shots`. |

Maths: KaTeX 0.16.9 (fonts embedded as data URIs, since artifacts only load scripts from cdnjs), auto-render + copy-tex. Graph calculator: math.js 12.4.1.
