---
name: circtex
description: Make clean, consistent LaTeX study notes with circuit diagrams (circuitikz), block diagrams, formulas and revision boxes, compiled to PDF. Use whenever the user asks for LaTeX notes, study notes, a circuit diagram, op-amp, BJT, MOSFET, filter, logic-gate or signals notes, "circtex", "circuitex", "CircuiteX", or anything involving circuitikz/TikZ for electronics and ECE topics, even if they don't say "skill". Components come from a predefined library, facts come from predefined trusted sources, and the note is written as an editable JSON spec, so no planning chatter or hand-written LaTeX is needed.
---

# circtex (CircuiteX)

Notes are structured as a **JSON spec**, not hand-written LaTeX. `scripts/build.py` compiles the spec into clean `.tex` and PDF using a standardized, robust preamble and predefined Circuitikz components. This guarantees visual consistency, prevents syntax errors, and saves context tokens.

## Workflow (follow exactly)

1. **No preamble chatter.** Do not announce an implementation plan or repeat the prompt. Go straight to step 2.
2. **Check libraries silently:**
   - `library/circuits.json`: Ready-made circuit snippets (e.g., `inverting-opamp`, `noninverting-opamp`, `mosfet-common-source`, `schmitt-trigger`, `common-emitter`, `rc-lowpass`, `rc-highpass`, `voltage-divider`). Use one whenever it fits.
   - `library/components.json`: Exact circuitikz component syntax. For circuits without a snippet, write a `custom` circuit block using only these forms. Never invent symbols.
   - `library/sources.json`: Trusted reference textbooks per topic. Take formulas, behaviour, and typical values ONLY from these. List the referenced keys in `meta.references`.
   - If a topic is not covered by any source, state it in one line and mark the claim "unverified" in the note. Never pull unverified facts from random search hits.
3. **Write the note spec** to `<name>.json`, following `spec/note-schema.json`. See `examples/` for structure.
4. **Build:**
   ```bash
   python <skill-dir>/scripts/build.py <name>.json --out out/
   ```
   - Validation runs first. If errors are reported (`SPEC ERRORS`), fix the JSON and rebuild. Do not hand-edit the generated `.tex`.
   - If LaTeX is not installed or `--no-pdf` is passed, `build.py` will generate the valid `.tex` file directly.
5. **Deliver** the PDF path (or `.tex` if no LaTeX compiler is available) and the `.json` spec. The JSON spec is what the user edits to customize content. Keep any closing comments to at most two sentences.

## Spec rules

- Required vs. optional fields per block are defined in `spec/note-schema.json`. Block types: `text`, `definition`, `formula`, `example`, `warning`, `list`, `table`, `circuit`, `summary`, `check`.
- `body`, `tex`, and similar fields contain raw LaTeX math. In JSON, every backslash must be doubled (e.g. `"\\frac{V_\\mathrm{out}}{V_\\mathrm{in}}"`).
- Organize logically: one core concept per section. End with a `summary` and a `check` block unless requested otherwise.
- Circuits: prefer `{"type": "circuit", "snippet": "<id>", "params": {...}}`. Params override default symbols with actual component values (e.g. `"$10\\,\\mathrm{k}\\Omega$"`).
- Hand-verify circuit logic: ground node must be present, feedback polarity correct, every terminal and component labelled, and junction dots (`*-*` or `*-o`) present at wire intersections.

## Customization

Everything is plain JSON editable by hand:
- `spec/theme.json`: Color palette (hex values), font package, paper size, margins, header title.
- `spec/note-schema.json`: Field definitions and required/optional block rules.
- `library/*.json`: Predefined components, circuit snippets, and trusted references.
- To add a circuit snippet: drop a `.tex` file with `<<param>>` placeholders into `assets/circuits/` and register it in `library/circuits.json`.

## Error handling

- `SPEC ERRORS`: JSON violates schema or references unknown snippets/params/sources. Fix the reported JSON fields.
- `LATEX ERRORS`:
  - If a font package is missing, edit `font_setup` in `spec/theme.json` (e.g., replace `\usepackage{mathpazo}` with `\usepackage{lmodern}`).
  - If `pdflatex` is not installed, use `--no-pdf` or install a LaTeX distribution (MiKTeX on Windows, MacTeX on macOS, `texlive` on Linux).
- Circuit label collisions: use relative offsets (`++(x,y)`), label sides (`l_=` or `a_=`), and coordinate anchors instead of hardcoded coordinates.
