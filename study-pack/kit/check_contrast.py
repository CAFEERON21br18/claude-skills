"""Contrast check for every theme in themes.json (or a custom theme file). Exit 1 on failure.
Text pairs need 4.5:1, UI accents 3:1."""
import json,sys
def lum(h):
    h=h.lstrip('#'); r,g,b=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    f=lambda c:c/12.92 if c<=0.03928 else ((c+0.055)/1.055)**2.4
    return 0.2126*f(r)+0.7152*f(g)+0.0722*f(b)
def cr(a,b):
    la,lb=lum(a),lum(b); return (max(la,lb)+0.05)/(min(la,lb)+0.05)
TEXT=[('ink','bg'),('ink','surface'),('muted','bg'),('muted','surface'),('band-ink','band'),('accent-ink','accent'),
      ('accent','surface'),('accent2','surface'),('accent2','bg'),('ok','ok-soft'),('bad','bad-soft'),('trap','trap-soft'),('warn','warn-soft'),('ink','accent-soft'),('ink','accent2-soft'),('band-muted','band')]
UI=[('accent','bg'),('line','bg')]
def run(path):
    T=json.load(open(path)); bad=0
    for k,t in T.items():
        if k.startswith('_'): continue
        for mode in ('light','dark'):
            c=t[mode]
            for a,b in TEXT:
                v=cr(c[a],c[b])
                if v<4.5: print(f'FAIL {k}/{mode}: {a} on {b} = {v:.2f} (need 4.5)'); bad+=1
            v=cr(c['accent'],c['bg'])
            if v<3: print(f'FAIL {k}/{mode}: accent on bg = {v:.2f} (need 3)'); bad+=1
    print('contrast:', 'OK' if not bad else f'{bad} failures'); return bad
if __name__=='__main__': sys.exit(1 if run(sys.argv[1] if len(sys.argv)>1 else 'themes.json') else 0)
