"""
Generare raport HTML pentru rezultatele lanțului Planner → Solver → Verifier.
"""

import html
import re
import os
from datetime import datetime


# ── convertor Markdown → HTML ─────────────────────────────────────────────────

def _inline(text: str) -> str:
    """Aplică formatare inline (bold, italic) pe text deja HTML-escaped."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__',     r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*',     r'<em>\1</em>', text)
    return text


def _md_to_html(text: str) -> str:
    """
    Convertor Markdown → HTML orientat pe blocuri.
    - Protejează formulele LaTeX ($...$ și $$...$$) de html.escape
    - Redă liste ordonate ca <ol> (numerotate) și neordonate ca <ul>
    - Fiecare item de listă pe rând separat cu spațiere vizibilă
    - Paragrafe separate prin linie goală
    """
    # ── 1. Protejează formulele matematice ──────────────────────────────────
    math_store: list[str] = []

    def save_block_math(m: re.Match) -> str:
        math_store.append(m.group(0))
        return f"%%MATH{len(math_store)-1}%%"

    def save_inline_math(m: re.Match) -> str:
        math_store.append(m.group(0))
        return f"%%MATH{len(math_store)-1}%%"

    text = re.sub(r'\$\$.+?\$\$',              save_block_math,  text, flags=re.DOTALL)
    text = re.sub(r'\\\[.+?\\\]',             save_block_math,  text, flags=re.DOTALL)
    text = re.sub(r'\$.+?\$',                 save_inline_math, text)
    text = re.sub(r'\\\(.+?\\\)',             save_inline_math, text)

    # ── 2. Parser linie cu linie → blocuri HTML ─────────────────────────────
    lines  = text.split('\n')
    output = []
    i      = 0

    while i < len(lines):
        raw     = lines[i]
        stripped = raw.strip()

        # Linie goală → separare vizuală
        if not stripped:
            output.append('<div class="gap"></div>')
            i += 1
            continue

        # Headings
        for level, prefix in ((3, '### '), (2, '## '), (1, '# ')):
            if stripped.startswith(prefix):
                content = html.escape(stripped[len(prefix):])
                output.append(f'<h{level}>{_inline(content)}</h{level}>')
                i += 1
                break
        else:
            # Listă ordonată  (1. / 2. / …)
            if re.match(r'^\d+\.\s', stripped):
                items = []
                while i < len(lines) and re.match(r'^\d+\.\s', lines[i].strip()):
                    item = re.sub(r'^\d+\.\s+', '', lines[i].strip())
                    items.append(f'<li>{_inline(html.escape(item))}</li>')
                    i += 1
                output.append('<ol>' + ''.join(items) + '</ol>')
                continue

            # Listă neordonată  (- / *)
            if re.match(r'^[-*]\s', stripped):
                items = []
                while i < len(lines) and re.match(r'^[-*]\s', lines[i].strip()):
                    item = re.sub(r'^[-*]\s+', '', lines[i].strip())
                    items.append(f'<li>{_inline(html.escape(item))}</li>')
                    i += 1
                output.append('<ul>' + ''.join(items) + '</ul>')
                continue

            # Paragraf obișnuit
            output.append(f'<p>{_inline(html.escape(stripped))}</p>')
            i += 1

    result = '\n'.join(output)

    # ── 3. Restaurează formulele matematice ─────────────────────────────────
    for idx, formula in enumerate(math_store):
        result = result.replace(f'%%MATH{idx}%%', formula)

    return result


# ── generator raport ──────────────────────────────────────────────────────────

def generate_html_report(problem: str, plan: str, solution: str, verdict: str,
                          output_dir: str = ".") -> str:
    """
    Generează un fișier HTML cu rezultatele complete ale lanțului.
    Returnează calea fișierului generat.
    """
    timestamp   = datetime.now()
    filename    = f"report_{timestamp.strftime('%Y%m%d_%H%M%S')}.html"
    filepath    = os.path.join(output_dir, filename)

    verdict_class = (
        "verdict-correct"
        if "CORECT" in verdict.upper() and "INCORECT" not in verdict.upper()
        else "verdict-incorrect"
    )

    html_content = f"""<!DOCTYPE html>
<html lang="ro">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Raport Planner · Solver · Verifier</title>

  <!-- KaTeX pentru redarea formulelor matematice -->
  <link rel="stylesheet"
        href="https://cdn.jsdelivr.net/npm/katex@0.16.10/dist/katex.min.css">
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.10/dist/katex.min.js"></script>
  <script defer
          src="https://cdn.jsdelivr.net/npm/katex@0.16.10/dist/contrib/auto-render.min.js"
          onload="renderMathInElement(document.body, {{
            delimiters: [
              {{left:'$$',   right:'$$',   display:true}},
              {{left:'\\\\[', right:'\\\\]', display:true}},
              {{left:'$',    right:'$',    display:false}},
              {{left:'\\\\(', right:'\\\\)', display:false}}
            ],
            throwOnError: false
          }})">
  </script>

  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: 'Segoe UI', system-ui, sans-serif;
      background: #0f1117;
      color: #e2e8f0;
      min-height: 100vh;
      padding: 2rem 1rem;
    }}

    .container {{ max-width: 900px; margin: 0 auto; }}

    /* ── Header ── */
    header {{ text-align: center; margin-bottom: 2.5rem; }}
    header h1 {{
      font-size: 1.9rem; font-weight: 700;
      background: linear-gradient(135deg, #6366f1, #a78bfa, #38bdf8);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      background-clip: text; margin-bottom: .4rem;
    }}
    header .subtitle {{ color: #64748b; font-size: .9rem; }}

    /* ── Problemă ── */
    .problem-box {{
      background: linear-gradient(135deg, #1e1b4b, #1e293b);
      border: 1px solid #4338ca; border-radius: 12px;
      padding: 1.4rem 1.6rem; margin-bottom: 2rem;
    }}
    .problem-box .label {{
      font-size: .72rem; font-weight: 700; letter-spacing: .1em;
      text-transform: uppercase; color: #818cf8; margin-bottom: .5rem;
    }}
    .problem-box p {{ font-size: 1.05rem; line-height: 1.65; color: #e0e7ff; }}

    /* ── Card etapă ── */
    .stage {{
      background: #161b27; border-radius: 14px;
      border: 1px solid #1e293b; margin-bottom: 1.6rem;
      overflow: hidden; transition: box-shadow .2s;
    }}
    .stage:hover {{ box-shadow: 0 0 0 1px #334155; }}

    .stage-header {{
      display: flex; align-items: center; gap: .75rem;
      padding: 1rem 1.4rem; border-bottom: 1px solid #1e293b;
    }}
    .stage-icon  {{ font-size: 1.35rem; line-height: 1; }}
    .stage-title {{ font-size: 1rem; font-weight: 700; letter-spacing: .03em; }}
    .stage-badge {{
      margin-left: auto; font-size: .7rem; font-weight: 600;
      padding: .2rem .6rem; border-radius: 20px;
    }}

    /* culori per etapă */
    .stage-planner  .stage-header {{ background: linear-gradient(90deg,#1a2540,#1e293b); }}
    .stage-planner  .stage-title  {{ color: #60a5fa; }}
    .stage-planner  .stage-badge  {{ background: #1e3a5f; color: #60a5fa; }}

    .stage-solver   .stage-header {{ background: linear-gradient(90deg,#1a2e2a,#1e293b); }}
    .stage-solver   .stage-title  {{ color: #34d399; }}
    .stage-solver   .stage-badge  {{ background: #134e3a; color: #34d399; }}

    .stage-verifier .stage-header {{ background: linear-gradient(90deg,#2a1f1a,#1e293b); }}
    .stage-verifier .stage-title  {{ color: #fb923c; }}
    .stage-verifier .stage-badge  {{ background: #431407; color: #fb923c; }}

    /* ── Conținut etapă ── */
    .stage-body {{
      padding: 1.3rem 1.6rem;
      font-size: .94rem; line-height: 1.8; color: #cbd5e1;
    }}
    .stage-body .gap  {{ height: .6rem; }}
    .stage-body p     {{ margin-bottom: .5rem; }}

    .stage-body h1, .stage-body h2, .stage-body h3 {{
      color: #e2e8f0; margin: 1.1rem 0 .5rem;
    }}
    .stage-body h2 {{ font-size: 1.05rem; }}
    .stage-body h3 {{ font-size: .97rem; color: #94a3b8; }}

    /* Liste – fiecare item pe rând separat, spațiat */
    .stage-body ol,
    .stage-body ul {{
      padding-left: 1.5rem;
      margin: .6rem 0 .8rem;
      display: flex; flex-direction: column; gap: .55rem;
    }}
    .stage-body ol {{ list-style: decimal; }}
    .stage-body ul {{ list-style: disc; }}
    .stage-body li  {{
      padding: .45rem .6rem;
      background: #1e293b;
      border-radius: 6px;
      border-left: 3px solid #334155;
      line-height: 1.6;
    }}
    .stage-body strong {{ color: #f1f5f9; }}

    /* KaTeX display */
    .katex-display {{ margin: .8rem 0; overflow-x: auto; }}

    /* ── Verdict ── */
    .verdict-correct  {{ --accent: #4ade80; --bg: #052e16; --border: #166534; }}
    .verdict-incorrect {{ --accent: #f87171; --bg: #2d0a0a; --border: #7f1d1d; }}
    .verdict-correct  .stage-title,
    .verdict-incorrect .stage-title {{ color: var(--accent); }}

    /* ── Footer ── */
    footer {{
      text-align: center; margin-top: 2.5rem;
      color: #334155; font-size: .8rem;
    }}
  </style>
</head>
<body>
  <div class="container">

    <header>
      <h1>Planner &rarr; Solver &rarr; Verifier</h1>
      <p class="subtitle">Generat la {timestamp.strftime('%d %B %Y, %H:%M:%S')}</p>
    </header>

    <!-- Problemă -->
    <div class="problem-box">
      <div class="label">Problemă</div>
      <p>{html.escape(problem)}</p>
    </div>

    <!-- Etapa 1: Planner -->
    <div class="stage stage-planner">
      <div class="stage-header">
        <span class="stage-icon">🗺️</span>
        <span class="stage-title">PLANNER</span>
        <span class="stage-badge">Etapa 1</span>
      </div>
      <div class="stage-body">
        {_md_to_html(plan)}
      </div>
    </div>

    <!-- Etapa 2: Solver -->
    <div class="stage stage-solver">
      <div class="stage-header">
        <span class="stage-icon">⚙️</span>
        <span class="stage-title">SOLVER</span>
        <span class="stage-badge">Etapa 2</span>
      </div>
      <div class="stage-body">
        {_md_to_html(solution)}
      </div>
    </div>

    <!-- Etapa 3: Verifier -->
    <div class="stage stage-verifier {verdict_class}">
      <div class="stage-header">
        <span class="stage-icon">✅</span>
        <span class="stage-title">VERIFIER</span>
        <span class="stage-badge">Etapa 3</span>
      </div>
      <div class="stage-body">
        {_md_to_html(verdict)}
      </div>
    </div>

    <footer>
      Prompt Chaining &middot; Model: llama-3.3-70b-versatile &middot; Groq API
    </footer>

  </div>
</body>
</html>"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

    return filepath
