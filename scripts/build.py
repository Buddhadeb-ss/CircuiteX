#!/usr/bin/env python3
"""CircuiteX Build Engine: note-spec JSON -> .tex -> .pdf

Usage: python build.py note.json [--out DIR] [--no-pdf] [--check] [--png] [--auto-install-compiler]
Validates against spec/note-schema.json, library/circuits.json, library/sources.json.
Fail-proof compilation with automatic compiler discovery and prose escaping.
"""
import argparse
import datetime
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_json(rel_path):
    return json.loads((ROOT / rel_path).read_text(encoding="utf-8"))


def fill(template, values):
    return re.sub(r"<<(\w+)>>", lambda m: str(values.get(m.group(1), "")), template)


def escape_latex_prose(text):
    """Escapes special LaTeX characters in regular prose while leaving math mode untouched."""
    if not isinstance(text, str):
        return str(text)

    # Split by display math \[...\], $$, or inline $...$
    pattern = r'(\\\[[\s\S]*?\\\]|\$\$(?:\\.|[^$])*\$\$|\$(?:\\.|[^$])*\$)'
    tokens = re.split(pattern, text)
    result = []
    for token in tokens:
        if not token:
            continue
        if (token.startswith('$') and token.endswith('$') and len(token) >= 2) or \
           (token.startswith(r'\[') and token.endswith(r'\]')):
            # Inside math mode: preserve exact math syntax
            result.append(token)
        else:
            # Outside math mode: escape characters that crash LaTeX
            t = re.sub(r'(?<!\\)&', r'\&', token)
            t = re.sub(r'(?<!\\)%', r'\%', t)
            t = re.sub(r'(?<!\\)#', r'\#', t)
            t = re.sub(r'(?<!\\)_', r'\_', t)
            result.append(t)
    return ''.join(result)


def escape_code(text):
    """Escapes code characters for display inside a LaTeX monospace box, preserving indentation."""
    replacements = [
        ('\\', r'\textbackslash{}'),
        ('{', r'\{'), ('}', r'\}'),
        ('_', r'\_'), ('^', r'\^{}'),
        ('~', r'\textasciitilde{}'),
        ('&', r'\&'), ('%', r'\%'),
        ('#', r'\#'), ('$', r'\$'),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    lines = []
    for line in text.split('\n'):
        leading_spaces = len(line) - len(line.lstrip(' '))
        line_body = line.lstrip(' ')
        if leading_spaces > 0:
            lines.append(r'\hspace*{' + f"{leading_spaces * 0.5:.1f}" + 'em}' + line_body)
        else:
            lines.append(line_body)
    return '\\\\\n'.join(lines)


def find_latex_compiler():
    if shutil.which("pdflatex"):
        return "pdflatex"
    if shutil.which("tectonic"):
        return "tectonic"
    # Check Antigravity / user bin for standalone tectonic
    local_bin = Path.home() / ".gemini" / "bin" / ("tectonic.exe" if sys.platform == "win32" else "tectonic")
    if local_bin.exists():
        return str(local_bin)
    return None


# ---------- block renderers ----------
def boxed(env):
    def r(b, ctx):
        t = escape_latex_prose(b['title']) if b.get('title') else ""
        opt = f"[title={{{t}}}]" if t else ""
        body = escape_latex_prose(b['body'])
        return f"\\begin{{{env}}}{opt}\n{body}\n\\end{{{env}}}\n"
    return r


def r_text(b, ctx):
    return escape_latex_prose(b["body"]) + "\n"


def r_formula(b, ctx):
    t = escape_latex_prose(b['title']) if b.get('title') else ""
    opt = f"[title={{{t}}}]" if t else ""
    note_txt = escape_latex_prose(b['note']) if b.get('note') else ""
    note = f"\n{note_txt}" if note_txt else ""
    # b['tex'] is raw math, do not escape
    return f"\\begin{{formulabox}}{opt}\n\\[ {b['tex']} \\]{note}\n\\end{{formulabox}}\n"


def r_list(b, ctx):
    env = "enumerate" if b.get("ordered") else "itemize"
    t = escape_latex_prose(b['title']) if b.get('title') else ""
    title = f"\\textbf{{{t}}}\n" if t else ""
    items = "\n".join(f"  \\item {escape_latex_prose(i)}" for i in b["items"])
    return f"{title}\\begin{{{env}}}\n{items}\n\\end{{{env}}}\n"


def r_table(b, ctx):
    cols = [escape_latex_prose(c) for c in b["columns"]]
    head = " & ".join(f"\\textbf{{{c}}}" for c in cols)
    rendered_rows = []
    for row in b["rows"]:
        cells = [escape_latex_prose(cell) for cell in row]
        rendered_rows.append(" & ".join(cells) + r" \\")
    rows_str = "\n".join(rendered_rows)
    cap = escape_latex_prose(b['caption']) if b.get('caption') else ""
    cap_tex = f"\\captionof{{table}}{{{cap}}}\n\\vspace{{0.4em}}\n" if cap else ""
    return (f"\\noindent\\begin{{minipage}}{{\\linewidth}}\n\\centering\n{cap_tex}\\begin{{tabular}}{{{'l' * len(cols)}}}\n\\toprule\n"
            f"{head} \\\\\n\\midrule\n{rows_str}\n\\bottomrule\n\\end{{tabular}}\n\\end{{minipage}}\n\\vspace{{0.8em}}\n")


def r_circuit(b, ctx):
    scale_opt = f"[scale={b['scale']}, transform shape]" if b.get("scale") else ""
    if "snippet" in b:
        spec = ctx["circuits"][b["snippet"]]
        params = {**spec["params"], **b.get("params", {})}
        raw_body = (ctx["root"] / "assets" / "circuits" / f"{b['snippet']}.tex").read_text(encoding="utf-8")
        body = fill(raw_body, params)
        if scale_opt:
            body = body.replace("\\begin{circuitikz}", f"\\begin{{circuitikz}}{scale_opt}", 1)
        cap = escape_latex_prose(b.get("caption", spec["title"]))
    else:
        body = f"\\begin{{circuitikz}}{scale_opt}\n{b['custom']}\n\\end{{circuitikz}}"
        cap = escape_latex_prose(b.get("caption", ""))
    cap_tex = f"\\captionof{{figure}}{{{cap}}}\n" if cap else ""
    return f"\\noindent\\begin{{minipage}}{{\\linewidth}}\n\\centering\n{body}\n\n{cap_tex}\\end{{minipage}}\n\\vspace{{0.8em}}\n"


def r_code(b, ctx):
    t = escape_latex_prose(b.get("title", ""))
    opt = f"[title={{{t}}}]" if t else ""
    cap = escape_latex_prose(b.get("caption", ""))
    cap_tex = f"\\captionof{{listing}}{{{cap}}}\n" if cap else ""
    code_body = escape_code(b["code"])
    return f"{cap_tex}\\begin{{codebox}}{opt}\n{code_body}\n\\end{{codebox}}\n"


def r_summary(b, ctx):
    items = "\n".join(f"  \\item {escape_latex_prose(p)}" for p in b["points"])
    t = escape_latex_prose(b.get("title", "Summary"))
    return f"\\begin{{summarybox}}[title={{{t}}}]\n\\begin{{itemize}}\n{items}\n\\end{{itemize}}\n\\end{{summarybox}}\n"


def r_check(b, ctx):
    items = "\n".join(f"  \\item {escape_latex_prose(q)}" for q in b["questions"])
    t = escape_latex_prose(b.get("title", "Check yourself"))
    return f"\\begin{{checkbox}}[title={{{t}}}]\n\\begin{{enumerate}}\n{items}\n\\end{{enumerate}}\n\\end{{checkbox}}\n"


RENDERERS = {
    "text": r_text, "definition": boxed("defbox"), "formula": r_formula,
    "example": boxed("examplebox"), "warning": boxed("warnbox"),
    "list": r_list, "table": r_table, "circuit": r_circuit,
    "code": r_code, "summary": r_summary, "check": r_check,
}


# ---------- validation ----------
def validate(spec, schema, circuits, sources):
    errs = []
    if not isinstance(spec, dict):
        return ["Root specification must be a JSON object"]

    meta = spec.get("meta")
    if not isinstance(meta, dict):
        return ["'meta' must be a JSON object"]

    for f in schema["meta"]["required"]:
        if f not in meta:
            errs.append(f"meta: missing required '{f}'")
    for f in meta:
        if f not in schema["meta"]["required"] + schema["meta"]["optional"]:
            errs.append(f"meta: unknown field '{f}'")

    if "references" in meta:
        if not isinstance(meta["references"], list):
            errs.append("meta.references must be a list of source keys")
        else:
            for k in meta["references"]:
                if k not in sources:
                    errs.append(f"meta.references: '{k}' not in library/sources.json")

    sections = spec.get("sections")
    if not isinstance(sections, list) or len(sections) == 0:
        errs.append("spec: 'sections' must be a non-empty list")
        return errs

    for si, sec in enumerate(sections, 1):
        if not isinstance(sec, dict):
            errs.append(f"section {si}: must be a JSON object")
            continue
        for f in schema["section"]["required"]:
            if f not in sec:
                errs.append(f"section {si}: missing '{f}'")
        if not isinstance(sec.get("heading"), str):
            errs.append(f"section {si}: 'heading' must be a string")
        blocks = sec.get("blocks")
        if not isinstance(blocks, list):
            errs.append(f"section {si}: 'blocks' must be a list")
            continue

        for bi, b in enumerate(blocks, 1):
            where = f"section {si} block {bi}"
            if not isinstance(b, dict):
                errs.append(f"{where}: must be a JSON object")
                continue
            t = b.get("type")
            if t not in schema["blocks"]:
                errs.append(f"{where}: unknown type '{t}' (valid: {', '.join(schema['blocks'])})")
                continue
            rule = schema["blocks"][t]
            for f in rule["required"]:
                if f not in b:
                    errs.append(f"{where} ({t}): missing required '{f}'")
            for f in b:
                if f != "type" and f not in rule["required"] + rule["optional"]:
                    errs.append(f"{where} ({t}): unknown field '{f}'")

            # Type specific structural checks
            if t == "list" and "items" in b and not isinstance(b["items"], list):
                errs.append(f"{where} ({t}): 'items' must be a list of strings")
            elif t == "summary" and "points" in b and not isinstance(b["points"], list):
                errs.append(f"{where} ({t}): 'points' must be a list of strings")
            elif t == "check" and "questions" in b and not isinstance(b["questions"], list):
                errs.append(f"{where} ({t}): 'questions' must be a list of strings")
            elif t == "table" and "columns" in b and "rows" in b:
                if not isinstance(b["columns"], list):
                    errs.append(f"{where} ({t}): 'columns' must be a list")
                if not isinstance(b["rows"], list):
                    errs.append(f"{where} ({t}): 'rows' must be a list of lists")
            elif t == "circuit":
                has_s, has_c = "snippet" in b, "custom" in b
                if has_s == has_c:
                    errs.append(f"{where}: circuit needs exactly one of 'snippet' or 'custom'")
                if has_s:
                    if b["snippet"] not in circuits:
                        errs.append(f"{where}: snippet '{b['snippet']}' not in library/circuits.json "
                                    f"(have: {', '.join(sorted(circuits.keys()))})")
                    else:
                        bad = set(b.get("params", {})) - set(circuits[b["snippet"]]["params"])
                        if bad:
                            errs.append(f"{where}: unknown params {sorted(bad)} for '{b['snippet']}' "
                                        f"(valid: {sorted(circuits[b['snippet']]['params'])})")
                if "scale" in b and not isinstance(b["scale"], (int, float)):
                    errs.append(f"{where}: 'scale' must be a number (e.g. 0.85)")

    return errs


# ---------- compile & render ----------
def compile_latex(tex_path, out_dir, compiler):
    stem = tex_path.stem
    if "tectonic" in compiler.lower():
        r = subprocess.run([compiler, tex_path.name], cwd=out_dir, capture_output=True, text=True)
        if r.returncode != 0:
            print("LATEX ERRORS:")
            for line in r.stderr.splitlines()[:6]:
                print(f"  {line}")
            return 1
    else:
        # Standard pdflatex (run twice for cross-refs and tcolorbox bounds)
        for _ in range(2):
            r = subprocess.run([compiler, "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
                               cwd=out_dir, capture_output=True, text=True)
            if r.returncode != 0:
                log = (out_dir / f"{stem}.log").read_text(errors="ignore").splitlines()
                hits = [i for i, l in enumerate(log) if l.startswith("!")][:3]
                print("LATEX ERRORS:")
                for i in hits:
                    print("  " + " | ".join(x.strip() for x in log[i:i + 3] if x.strip()))
                print(f"(full log: {out_dir / (stem + '.log')})")
                return 1
        for ext in ("aux", "log", "out"):
            (out_dir / f"{stem}.{ext}").unlink(missing_ok=True)
    return 0


def render_pdf_to_png(pdf_path, dpi=150):
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(pdf_path))
        png_paths = []
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=dpi)
            out_img = pdf_path.parent / f"{pdf_path.stem}-page{i+1}.png"
            pix.save(str(out_img))
            png_paths.append(out_img)
        return png_paths
    except ImportError:
        print("Note: Install 'pymupdf' to enable automatic PNG page preview rendering.")
        return []


def build(spec_path, out_dir=".", compile_pdf=True, check_only=False, auto_install=False, generate_png=False):
    spec_file = Path(spec_path)
    if not spec_file.exists():
        print(f"ERROR: Spec file not found: {spec_path}")
        return 2

    try:
        spec = json.loads(spec_file.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"SPEC ERRORS:\n  Failed to read or parse JSON file: {e}")
        return 2

    schema = load_json("spec/note-schema.json")
    circuits = load_json("library/circuits.json")["circuits"]
    sources = load_json("library/sources.json")["sources"]
    theme = load_json("spec/theme.json")
    comps = load_json("library/components.json")

    errs = validate(spec, schema, circuits, sources)
    if errs:
        print("SPEC ERRORS:\n  " + "\n  ".join(errs))
        return 2

    if check_only:
        print(f"VALID: {spec_path}")
        return 0

    meta = spec["meta"]
    colors = "\n".join(f"\\definecolor{{{k}}}{{HTML}}{{{v}}}" for k, v in theme["colors"].items())
    pre = fill((ROOT / "assets/preamble.tex").read_text(encoding="utf-8"), {
        "font_size": theme["font_size"], "paper": theme["paper"], "margin": theme["margin"],
        "header_text": escape_latex_prose(theme["header_text"]),
        "font_setup": theme["font_setup"],
        "title": escape_latex_prose(meta["title"]),
        "color_defs": colors,
        "style": comps.get("style", "american")
    })

    date = meta.get("date", "auto")
    date = datetime.date.today().strftime("%d %B %Y") if date == "auto" else escape_latex_prose(date)
    subtitle = f"\\\\[0.2em]\\large {escape_latex_prose(meta['subject'])}" if meta.get("subject") else ""
    author = f"\\\\[0.2em]\\normalsize {escape_latex_prose(meta['author'])}" if meta.get("author") else ""
    title_esc = escape_latex_prose(meta['title'])

    parts = [
        pre,
        "\\begin{document}",
        f"\\begin{{center}}{{\\Huge\\bfseries\\color{{accent}} {title_esc}}}{subtitle}{author}"
        f"\\\\[0.4em]\\small {date}\\end{{center}}\n\\vspace{{0.5em}}\n"
    ]

    ctx = {"circuits": circuits, "root": ROOT}
    for sec in spec["sections"]:
        sec_head = escape_latex_prose(sec['heading'])
        parts.append(f"\\section{{{sec_head}}}\n")
        for b in sec["blocks"]:
            parts.append(RENDERERS[b["type"]](b, ctx))

    refs = meta.get("references", [])
    if refs:
        items = "\n".join(f"  \\item {sources[k]['cite']}" for k in refs)
        parts.append(f"\\begin{{summarybox}}[title={{References}}]\\small\n\\begin{{itemize}}\n{items}\n\\end{{itemize}}\n\\end{{summarybox}}\n")
    parts.append("\\end{document}\n")

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^A-Za-z0-9_-]+", "-", spec_file.stem)
    tex_path = out / f"{stem}.tex"
    tex_path.write_text("\n".join(parts), encoding="utf-8")

    if not compile_pdf:
        print(tex_path)
        return 0

    compiler = find_latex_compiler()
    if not compiler:
        if auto_install:
            print("No compiler found. Auto-installing standalone Tectonic engine...")
            from setup_compiler import install_tectonic
            compiler = str(install_tectonic())
        else:
            print("LATEX ERRORS:\n  No LaTeX compiler (pdflatex or tectonic) was found.")
            print(f"  LaTeX file generated successfully: {tex_path}")
            print("  Run 'python scripts/setup_compiler.py' or use --auto-install-compiler to install Tectonic.")
            return 1

    code = compile_latex(tex_path, out, compiler)
    if code != 0:
        return code

    pdf_path = out / f"{stem}.pdf"
    print(pdf_path)

    if generate_png:
        pngs = render_pdf_to_png(pdf_path)
        for p in pngs:
            print(f"  Preview: {p}")

    return 0


def watch_and_build(spec_path, out_dir, compile_pdf=True, generate_png=False):
    spec_file = Path(spec_path)
    print(f"Watching {spec_file} for changes... (Press Ctrl+C to exit)")
    last_mtime = 0
    while True:
        try:
            mtime = spec_file.stat().st_mtime
            if mtime != last_mtime:
                last_mtime = mtime
                print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] Detected change, rebuilding...")
                build(spec_path, out_dir=out_dir, compile_pdf=compile_pdf, generate_png=generate_png)
            time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopped watch mode.")
            break
        except Exception as e:
            print(f"Error during watch build: {e}")
            time.sleep(1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="CircuiteX: Compile JSON notes to LaTeX and publication-quality PDF.")
    ap.add_argument("spec", help="Path to JSON note specification file")
    ap.add_argument("--out", default=".", help="Output directory for generated files (default: current dir)")
    ap.add_argument("--no-pdf", action="store_true", help="Generate .tex source only without compiling to PDF")
    ap.add_argument("--check", action="store_true", help="Validate spec against schema and registries only")
    ap.add_argument("--png", action="store_true", help="Render compiled PDF pages to PNG previews (requires PyMuPDF)")
    ap.add_argument("--auto-install-compiler", action="store_true", help="Automatically install standalone Tectonic compiler if missing")
    ap.add_argument("--watch", action="store_true", help="Watch specification file and recompile automatically on save")
    a = ap.parse_args()

    if a.watch:
        watch_and_build(a.spec, a.out, compile_pdf=not a.no_pdf, generate_png=a.png)
        sys.exit(0)
    else:
        sys.exit(build(
            a.spec,
            out_dir=a.out,
            compile_pdf=not a.no_pdf,
            check_only=a.check,
            auto_install=a.auto_install_compiler,
            generate_png=a.png,
        ))
