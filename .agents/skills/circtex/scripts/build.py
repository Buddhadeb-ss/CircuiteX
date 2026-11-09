#!/usr/bin/env python3
"""circtex build: note-spec JSON -> .tex -> .pdf

Usage: python build.py note.json [--out DIR] [--no-pdf] [--check]
Validates against spec/note-schema.json, library/circuits.json, library/sources.json.
Prints a short list of problems, or the output paths. No chatter.
"""
import argparse, datetime, json, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
load = lambda p: json.loads((ROOT / p).read_text(encoding="utf-8"))


def fill(template, values):
    return re.sub(r"<<(\w+)>>", lambda m: str(values.get(m.group(1), "")), template)


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


# ---------- block renderers (add new block types here + in note-schema.json) ----------
def boxed(env):
    def r(b, ctx):
        opt = f"[title={{{b['title']}}}]" if b.get("title") else ""
        return f"\\begin{{{env}}}{opt}\n{b['body']}\n\\end{{{env}}}\n"
    return r


def r_text(b, ctx):
    return b["body"] + "\n"


def r_formula(b, ctx):
    opt = f"[title={{{b['title']}}}]" if b.get("title") else ""
    note = f"\n{b['note']}" if b.get("note") else ""
    return f"\\begin{{formulabox}}{opt}\n\\[ {b['tex']} \\]{note}\n\\end{{formulabox}}\n"


def r_list(b, ctx):
    env = "enumerate" if b.get("ordered") else "itemize"
    title = f"\\textbf{{{b['title']}}}\n" if b.get("title") else ""
    items = "\n".join(f"  \\item {i}" for i in b["items"])
    return f"{title}\\begin{{{env}}}\n{items}\n\\end{{{env}}}\n"


def r_table(b, ctx):
    cols = b["columns"]
    head = " & ".join(f"\\textbf{{{c}}}" for c in cols)
    rows = "\n".join(" & ".join(str(c) for c in row) + r" \\" for row in b["rows"])
    cap = f"\\captionof{{table}}{{{b['caption']}}}\n" if b.get("caption") else ""
    return (f"\\begin{{center}}\n{cap}\\begin{{tabular}}{{{'l' * len(cols)}}}\n\\toprule\n"
            f"{head} \\\\\n\\midrule\n{rows}\n\\bottomrule\n\\end{{tabular}}\n\\end{{center}}\n")


def r_circuit(b, ctx):
    if "snippet" in b:
        spec = ctx["circuits"][b["snippet"]]
        params = {**spec["params"], **b.get("params", {})}
        body = (ctx["root"] / "assets" / "circuits" / f"{b['snippet']}.tex").read_text(encoding="utf-8")
        body = fill(body, params)
        cap = b.get("caption", spec["title"])
    else:
        body = f"\\begin{{circuitikz}}\n{b['custom']}\n\\end{{circuitikz}}"
        cap = b.get("caption")
    cap_tex = f"\\captionof{{figure}}{{{cap}}}\n" if cap else ""
    return f"\\begin{{center}}\n{body}\n\n{cap_tex}\\end{{center}}\n"


def r_summary(b, ctx):
    items = "\n".join(f"  \\item {p}" for p in b["points"])
    t = b.get("title", "Summary")
    return f"\\begin{{summarybox}}[title={{{t}}}]\n\\begin{{itemize}}\n{items}\n\\end{{itemize}}\n\\end{{summarybox}}\n"


def r_check(b, ctx):
    items = "\n".join(f"  \\item {q}" for q in b["questions"])
    t = b.get("title", "Check yourself")
    return f"\\begin{{checkbox}}[title={{{t}}}]\n\\begin{{enumerate}}\n{items}\n\\end{{enumerate}}\n\\end{{checkbox}}\n"


RENDERERS = {
    "text": r_text, "definition": boxed("defbox"), "formula": r_formula,
    "example": boxed("examplebox"), "warning": boxed("warnbox"),
    "list": r_list, "table": r_table, "circuit": r_circuit,
    "summary": r_summary, "check": r_check,
}


# ---------- validation ----------
def validate(spec, schema, circuits, sources):
    errs = []
    meta = spec.get("meta", {})
    for f in schema["meta"]["required"]:
        if f not in meta:
            errs.append(f"meta: missing required '{f}'")
    for f in meta:
        if f not in schema["meta"]["required"] + schema["meta"]["optional"]:
            errs.append(f"meta: unknown field '{f}'")
    for k in meta.get("references", []):
        if k not in sources:
            errs.append(f"meta.references: '{k}' not in library/sources.json")
    if not spec.get("sections"):
        errs.append("no sections")
    for si, sec in enumerate(spec.get("sections", []), 1):
        for f in schema["section"]["required"]:
            if f not in sec:
                errs.append(f"section {si}: missing '{f}'")
        for bi, b in enumerate(sec.get("blocks", []), 1):
            where = f"section {si} block {bi}"
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
            if t == "circuit":
                has_s, has_c = "snippet" in b, "custom" in b
                if has_s == has_c:
                    errs.append(f"{where}: circuit needs exactly one of 'snippet' or 'custom'")
                if has_s:
                    if b["snippet"] not in circuits:
                        errs.append(f"{where}: snippet '{b['snippet']}' not in library/circuits.json "
                                    f"(have: {', '.join(circuits)})")
                    else:
                        bad = set(b.get("params", {})) - set(circuits[b["snippet"]]["params"])
                        if bad:
                            errs.append(f"{where}: unknown params {sorted(bad)} for '{b['snippet']}' "
                                        f"(valid: {sorted(circuits[b['snippet']]['params'])})")
    return errs


# ---------- build ----------
def build(spec_path, out_dir=".", compile_pdf=True, check_only=False):
    try:
        spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"SPEC ERRORS:\n  Failed to read or parse JSON file: {e}")
        return 2

    schema = load("spec/note-schema.json")
    circuits = load("library/circuits.json")["circuits"]
    sources = load("library/sources.json")["sources"]
    theme = load("spec/theme.json")
    comps = load("library/components.json")

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
        "header_text": theme["header_text"], "font_setup": theme["font_setup"], "title": meta["title"], "color_defs": colors,
        "style": comps.get("style", "american")})

    date = meta.get("date", "auto")
    date = datetime.date.today().strftime("%d %B %Y") if date == "auto" else date
    subtitle = f"\\\\[0.2em]\\large {meta['subject']}" if meta.get("subject") else ""
    author = f"\\\\[0.2em]\\normalsize {meta['author']}" if meta.get("author") else ""
    parts = [pre, "\\begin{document}",
             f"\\begin{{center}}{{\\Huge\\bfseries\\color{{accent}} {meta['title']}}}{subtitle}{author}"
             f"\\\\[0.4em]\\small {date}\\end{{center}}\n\\vspace{{0.5em}}\n"]

    ctx = {"circuits": circuits, "root": ROOT}
    for sec in spec["sections"]:
        parts.append(f"\\section{{{sec['heading']}}}\n")
        for b in sec["blocks"]:
            parts.append(RENDERERS[b["type"]](b, ctx))
    refs = meta.get("references", [])
    if refs:
        items = "\n".join(f"  \\item {sources[k]['cite']}" for k in refs)
        parts.append(f"\\begin{{summarybox}}[title={{References}}]\\small\n\\begin{{itemize}}\n{items}\n\\end{{itemize}}\n\\end{{summarybox}}\n")
    parts.append("\\end{document}\n")

    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^A-Za-z0-9_-]+", "-", Path(spec_path).stem)
    tex = out / f"{stem}.tex"
    tex.write_text("\n".join(parts), encoding="utf-8")
    if not compile_pdf:
        print(tex); return 0

    compiler = find_latex_compiler()
    if not compiler:
        print("LATEX ERRORS:\n  No LaTeX compiler (pdflatex or tectonic) was found.")
        print(f"  LaTeX file generated successfully: {tex}")
        print("  Install MiKTeX / TeX Live or Tectonic to compile PDFs, or use --no-pdf.")
        return 1

    if "tectonic" in compiler.lower():
        # Tectonic single-pass compiler
        r = subprocess.run([compiler, tex.name], cwd=out, capture_output=True, text=True)
        if r.returncode != 0:
            print("LATEX ERRORS:")
            for line in r.stderr.splitlines()[:5]:
                print(f"  {line}")
            return 1
    else:
        # Standard pdflatex (run twice for cross-refs)
        for _ in range(2):
            r = subprocess.run([compiler, "-interaction=nonstopmode", "-halt-on-error", tex.name],
                               cwd=out, capture_output=True, text=True)
            if r.returncode != 0:
                log = (out / f"{stem}.log").read_text(errors="ignore").splitlines()
                hits = [i for i, l in enumerate(log) if l.startswith("!")][:3]
                print("LATEX ERRORS:")
                for i in hits:
                    print("  " + " | ".join(x.strip() for x in log[i:i + 3] if x.strip()))
                print(f"(full log: {out / (stem + '.log')})")
                return 1
        for ext in ("aux", "log", "out"):
            (out / f"{stem}.{ext}").unlink(missing_ok=True)

    pdf_out = out / f"{stem}.pdf"
    print(pdf_out)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Compile circtex JSON notes to LaTeX and PDF.")
    ap.add_argument("spec", help="Path to JSON note spec")
    ap.add_argument("--out", default=".", help="Output directory for generated files")
    ap.add_argument("--no-pdf", action="store_true", help="Generate .tex only without compiling PDF")
    ap.add_argument("--check", action="store_true", help="Validate spec against schema and registries only")
    a = ap.parse_args()
    sys.exit(build(a.spec, a.out, compile_pdf=not a.no_pdf, check_only=a.check))
