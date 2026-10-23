#!/usr/bin/env python3
"""study-pack kit — the personalization questions, always the same form in the same order.

    python3 questions.py --lang pt [--mine] [--calc] [--lesson-style] [--exam 2026-11-06] [--text]

Prints the HTML for the inline form (Visualizer show_widget, elicitation module). Pass it unchanged.
--mine          the user uploaded their own exercises (adds "source" and "All my exercises")
--calc          the course is calculation-heavy (adds the graph calculator question)
--lesson-style  a Notion page "lesson-style" was found (adds it as the first exercise format)
--exam          exam date found in the material (pre-fills the deadline)
--text          prints the plain-text fallback instead (numbered questions, theme colors as hex)
"""
import json, argparse, pathlib, html
KIT = pathlib.Path(__file__).resolve().parent

L = {
 'pt': {'title': 'Detalhes do pacote de estudo', 'skip': 'Saltar', 'go': 'Continuar', 'other': 'Outro',
        'q': ['Que tema de cores queres?', 'Que letra?', 'Que funções queres nas páginas?', 'Em que formato são os exercícios?',
              'De onde vêm os exercícios?', 'Quantos exercícios por tópico?', 'Em que língua?', 'Juntar uma calculadora gráfica?',
              'Juntar o chat tutor (perguntas e notas do que não percebeste)?', 'Fazer um plano de estudo?', 'Data do teste ou exame', 'Horas por dia'],
        'fonts': [('Atkinson Hyperlegible', 'a mais legível'), ('Lexend', 'leitura fluida'), ('OpenDyslexic', 'feita para dislexia'), ('IBM Plex Sans', 'clássica')],
        'feat': ['Barra lateral', 'Modo foco', 'Histórico', 'Progresso', 'Contagem decrescente', 'Links para tópicos anteriores', 'Só erradas'],
        'fmt': ['A minha página lesson-style', 'Como na fonte', 'Escolha múltipla', 'Resposta livre corrigida pelo Claude', 'Verdadeiro / falso'],
        'src': [('Só os meus', 'mine'), ('50/50 meus e teus', 'mix'), ('Os teus (curso + Claude)', 'yours')],
        'all': 'Todos os meus', 'yes': 'Sim', 'no': 'Não', 'auto': 'Decides tu', 'theme_other': 'Outro (descreve)'},
 'fr': {'title': "Détails du pack d'étude", 'skip': 'Passer', 'go': 'Continuer', 'other': 'Autre',
        'q': ['Quel thème de couleurs veux-tu ?', 'Quelle police ?', 'Quelles fonctions veux-tu dans les pages ?', 'Quel format pour les exercices ?',
              "D'où viennent les exercices ?", "Combien d'exercices par thème ?", 'Dans quelle langue ?', 'Ajouter une calculatrice graphique ?',
              "Ajouter le chat tuteur (questions et notes de ce que tu n'as pas compris) ?", "Faire un plan d'étude ?", "Date du test ou de l'examen", 'Heures par jour'],
        'fonts': [('Atkinson Hyperlegible', 'la plus lisible'), ('Lexend', 'lecture fluide'), ('OpenDyslexic', 'faite pour la dyslexie'), ('IBM Plex Sans', 'classique')],
        'feat': ['Barre latérale', 'Mode focus', 'Historique', 'Progression', 'Compte à rebours', 'Liens vers les thèmes précédents', 'Erreurs seulement'],
        'fmt': ['Ma page lesson-style', 'Comme dans la source', 'QCM', 'Réponse libre corrigée par Claude', 'Vrai / faux'],
        'src': [('Seulement les miens', 'mine'), ('50/50 les miens et les tiens', 'mix'), ('Les tiens (cours + Claude)', 'yours')],
        'all': 'Tous les miens', 'yes': 'Oui', 'no': 'Non', 'auto': 'Tu décides', 'theme_other': 'Autre (décris)'},
 'en': {'title': 'Study pack details', 'skip': 'Skip', 'go': 'Continue', 'other': 'Other',
        'q': ['Which color theme do you want?', 'Which font?', 'Which features do you want on the pages?', 'Which format for the exercises?',
              'Where should the exercises come from?', 'How many exercises per topic?', 'Which language?', 'Add a graph calculator?',
              "Add the tutor chat (questions, and notes of what you didn't get)?", 'Make a study plan?', 'Test or exam date', 'Hours per day'],
        'fonts': [('Atkinson Hyperlegible', 'most readable'), ('Lexend', 'smooth reading'), ('OpenDyslexic', 'made for dyslexia'), ('IBM Plex Sans', 'classic')],
        'feat': ['Sidebar', 'Focus mode', 'Question history', 'Progress', 'Exam countdown', 'Links to earlier topics', 'Missed only'],
        'fmt': ['My lesson-style page', 'As in the source', 'Multiple choice', 'Free answer graded by Claude', 'True / false'],
        'src': [('Mine only', 'mine'), ('50/50 mine and yours', 'mix'), ('Yours (course + Claude)', 'yours')],
        'all': 'All of mine', 'yes': 'Yes', 'no': 'No', 'auto': 'You decide', 'theme_other': 'Other (describe)'},
}
FEAT_KEYS = ['sidebar', 'focus', 'history', 'progress', 'countdown', 'recall', 'review_only']
FMT_KEYS = ['lesson-style', 'source', 'mcq', 'free', 'tf']
HEAD = '<svg viewBox="0 0 20 20" fill="currentColor"><path d="M11.586 2a1.5 1.5 0 0 1 1.06.44l2.914 2.914a1.5 1.5 0 0 1 .44 1.06V16.5a1.5 1.5 0 0 1-1.5 1.5h-9a1.5 1.5 0 0 1-1.492-1.347L4 16.5v-13A1.5 1.5 0 0 1 5.5 2zM5.5 3a.5.5 0 0 0-.5.5v13a.5.5 0 0 0 .5.5h9a.5.5 0 0 0 .5-.5V7h-2.5A1.5 1.5 0 0 1 11 5.5V3zm7.04 10.304a.5.5 0 0 1 .92.392c-.295.69-.871 1.304-1.66 1.304-.487 0-.892-.234-1.2-.574-.309.34-.713.574-1.2.574-.486 0-.892-.233-1.2-.574-.31.34-.714.574-1.2.574a.5.5 0 0 1 0-1c.212 0 .52-.18.74-.696l.034-.067a.5.5 0 0 1 .886.067c.221.516.528.696.74.696.213 0 .52-.18.74-.696l.035-.067a.5.5 0 0 1 .885.067c.22.516.527.696.74.696s.519-.18.74-.696m0-4a.5.5 0 0 1 .92.392c-.295.69-.871 1.304-1.66 1.304-.487 0-.892-.234-1.2-.574-.309.34-.713.574-1.2.574-.486 0-.892-.233-1.2-.574-.31.34-.714.574-1.2.574a.5.5 0 0 1 0-1c.212 0 .52-.18.74-.696l.034-.067a.5.5 0 0 1 .886.067c.221.516.528.696.74.696.213 0 .52-.18.74-.696l.035-.067a.5.5 0 0 1 .885.067c.22.516.527.696.74.696s.519-.18.74-.696M12 5.5a.5.5 0 0 0 .5.5h2.293L12 3.207z"/></svg>'
CARD = 'border-radius:12px; padding:12px 14px; display:flex; flex-direction:column; gap:8px; align-items:flex-start; text-align:left; min-width:150px; box-shadow:0 1px 2px rgba(0,0,0,0.04)'
e = lambda s: html.escape(str(s), quote=True)

def pill(v, label, on=False, other=False):
    return f'<button type="button" class="elicit-pill" data-value="{e(v)}"{" aria-pressed=\"true\"" if on else ""}{" data-other" if other else ""}>{e(label)}</button>'

def group(q, name, inner, multi=False, other_for=None):
    o = f'<input type="text" class="elicit-other" data-for="{name}" placeholder="…" hidden>' if other_for else ''
    return f'<div class="elicit-group"><label class="elicit-question">{e(q)}</label><div class="elicit-pills" data-name="{name}" data-multi="{"true" if multi else "false"}">{inner}</div>{o}</div>'

def html_form(a):
    S = L[a.lang]; T = json.load(open(KIT / 'themes.json', encoding='utf-8')); Q = S['q']; out = []
    cards = ''
    for k, t in T.items():
        if k.startswith('_'):
            continue
        c = t['light']; sw = ''.join(f'<span style="width:18px;height:18px;border-radius:5px;border:1px solid rgba(0,0,0,.12);background:{c[x]}"></span>' for x in ('band', 'bg', 'accent', 'accent2'))
        cards += f'<button type="button" class="elicit-pill" data-value="{k}" style="{CARD}"><span style="display:flex;gap:4px">{sw}</span><span style="font-size:13px;font-weight:500">{e(t["name"][a.lang].split(" (")[0])}</span>' + (f'<span style="font-size:11px;color:var(--text-muted)">{e(t["name"][a.lang].split("(")[1].rstrip(")"))}</span>' if '(' in t['name'][a.lang] else '') + '</button>'
    cards += f'<button type="button" class="elicit-pill" data-value="other" data-other style="{CARD}"><i class="ti ti-palette" style="font-size:18px" aria-hidden="true"></i><span style="font-size:13px;font-weight:500">{e(S["theme_other"])}</span></button>'
    out.append(group(Q[0], 'theme', cards, other_for='theme'))
    fonts = ''.join(f'<button type="button" class="elicit-pill" data-value="{e(f)}"{" aria-pressed=\"true\"" if i == 0 else ""} style="{CARD}"><span style="font-size:13px;font-weight:500">{e(f)}</span><span style="font-size:11px;color:var(--text-muted)">{e(d)}</span></button>' for i, (f, d) in enumerate(S['fonts']))
    fonts += pill('other', S['other'], other=True)
    out.append(group(Q[1], 'font', fonts, other_for='font'))
    out.append(group(Q[2], 'features', ''.join(pill(k, l, on=k in ('sidebar', 'focus', 'history', 'progress', 'countdown')) for k, l in zip(FEAT_KEYS, S['feat'])), multi=True))
    fmts = [(k, l) for k, l in zip(FMT_KEYS, S['fmt']) if k != 'lesson-style' or a.lesson_style]
    out.append(group(Q[3], 'exercise_format', ''.join(pill(k, l, on=(k == 'lesson-style' or (not a.lesson_style and k in ('mcq', 'free')))) for k, l in fmts), multi=True))
    if a.mine:
        out.append(group(Q[4], 'source', ''.join(pill(v, l, on=v == 'mix') for l, v in S['src'])))
    counts = ([pill('all', S['all'])] if a.mine else []) + [pill(n, n, on=n == '5') for n in ('3', '5', '8', '10')] + [pill('other', S['other'], other=True)]
    out.append(group(Q[5], 'per_topic', ''.join(counts), other_for='per_topic'))
    out.append(group(Q[6], 'language', pill('pt', 'Português', on=a.lang == 'pt') + pill('fr', 'Français', on=a.lang == 'fr') + pill('en', 'English', on=a.lang == 'en')))
    if a.calc:
        out.append(group(Q[7], 'graph_calc', pill('yes', S['yes'], on=True) + pill('no', S['no'])))
    out.append(group(Q[8], 'tutor', pill('yes', S['yes'], on=True) + pill('no', S['no'])))
    out.append(group(Q[9], 'plan', pill('yes', S['yes']) + pill('no', S['no'], on=True)))
    out.append(f'<div class="elicit-group"><label class="elicit-question">{e(Q[10])}</label><input type="date" class="elicit-date" data-name="deadline"{f" value=\"{e(a.exam)}\"" if a.exam else ""}></div>')
    out.append(group(Q[11], 'hours', pill('auto', S['auto'], on=True) + ''.join(pill(h, h + 'h') for h in ('1', '2', '3', '4')) + pill('other', S['other'], other=True), other_for='hours'))
    return (f'<h2 class="sr-only">{e(S["title"])}</h2><form class="elicit"><div class="elicit-header">{HEAD}<span>{e(S["title"])}</span></div><div class="elicit-body">{"".join(out)}</div>'
            f'<div class="elicit-footer"><button type="button" class="elicit-skip">{e(S["skip"])}</button><button type="button" class="elicit-submit">{e(S["go"])}</button></div></form>')

def text_form(a):
    S = L[a.lang]; T = json.load(open(KIT / 'themes.json', encoding='utf-8')); Q = S['q']; n = 1; out = []
    out.append(f'{n}. {Q[0]}')
    for i, (k, t) in enumerate([(k, t) for k, t in T.items() if not k.startswith('_')], 1):
        c = t['light']; out.append(f'   {i}) {t["name"][a.lang]} — {c["band"]} / {c["bg"]} / {c["accent"]} / {c["accent2"]}')
    out.append(f'   7) {S["theme_other"]}'); n += 1
    out.append(f'{n}. {Q[1]} ' + ' · '.join(f for f, _ in S['fonts']) + f' · {S["other"]}'); n += 1
    out.append(f'{n}. {Q[2]} ' + ' · '.join(S['feat'])); n += 1
    out.append(f'{n}. {Q[3]} ' + ' · '.join(l for k, l in zip(FMT_KEYS, S['fmt']) if k != 'lesson-style' or a.lesson_style)); n += 1
    if a.mine:
        out.append(f'{n}. {Q[4]} ' + ' · '.join(l for l, _ in S['src'])); n += 1
    out.append(f'{n}. {Q[5]} ' + ((S['all'] + ' · ') if a.mine else '') + '3 · 5 · 8 · 10'); n += 1
    out.append(f'{n}. {Q[6]} Português · Français · English'); n += 1
    if a.calc:
        out.append(f'{n}. {Q[7]} {S["yes"]} · {S["no"]}'); n += 1
    out.append(f'{n}. {Q[8]} {S["yes"]} · {S["no"]}'); n += 1
    out.append(f'{n}. {Q[9]} {S["yes"]} · {S["no"]} — {Q[10]}{": " + a.exam if a.exam else ""} — {Q[11]}: {S["auto"]} · 1h · 2h · 3h · 4h')
    return '\n'.join(out)

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--lang', default='pt', choices=['pt', 'fr', 'en'])
    ap.add_argument('--mine', action='store_true'); ap.add_argument('--calc', action='store_true')
    ap.add_argument('--lesson-style', action='store_true'); ap.add_argument('--exam', default='')
    ap.add_argument('--text', action='store_true')
    a = ap.parse_args()
    print(text_form(a) if a.text else html_form(a))
