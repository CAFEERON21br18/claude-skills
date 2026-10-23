# Pack JSON — the only thing Claude writes

`build.py` turns these files into the four pages. Write them with a Python script (`json.dump`), never by hand, so LaTeX backslashes survive. Text fields use the small markdown below.

## Text fields (markdown-lite)

- Paragraphs separated by a blank line; `- ` lists; `1. ` lists; `**bold**` (never italics).
- Maths in `$…$` (inline) or `$$…$$` (display), KaTeX syntax. Write `<` and `>` normally (the build escapes them).
- `[Resumo 3](#r3)`, `[Revisão 3](#ch3)`, `[Sílabo 3](#t3)`: links between pages (same tab).
- `[[3]]` or `[[3|text]]`: dotted recall link to topic 3 on the same page.

## pack.json

```json
{
 "slug": "cdi",                      // storage prefix → "cdi-" (localStorage + db docs). Never change it on update.
 "course": "Cálculo Diferencial e Integral I",
 "short": "CDI-I", "school": "IST", "lang": "pt",          // pt | fr | en
 "exam": {"label": "1.º Teste", "date": "2026-11-06", "time": "18:00"},
 "theme": "focus",                   // focus | black-orange | yellow-white-orange | yellow-white-blue | darkblue-lightblue | black-pink | {custom object, same keys as themes.json}
 "font": "Atkinson Hyperlegible",    // Atkinson Hyperlegible | Lexend | OpenDyslexic | IBM Plex Sans | any Google Font name
 "features": {"sidebar": true, "focus": true, "history": true, "progress": true, "countdown": true,
              "recall": true, "review_only": true, "calc": true, "tutor": true, "plan": true},
 "exercise": {"format": ["lesson-style"], "source": "mine|mix|yours", "count": 5},   // count: number or "all"
 "urls": {"silabo": "", "resumo": "", "revisao": "", "plano": ""},   // artifact URLs; "" until published
 "storage": {"prefix": "cdi-", "docs": {"revisao": "revisao", "plano": "plano"}, "ls": {"revisao": "cdi-revisao-v1"}},  // only for packs made before the kit: keep their old keys
 "plan": {"start": "2026-10-24", "hours": "auto", "busy": {"2026-10-27": {"hours": 1, "note": "Exame de IEI às 10:30"}}, "weights": {"3": 1.5}, "hours_note": "2h nos dias úteis, 3h ao fim-de-semana"},
 "topics": [{"n": 1, "name": "Reais, módulos e indução", "meta": "Aula 1"}],
 "sources": ["Notion › Ruben › IST › CDI: Aulas 1–11"]
}
```

## topics/&lt;n&gt;.json

```json
{
 "n": 1,
 "syllabus": ["Axiomas de corpo e de ordem de $\\mathbb R$", "…"],          // 2–6 bullets, ≤ 12 words each
 "resumo":   [BLOCK, …],        // full explanation (Resumo)
 "examples": [EXAMPLE, …],      // ≥ 3 (Resumo)
 "lesson":   [BLOCK, …],        // short lesson (Revisão)
 "worked":   EXAMPLE,           // one step-by-step example (Revisão)
 "exercises":[EXERCISE, …],     // Revisão
 "shortage": "Só há 2 exercícios teus neste tópico."   // optional one-line notice
}
```

**BLOCK** `{"kind": "p|def|thm|formula|method|trap|bookerr|note", "title": "…", "body": "markdown", "plot": "x^2-2"}`
(`plot` optional: adds "Ver no gráfico" when the calculator is on. `bookerr` = red "Gralha no livro" box.)

**EXAMPLE** `{"title", "origin", "statement", "steps": [STEP…], "answer", "plot"?, "reconstructed"?: true}`

**STEP** `{"do": "…", "why": "…", "trap"?: "…", "by_claude"?: true, "flag"?: {"text": "what looks wrong", "fix": "corrected working"}}`

**EXERCISE**
```json
{"id": "e1-3", "type": "mcq|tf|free", "origin": "Ficha 3, ex. 2 | Course, sheet 1, ex. 4 | new",
 "q": "statement",
 "options": ["A", "B", "C", "D"],          // mcq: exactly 4
 "why": ["why A…", "…", "…", "…"],          // mcq: 4 (tf: 2) — each wrong one names the typical mistake
 "correct": 0,                              // mcq 0..3 ; tf 0 = true, 1 = false
 "gate": true,                              // calculation question: "Resolve no papel primeiro" + "Já resolvi — mostrar opções"
 "free_too": true,                          // also show the free-answer correction box under the options
 "layout": "two",                           // optional: options in two columns (only short, non-maths options)
 "key": {"steps": [STEP…], "answer": "…"},
 "plot": "…", "reconstructed": true}
```

- `origin: "new"` shows "Novo". Never label an invented exercise or example with a course source.
- Ids: `e<topic>-<k>`. On update, the same exercise (same sheet + number) keeps its id; new ones take the next numbers.

## plan.json

Made by `plan.py` (never by hand on a new plan). On update, keep the dated sessions as they are (ticks are keyed by date + index); only change texts and counts.
