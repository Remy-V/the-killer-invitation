"""
Regenerate print/cartes-killer.html from the live mission list in ../missions.html.

Run from anywhere:  python print/build_cards.py
Requires print/qr_b64.txt (base64 PNG QR code) to already exist — see
CLAUDE.md for how to regenerate it if the target URL ever changes.
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent

with open(REPO / "fonts.css", encoding="utf-8") as f:
    fonts_css = f.read()

with open(REPO / "missions.html", encoding="utf-8") as f:
    missions_html = f.read()

with open(HERE / "qr_b64.txt", encoding="utf-8") as f:
    QR_B64 = f.read().strip()

raw = re.findall(r'<span class="mission__text">(\d+)\. ([^<]*)</span>', missions_html)
missions = [(num, text) for num, text in raw]
assert missions, "no missions found in missions.html — did the markup change?"

BACK_GREETING = "Bienvenue Killer,"
BACK_RULES = [
    "Votre mission est au dos. <strong>Gardez-la secrète</strong> : si on la devine, vous devrez donner votre carte.",
    "Mission réussie ? Annoncez-le discrètement à votre cible : <strong>elle devra vous remettre sa carte</strong>.",
    "Démasqué par 3 témoins à la fois ? <strong>Vous perdez votre carte</strong> — redistribuée par notre agent infiltré.",
    "Dès 18h30 : <strong>récoltez un maximum de cartes</strong>. Discrétion et prudence, ne vous faites pas tuer...",
]
BACK_SIGN = "Tous les coups sont permis. Bonne chance."

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

CORNERS = (
    '<span class="card__corner card__corner--tl"></span>'
    '<span class="card__corner card__corner--tr"></span>'
    '<span class="card__corner card__corner--bl"></span>'
    '<span class="card__corner card__corner--br"></span>'
)

def front_card(num, text):
    return (
        '<div class="card"><div class="card__frame">'
        + CORNERS +
        f'<p class="card__eyebrow">KILLER INC. &middot; MISSION N&deg; {esc(num)}</p>'
        f'<p class="card__text">{esc(text)}</p>'
        '</div></div>\n'
    )

def blank_card():
    return f'<div class="card"><div class="card__frame">{CORNERS}</div></div>\n'

def back_card():
    rules_html = "".join(f"<p>{p}</p>" for p in BACK_RULES)
    return (
        '<div class="card"><div class="card__frame">'
        + CORNERS +
        f'<img class="card__qr" src="data:image/png;base64,{QR_B64}" alt="">'
        '<div class="card__mailhead">'
        '<p><span class="card__field">De :</span> Killer Inc.</p>'
        '<p><span class="card__field">Objet :</span> Votre mission de ce soir</p>'
        '</div>'
        f'<p class="card__greeting">{esc(BACK_GREETING)}</p>'
        f'<div class="card__rules">{rules_html}</div>'
        f'<p class="card__sign">{esc(BACK_SIGN)}</p>'
        '</div></div>\n'
    )

PER_PAGE = 10

def chunk(items, n):
    for i in range(0, len(items), n):
        yield items[i:i+n]

recto_pages = []
for page_missions in chunk(missions, PER_PAGE):
    cards = "".join(front_card(n, t) for n, t in page_missions)
    while len(page_missions) < PER_PAGE:
        cards += blank_card()
        page_missions = page_missions + [None]
    recto_pages.append(cards)

# one extra all-blank page, for missions added after this batch is printed
recto_pages.append("".join(blank_card() for _ in range(PER_PAGE)))

n_back_pages = len(recto_pages)
verso_pages = []
for _ in range(n_back_pages):
    cards = "".join(back_card() for _ in range(PER_PAGE))
    verso_pages.append(cards)

def page_html(cards_html, label):
    return f'<section class="sheet"><p class="sheet__label">{label}</p><div class="grid">{cards_html}</div></section>\n'

def recto_label(i):
    if i == len(recto_pages) - 1:
        return f"RECTO &mdash; feuille {i+1}/{len(recto_pages)} (cartes vierges, pour les missions ajout&eacute;es plus tard)"
    return f"RECTO &mdash; feuille {i+1}/{len(recto_pages)}"

recto_html = "".join(page_html(c, recto_label(i)) for i, c in enumerate(recto_pages))
verso_html = "".join(page_html(c, f"VERSO &mdash; feuille {i+1}/{len(verso_pages)} (identique)") for i, c in enumerate(verso_pages))

longest_num, longest_text = max(missions, key=lambda m: len(m[1]))

html = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Cartes Killer &mdash; impression</title>
<style>
{fonts_css}

:root{{
  --void:#050505;
  --blood:#a91d1f;
  --blood-bright:#d8262b;
}}
*{{box-sizing:border-box;}}
html,body{{margin:0;padding:0;}}
body{{
  background:#3a3a3a;
  font-family:'EB Garamond',Georgia,serif;
  color:#000;
}}

.instructions{{
  max-width:800px;
  margin:0 auto;
  padding:2rem 1.5rem;
  background:#fff;
  color:#111;
  font-family:'EB Garamond',Georgia,serif;
  line-height:1.6;
}}
.instructions h1{{
  font-family:'Nosifer','EB Garamond',serif;
  font-weight:400;
  color:var(--blood-bright);
  font-size:1.6rem;
  background:#111;
  padding:.6em 1em;
  margin:0 0 1em;
}}
.instructions ol{{padding-left:1.3em;}}
.instructions li{{margin-bottom:.5em;}}

.sheet{{
  width:210mm;
  height:297mm;
  margin:16px auto;
  background:#fff;
  box-shadow:0 4px 18px rgba(0,0,0,.5);
  position:relative;
  page-break-after:always;
}}
.sheet__label{{
  position:absolute;
  top:4mm;left:0;right:0;
  text-align:center;
  font-family:'Courier Prime',ui-monospace,monospace;
  font-size:7pt;
  letter-spacing:.1em;
  text-transform:uppercase;
  color:#999;
}}
.grid{{
  position:absolute;
  top:0;left:0;right:0;bottom:0;
  display:grid;
  grid-template-columns:repeat(2,85mm);
  grid-template-rows:repeat(5,55mm);
  justify-content:center;
  align-content:center;
  gap:0;
}}
.card{{
  width:85mm;
  height:55mm;
  padding:2.2mm;
  overflow:hidden;
}}
.card__frame{{
  width:100%;
  height:100%;
  border:.9pt solid #000;
  padding:2.6mm 4mm;
  position:relative;
  display:flex;
  flex-direction:column;
  overflow:hidden;
}}
.card__frame::before{{
  content:"";
  position:absolute;
  inset:1.1mm;
  border:.35pt solid #000;
  pointer-events:none;
}}
.card__corner{{
  position:absolute;
  width:3.6mm;
  height:3.6mm;
  border-style:solid;
  border-color:#000;
  border-width:0;
  pointer-events:none;
}}
.card__corner--tl{{top:.4mm;left:.4mm;border-top-width:1.1pt;border-left-width:1.1pt;}}
.card__corner--tr{{top:.4mm;right:.4mm;border-top-width:1.1pt;border-right-width:1.1pt;}}
.card__corner--bl{{bottom:.4mm;left:.4mm;border-bottom-width:1.1pt;border-left-width:1.1pt;}}
.card__corner--br{{bottom:.4mm;right:.4mm;border-bottom-width:1.1pt;border-right-width:1.1pt;}}
.card__eyebrow{{
  margin:0 0 1.8mm;
  font-family:'Courier Prime',ui-monospace,monospace;
  font-weight:400;
  font-size:6.2pt;
  letter-spacing:.1em;
  text-transform:uppercase;
  color:#000;
  text-align:center;
}}
.card__text{{
  margin:0;
  font-family:'Courier Prime',ui-monospace,monospace;
  font-weight:700;
  font-size:9pt;
  line-height:1.22;
  text-align:center;
  color:#000;
  flex:1;
  display:flex;
  align-items:center;
  justify-content:center;
}}
.card__qr{{
  position:absolute;
  right:1.8mm;
  top:1.8mm;
  width:12.5mm;
  height:12.5mm;
  z-index:1;
  image-rendering:pixelated;
}}

.card__mailhead{{
  position:relative;
  z-index:2;
  margin:1mm 15mm 1.3mm 0;
  padding-bottom:1mm;
  border-bottom:.35pt dashed #000;
}}
.card__mailhead p{{
  margin:0 0 .4mm;
  font-family:'Courier Prime',ui-monospace,monospace;
  font-size:6pt;
  color:#000;
}}
.card__mailhead p:last-child{{margin-bottom:0;}}
.card__field{{
  font-weight:700;
  text-transform:uppercase;
  letter-spacing:.06em;
}}
.card__greeting{{
  margin:0 0 2.4mm;
  font-family:'Courier Prime',ui-monospace,monospace;
  font-size:6pt;
  line-height:1.24;
  color:#000;
}}
.card__rules{{
  flex:1;
  overflow:hidden;
}}
.card__rules p{{
  margin:0 0 1mm;
  font-family:'Courier Prime',ui-monospace,monospace;
  font-size:6pt;
  line-height:1.24;
  text-align:justify;
  text-indent:2.5mm;
  color:#000;
  hyphens:auto;
}}
.card__rules p:last-child{{margin-bottom:0;}}
.card__rules strong{{font-weight:700;}}
.card__sign{{
  margin:1mm 0 0;
  padding-top:.8mm;
  border-top:.35pt solid #000;
  text-align:center;
  font-family:'EB Garamond',Georgia,serif;
  font-style:italic;
  font-weight:700;
  font-size:7pt;
}}

@media print{{
  body{{background:#fff;}}
  .instructions{{display:none;}}
  .sheet{{
    box-shadow:none;
    margin:0;
    width:210mm;
    height:297mm;
    page-break-after:always;
  }}
  @page{{size:A4;margin:0;}}
}}
</style>
</head>
<body>

<div class="instructions">
  <h1>Cartes Killer &mdash; impression</h1>
  <p><strong>{len(missions)} missions</strong>, format carte de visite 85&times;55&nbsp;mm, 10 cartes par feuille A4 (grille 2&times;5).</p>
  <ol>
    <li>Imprime d'abord toutes les pages <strong>RECTO</strong> ({len(recto_pages)} feuilles) &mdash; une mission unique par carte.</li>
    <li>Retourne la pile de feuilles imprim&eacute;es (dans n'importe quel sens &mdash; le verso est identique sur toutes les cartes, l'orientation n'a pas d'importance) et remets-la dans l'imprimante.</li>
    <li>Imprime les pages <strong>VERSO</strong> ({len(verso_pages)} feuilles) par-dessus.</li>
    <li>D&eacute;coupe le long des traits fins int&eacute;rieurs de chaque carte.</li>
  </ol>
  <p>Tout reste en noir pur (pas de rouge) &mdash; sur du papier rouge, du texte rouge serait invisible, donc les accents se font par le gras plut&ocirc;t que par la couleur. Le verso reprend la mise en page &laquo;&nbsp;mail&nbsp;&raquo; du site (De&nbsp;/&nbsp;Objet).</p>
  <p>V&eacute;rifie en particulier la <strong>mission n&deg;{longest_num}</strong>, la plus longue ({len(longest_text)} caract&egrave;res), dans l'aper&ccedil;u avant impression.</p>
  <p>La derni&egrave;re feuille RECTO ({len(recto_pages)}/{len(recto_pages)}) est enti&egrave;rement vierge &mdash; garde-la pour &eacute;crire &agrave; la main les missions ajout&eacute;es apr&egrave;s cette impression.</p>
</div>

{recto_html}
{verso_html}
</body>
</html>
"""

out_path = HERE / "cartes-killer.html"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)

print("done ->", out_path)
print("recto pages:", len(recto_pages))
print("verso pages:", len(verso_pages))
print("total missions:", len(missions))
