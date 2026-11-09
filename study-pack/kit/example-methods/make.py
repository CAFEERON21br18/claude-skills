#!/usr/bin/env python3
"""Builds example-methods/: the bundled example pack with every method part on (test pack for build.py and check.py).

    python3 example-methods/make.py && python3 build.py example-methods && python3 check.py example-methods/out
"""
import json, pathlib, shutil

HERE = pathlib.Path(__file__).resolve().parent
EX = HERE.parent / 'example'


def tf(id, q, correct, why_t, why_f, method, do, why, answer, **kw):
    return {'id': id, 'type': 'tf', 'origin': 'new', 'q': q, 'correct': correct, 'why': [why_t, why_f],
            'key': {'method': method, 'steps': [{'do': do, 'why': why}], 'answer': answer}, **kw}


def free(id, q, method, steps, answer, **kw):
    return {'id': id, 'type': 'free', 'origin': 'new', 'q': q,
            'key': {'method': method, 'steps': [{'do': d, 'why': w} for d, w in steps], 'answer': answer}, **kw}


def example(title, statement, method, steps, answer):
    return {'title': title, 'origin': 'new', 'statement': statement, 'method': method,
            'steps': [{'do': d, 'why': w} for d, w in steps], 'answer': answer}


ABS = 'Desdobra-se o módulo em dois ramos com a regra $|u|<a\\Leftrightarrow -a<u<a$ e resolve-se cada desigualdade.'
IND = 'Prova por indução: verifica-se a base e depois mostra-se que $P(n)$ implica $P(n+1)$, usando a hipótese.'
GAU = 'Sistema linear: escreve-se a matriz aumentada e aplica-se Gauss até à escada, lendo depois as soluções.'
PRD = 'Produto de matrizes: cada entrada é linha da primeira vezes coluna da segunda, somando os produtos.'


def parts1():
    k = lambda i, a, b: tf(f'e1-k{i}', f'$|{a}|={b}$', 0 if abs(a) == b else 1, 'Verdadeiro: o módulo é a distância a zero, sempre positiva.', 'Falso: o módulo de um número negativo é o seu simétrico.',
                           'Módulo de um número: tira-se o sinal, porque o módulo mede distância a zero.', f'$|{a}|={abs(a)}$', 'Distância de um número a zero.', f'$|{a}|={abs(a)}$')
    return {
        'active_recall': {'questions': [{'q': 'O que diz a desigualdade triangular?', 'a': '$|x+y|\\le|x|+|y|$ para todos os reais $x,y$.'},
                                        {'q': 'Como se desdobra $|x|<a$?', 'a': '$-a<x<a$ (um só intervalo, «e»).'},
                                        {'q': 'E $|x|>a$?', 'a': '$x>a$ ou $x<-a$ (dois ramos, «ou»).'},
                                        {'q': 'Quais são os dois passos da indução?', 'a': 'Base $P(p)$ e hereditariedade $P(n)\\Rightarrow P(n+1)$.'}],
                          'keys': ['Módulo = distância a zero', '$|x|<a$: um intervalo; $|x|>a$: dois ramos', 'Indução: base + hereditariedade, usando a hipótese']},
        'spaced': {'quick': [{'q': '$|-3|$', 'a': '$3$'}, {'q': 'Resolve $|x|<2$', 'a': '$]-2,2[$'}, {'q': 'Resolve $|x|\\ge1$', 'a': '$x\\le-1$ ou $x\\ge1$'},
                             {'q': 'Passo da indução que usa a hipótese?', 'a': 'A hereditariedade.'}]},
        'kumon': [[k(1, -3, 3), k(2, 5, 5), k(3, -7, -7)],
                  [tf(f'e1-k2{i}', q, c, 'Verdadeiro: é a regra do módulo aplicada corretamente.', 'Falso: troca-se «e» por «ou» ou o sentido da desigualdade.',
                      'Inequação com módulo: identifica-se se é «menor» (um intervalo) ou «maior» (dois ramos).', d, 'Regra do módulo com $a>0$.', d)
                   for i, (q, c, d) in enumerate([('$|x|<1\\Leftrightarrow -1<x<1$', 0, '$-1<x<1$'), ('$|x|>2\\Leftrightarrow -2<x<2$', 1, '$x>2\\lor x<-2$'), ('$|x|\\le0\\Leftrightarrow x=0$', 0, '$x=0$')], 1)],
                  [free(f'e1-k3{i}', f'Resolve ${q}$.', ABS, [(s1, 'Regra do módulo com dois lados.'), (s2, 'Isolar $x$ em cada lado.')], ans)
                   for i, (q, s1, s2, ans) in enumerate([('|x-1|<3', '$-3<x-1<3$', '$-2<x<4$', '$]-2,4[$'), ('|x+2|\\le1', '$-1\\le x+2\\le1$', '$-3\\le x\\le-1$', '$[-3,-1]$'), ('|2x|<4', '$-4<2x<4$', '$-2<x<2$', '$]-2,2[$')], 1)]],
        'worked_examples': [{'example': example('Módulo com «menor»', 'Resolve $|x-3|<2$.', ABS, [('$-2<x-3<2$', 'Regra $|u|<a\\Leftrightarrow -a<u<a$.'), ('$1<x<5$', 'Somar 3 aos três membros.')], '$]1,5[$'),
                             'twin': free('e1-w1', 'Resolve $|x-4|<1$.', ABS, [('$-1<x-4<1$', 'Regra do módulo com «menor».'), ('$3<x<5$', 'Somar 4 aos três membros.')], '$]3,5[$')},
                            {'example': example('Módulo com «maior»', 'Resolve $|x+1|>3$.', ABS, [('$x+1>3\\ \\lor\\ x+1<-3$', 'Regra $|u|>a$: dois ramos.'), ('$x>2\\ \\lor\\ x<-4$', 'Subtrair 1 em cada ramo.')], '$]-\\infty,-4[\\cup]2,+\\infty[$'),
                             'twin': free('e1-w2', 'Resolve $|x+2|>1$.', ABS, [('$x+2>1\\ \\lor\\ x+2<-1$', 'Regra do módulo com «maior».'), ('$x>-1\\ \\lor\\ x<-3$', 'Subtrair 2 em cada ramo.')], '$]-\\infty,-3[\\cup]-1,+\\infty[$')}],
        'shuhari': {'shu': [free('e1-s1', 'Prova por indução que $1+2+\\dots+n=\\frac{n(n+1)}2$.', IND, [('Base: $1=\\frac{1\\cdot2}2$.', 'A fórmula vale para $n=1$.'), ('Somar $n+1$ à hipótese: $\\frac{n(n+1)}2+n+1=\\frac{(n+1)(n+2)}2$.', 'Usar a hipótese de indução.')], 'A fórmula vale para todo o $n\\ge1$.',
                                 hints=['Começa por $n=1$: os dois lados dão o mesmo?', 'Supõe a fórmula para $n$ e soma $n+1$ aos dois lados.'])],
                    'ha': [free('e1-s2', 'Prova por indução que $1+3+\\dots+(2n-1)=n^2$.', IND, [('Base: $1=1^2$.', 'A fórmula vale para $n=1$.'), ('$n^2+(2n+1)=(n+1)^2$.', 'Usar a hipótese e somar o termo seguinte.')], 'A soma dos $n$ primeiros ímpares é $n^2$.')],
                    'ri': [free('e1-s3', 'Descobre uma fórmula para $2+4+\\dots+2n$ e prova-a.', 'Experimenta valores pequenos, adivinha a fórmula e prova-a por indução (base + hereditariedade).', [('Para $n=1,2,3$: $2,6,12$, ou seja $n(n+1)$.', 'Testar casos pequenos sugere a fórmula.'), ('$n(n+1)+2(n+1)=(n+1)(n+2)$.', 'Hereditariedade com a hipótese.')], '$2+4+\\dots+2n=n(n+1)$.')]},
        'problem_first': {'starter': free('e1-p1', 'Para que valores de $x$ está $x$ a menos de 2 unidades de 5?', 'Distância entre dois números é o módulo da diferença: traduz-se a frase para $|x-5|<2$.', [('$|x-5|<2$', 'Distância entre $x$ e 5.'), ('$3<x<7$', 'Regra do módulo e somar 5.')], '$]3,7[$',
                                           hints=['«Distância entre $x$ e 5» escreve-se com um módulo.', 'Que intervalo tem centro 5 e raio 2?']),
                          'compare': 'A lição dá o atalho: distância entre $x$ e 5 é $|x-5|$ e «menor que 2» desdobra-se num só intervalo. Se resolveste por tentativas, compara: a regra dá logo os extremos 3 e 7 sem testar valores.'},
        'feynman': {'task': 'Explica a alguém de 12 anos o que quer dizer $|x-5|<2$ e porque é que dá um só intervalo.',
                    'checklist': ['Diz que o módulo é uma distância', 'Usa um exemplo com números', 'Explica porque dá «entre» e não «ou»', 'Não usa termos que a criança não conheça']},
        'mindmap': {'center': 'Reais, módulo e indução', 'branches': [{'label': 'Axiomas', 'leaves': ['corpo', 'ordem', 'supremo']}, {'label': 'Módulo', 'leaves': ['distância a zero', 'desigualdade triangular', '«menor»: um intervalo']}, {'label': 'Indução', 'leaves': ['base', 'hereditariedade']}],
                    'blanks': [[0, 1], [1, 1], [2, 1]]},
        'sq3r': {'survey': 'Este tópico apresenta as regras que fazem dos reais um corpo ordenado, o módulo como distância e a indução como forma de provar uma afirmação para todos os naturais.',
                 'questions': ['O que é o módulo de um número?', 'Quando dá um intervalo e quando dá dois ramos?', 'Quais são os dois passos da indução?'],
                 'recap': ['A distância a zero', '«Menor»: um intervalo; «maior»: dois ramos', 'Base e hereditariedade']},
        'cornell': {'cues': [{'cue': 'Módulo', 'note': 'distância a zero, $|x|\\ge0$'}, {'cue': 'Triangular', 'note': '$|x+y|\\le|x|+|y|$'}, {'cue': '$|x|<a$', 'note': '$-a<x<a$'}, {'cue': 'Indução', 'note': 'base + hereditariedade'}],
                    'summary': 'O módulo mede distâncias e transforma-se num intervalo ou em dois ramos conforme o sinal da desigualdade; a indução prova uma afirmação para todos os naturais com dois passos, a base e a hereditariedade.'},
        'hansei': ['Distingui bem «menor» de «maior» nos módulos?'],
    }


def parts2():
    m = lambda i, top, q, c, ok, no, meth, do, why, ans: tf(f'e2-m{i}', q, c, ok, no, meth, do, why, ans, topic=top)
    return {
        'active_recall': {'questions': [{'q': 'Quando se pode multiplicar $A$ por $B$?', 'a': 'Quando o número de colunas de $A$ é igual ao de linhas de $B$.'},
                                        {'q': '$AB=BA$ sempre?', 'a': 'Não: o produto de matrizes não é comutativo.'},
                                        {'q': 'O que é um pivô?', 'a': 'A primeira entrada não nula de uma linha em escada.'},
                                        {'q': 'O que é a característica?', 'a': 'O número de pivôs da matriz em escada.'}],
                          'keys': ['Linha × coluna', 'Não comutativo', 'Gauss até à escada; car = número de pivôs']},
        'spaced': {'quick': [{'q': 'Ordem de $AB$ com $A$ $2\\times3$ e $B$ $3\\times1$', 'a': '$2\\times1$'}, {'q': '$\\det\\begin{pmatrix}1&2\\\\3&4\\end{pmatrix}$', 'a': '$-2$'},
                             {'q': 'Operações de Gauss permitidas', 'a': 'Trocar linhas, multiplicar por $k\\neq0$, somar múltiplos de outra linha.'}, {'q': 'Sistema possível e indeterminado quando…', 'a': 'car(A) = car(A|b) < número de incógnitas.'}]},
        'kumon': [[tf(f'e2-k1{i}', q, c, 'Verdadeiro: conta as colunas da primeira e as linhas da segunda.', 'Falso: as dimensões do meio não coincidem.', PRD, d, 'Regra das dimensões do produto.', d)
                   for i, (q, c, d) in enumerate([('$A_{2\\times3}B_{3\\times2}$ existe', 0, 'Existe, $2\\times2$'), ('$A_{2\\times2}B_{3\\times1}$ existe', 1, 'Não existe'), ('$A_{1\\times3}B_{3\\times1}$ é $1\\times1$', 0, '$1\\times1$')], 1)],
                  [free(f'e2-k2{i}', f'Calcula ${q}$.', PRD, [(s, 'Linha vezes coluna.'), (s2, 'Somar os produtos.')], ans)
                   for i, (q, s, s2, ans) in enumerate([('\\begin{pmatrix}1&2\\end{pmatrix}\\begin{pmatrix}3\\\\4\\end{pmatrix}', '$1\\cdot3+2\\cdot4$', '$3+8$', '$11$'), ('\\begin{pmatrix}2&0\\end{pmatrix}\\begin{pmatrix}5\\\\1\\end{pmatrix}', '$2\\cdot5+0\\cdot1$', '$10+0$', '$10$'), ('\\begin{pmatrix}1&1\\end{pmatrix}\\begin{pmatrix}1\\\\-1\\end{pmatrix}', '$1-1$', '$0$', '$0$')], 1)],
                  [free(f'e2-k3{i}', f'Resolve ${q}$.', GAU, [(s, 'Eliminar $x$ da segunda equação.'), (s2, 'Substituir para trás.')], ans)
                   for i, (q, s, s2, ans) in enumerate([('x+y=3,\\ x-y=1', '$2y=2$', '$y=1,\\ x=2$', '$(2,1)$'), ('x+y=2,\\ x+2y=3', '$y=1$', '$x=1$', '$(1,1)$'), ('x+2y=4,\\ 2x+y=5', '$-3y=-3$', '$y=1,\\ x=2$', '$(2,1)$')], 1)]],
        'worked_examples': [{'example': example('Sistema 2×2 por Gauss', 'Resolve $x+y=5,\\ x-y=1$.', GAU, [('$L_2\\leftarrow L_2-L_1$: $-2y=-4$.', 'Eliminar $x$ com uma operação de Gauss.'), ('$y=2,\\ x=3$.', 'Substituir para trás na primeira linha.')], '$(3,2)$'),
                             'twin': free('e2-w1', 'Resolve $x+y=7,\\ x-y=3$.', GAU, [('$-2y=-4$', 'Subtrair a primeira linha à segunda.'), ('$y=2,\\ x=5$', 'Substituição para trás.')], '$(5,2)$')},
                            {'example': example('Produto 2×2', 'Calcula $\\begin{pmatrix}1&0\\\\2&1\\end{pmatrix}\\begin{pmatrix}3\\\\1\\end{pmatrix}$.', PRD, [('$1\\cdot3+0\\cdot1=3$', 'Primeira linha vezes a coluna.'), ('$2\\cdot3+1\\cdot1=7$', 'Segunda linha vezes a coluna.')], '$\\begin{pmatrix}3\\\\7\\end{pmatrix}$'),
                             'twin': free('e2-w2', 'Calcula $\\begin{pmatrix}2&1\\\\0&1\\end{pmatrix}\\begin{pmatrix}1\\\\4\\end{pmatrix}$.', PRD, [('$2\\cdot1+1\\cdot4=6$', 'Primeira linha vezes a coluna.'), ('$0\\cdot1+1\\cdot4=4$', 'Segunda linha vezes a coluna.')], '$\\begin{pmatrix}6\\\\4\\end{pmatrix}$')}],
        'shuhari': {'shu': [free('e2-s1', 'Resolve $x+y=4,\\ x-y=2$ como no exemplo.', GAU, [('$-2y=-2$', 'Subtrair a primeira linha.'), ('$y=1,\\ x=3$', 'Substituição para trás.')], '$(3,1)$', hints=['Faz $L_2\\leftarrow L_2-L_1$.', 'Com $y$, volta à primeira equação.'])],
                    'ha': [free('e2-s2', 'Resolve $2x+y=5,\\ x+y=3$.', GAU, [('$L_2\\leftarrow 2L_2-L_1$: $y=1$.', 'Eliminar $x$ com um múltiplo.'), ('$x=2$', 'Substituição para trás.')], '$(2,1)$')],
                    'ri': [free('e2-s3', 'Inventa um sistema 2×2 sem solução e mostra porquê com Gauss.', 'Um sistema é impossível quando a escada dá uma linha $0=c$ com $c\\neq0$: escolhem-se duas retas paralelas.', [('$x+y=1,\\ x+y=2$', 'Retas paralelas, mesmo lado esquerdo.'), ('$L_2-L_1$: $0=1$.', 'A linha impossível prova que não há solução.')], 'Por exemplo $x+y=1,\\ x+y=2$.')]},
        'problem_first': {'starter': free('e2-p1', 'Dois números somam 10 e a diferença é 4. Quais são?', 'Duas incógnitas com duas condições lineares: escreve-se um sistema e elimina-se uma incógnita.', [('$x+y=10,\\ x-y=4$', 'Traduzir as duas frases.'), ('$2x=14$, $x=7$, $y=3$', 'Somar as equações elimina $y$.')], '$7$ e $3$',
                                           hints=['Chama $x$ e $y$ aos números e escreve duas equações.', 'Somar as duas equações faz desaparecer uma incógnita.']),
                          'compare': 'Somar as equações é exatamente uma operação de Gauss. A lição faz o mesmo de forma sistemática, com a matriz aumentada, e funciona igual com três ou mais incógnitas, onde as tentativas deixam de chegar.'},
        'interleaving': [m(1, 1, '$|x-1|<2\\Leftrightarrow -1<x<3$', 0, 'Verdadeiro: é o intervalo de centro 1 e raio 2.', 'Falso: seria assim só com «maior».', ABS, '$-2<x-1<2$', 'Regra do módulo com «menor».', '$]-1,3[$'),
                         m(2, 2, '$AB=BA$ para quaisquer matrizes quadradas', 1, 'Verdadeiro só em casos especiais, não em geral.', 'Falso: o produto de matrizes não é comutativo.', PRD, 'Contraexemplo com matrizes $2\\times2$.', 'Basta um caso em que falhe.', 'Falso'),
                         m(3, 1, 'Na indução, a hereditariedade usa a hipótese $P(n)$', 0, 'Verdadeiro: parte-se de $P(n)$ para chegar a $P(n+1)$.', 'Falso: sem hipótese não há passo de indução.', IND, '$P(n)\\Rightarrow P(n+1)$', 'Definição do passo de indução.', 'Verdadeiro'),
                         m(4, 2, 'Um sistema com uma linha $0=3$ na escada é impossível', 0, 'Verdadeiro: nenhuma escolha das incógnitas dá $0=3$.', 'Falso: a linha diz que não há solução.', GAU, 'A linha $0=3$ nunca se verifica.', 'Leitura da escada de Gauss.', 'Verdadeiro')],
        'feynman': {'task': 'Explica a alguém de 12 anos o que faz o método de Gauss e porque não muda as soluções.',
                    'checklist': ['Diz que se eliminam incógnitas uma a uma', 'Explica porque as operações não mudam as soluções', 'Usa um exemplo pequeno', 'Diz quando o sistema não tem solução']},
        'mindmap': {'center': 'Matrizes e sistemas', 'branches': [{'label': 'Operações', 'leaves': ['soma', 'produto linha × coluna', 'não comutativo']}, {'label': 'Gauss', 'leaves': ['matriz aumentada', 'escada', 'pivôs']}, {'label': 'Soluções', 'leaves': ['possível determinado', 'indeterminado', 'impossível']}],
                    'blanks': [[0, 2], [1, 2], [2, 2]]},
        'sq3r': {'survey': 'Este tópico mostra como se opera com matrizes, porque o produto não é comutativo e como o método de Gauss resolve qualquer sistema linear e classifica as suas soluções.',
                 'questions': ['Quando se pode multiplicar duas matrizes?', 'O que se faz no método de Gauss?', 'Como se sabe se um sistema é impossível?'],
                 'recap': ['Colunas da primeira = linhas da segunda', 'Operações de linha até à escada', 'Aparece uma linha $0=c$ com $c\\neq0$']},
        'cornell': {'cues': [{'cue': 'Produto', 'note': 'linha × coluna'}, {'cue': 'Comutativo?', 'note': 'não: $AB\\neq BA$ em geral'}, {'cue': 'Gauss', 'note': 'operações de linha até à escada'}, {'cue': 'car(A)', 'note': 'número de pivôs'}],
                    'summary': 'O produto de matrizes faz-se linha vezes coluna e não é comutativo; o método de Gauss leva a matriz aumentada à escada, e os pivôs dão a característica, que decide se o sistema é possível e quantas soluções tem.'},
    }


def main():
    out = HERE
    for f in ('pack.json', 'map.json'):
        shutil.copy(EX / f, out / f)
    (out / 'topics').mkdir(exist_ok=True)
    pack = json.load(open(out / 'pack.json', encoding='utf-8'))
    pack['slug'] = 'cdim'; pack['course'] = 'Cálculo Diferencial (exemplo com métodos)'
    pack['features']['plan'] = False; pack['features']['tests'] = False
    pack['urls'] = {k: '' for k in pack['urls']}
    pack['methods'] = {'time': 'pomodoro', 'hansei': True, 'learning': ['active_recall', 'spaced', 'learning_by_doing', 'kumon', 'worked_examples', 'shuhari',
                                                                       'problem_first', 'interleaving', 'feynman', 'mindmap', 'sq3r', 'cornell']}
    json.dump(pack, open(out / 'pack.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for n, parts in ((1, parts1()), (2, parts2())):
        tp = json.load(open(EX / 'topics' / f'{n}.json', encoding='utf-8'))
        for i, e in enumerate(tp['exercises']):
            e['level'] = min(i + 1, 3)
        if len(tp['exercises']) < 3:   # learning by doing needs levels 1, 2 and 3
            tp['exercises'] += [free(f'e{n}-g{k}', q, GAU if n == 2 else ABS, s, a, level=k) for k, (q, s, a) in {
                2: ('Resolve $x+y=6,\\ x-y=2$.', [('$-2y=-4$', 'Subtrair a primeira linha.'), ('$y=2,\\ x=4$', 'Substituição para trás.')], '$(4,2)$'),
                3: ('Resolve $x+y+z=3,\\ y+z=2,\\ z=1$.', [('$z=1$, $y=1$', 'Ler a escada de baixo para cima.'), ('$x=1$', 'Substituir na primeira equação.')], '$(1,1,1)$')}.items()]
        tp['parts'] = parts
        json.dump(tp, open(out / 'topics' / f'{n}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('example-methods written')


if __name__ == '__main__':
    main()
