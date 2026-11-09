# Task: build the "circtex" skill

Paste this whole file into Antigravity as the task. A working reference implementation is attached as `circtex.skill` (it is a zip: rename to `.zip` and extract). Use it as the starting point, verify it, and improve it. Do not start from scratch.

## 1. Who and why

- User is an ECE student who writes study notes in LaTeX and wants clean circuit diagrams and diagrammatic notes.
- Problem: AI-generated LaTeX notes come out bad. Circuit diagrams have overlapping labels, wires crossing with no junction dots, missing grounds, wrong feedback topology, inconsistent styling, and walls of text.

## 2. Diagnosis (why AI output is bad)

1. The AI writes TikZ coordinates blind and never sees the rendered result. Most visual defects come from this.
2. No fixed reference: it invents symbol syntax and takes facts from random sources.
3. No compile-and-look step, so errors reach the user.
4. Vague prompts make it worse, but that is the smaller cause.
5. It also wastes tokens by writing an "implementation plan" message before the LaTeX.

## 3. Requirements (from the user)

- A skill named `circtex` that gives the AI everything up front:
  - **Predefined components**: do not re-derive how a resistor, op-amp, BJT, MOSFET or gate is drawn. Exact circuitikz syntax is stored.
  - **Predefined best sources** for facts (formulas, behaviour). Use only these; if a topic is not covered, say so and mark it "unverified". No guessing from random web pages.
  - **No implementation/plan message** before producing the LaTeX. Go straight to the output. Max two sentences after.
  - **A human-readable, human-editable JSON file** that structures the note and states what is required vs optional.
- Output: `.tex` + compiled PDF + the JSON spec.

## 4. Design that was built (reference implementation)

The note is a JSON spec; a script renders it with a fixed preamble. Claude never hand-writes LaTeX.

```
circtex/
├── SKILL.md                      workflow + rules (pushy trigger description)
├── spec/
│   ├── note-schema.json          required/optional fields per block type
│   └── theme.json                colors, font_setup, paper, margin, header
├── library/
│   ├── components.json           circuitikz syntax per component + layout rules
│   ├── circuits.json             registry of ready-made circuits + default params
│   └── sources.json              trusted references per topic
├── assets/
│   ├── preamble.tex              fixed preamble, tcolorbox note boxes (<<placeholders>>)
│   └── circuits/*.tex            rc-lowpass, voltage-divider, inverting-opamp,
│                                 noninverting-opamp, common-emitter (<<param>> placeholders)
├── scripts/build.py              spec.json -> .tex -> .pdf, validates first
└── examples/inverting-amplifier.json
```

Block types: text, definition, formula, example, warning, list, table, circuit, summary, check. Meta: title (required); subject, author, date, references (optional). `circuit` takes exactly one of `snippet` (+ optional `params`) or `custom` (raw circuitikz body).

`build.py` behaviour:
- Validates against the schema, circuits registry and sources registry; prints a short `SPEC ERRORS` list and exits 2.
- Renders, runs pdflatex twice, and on failure prints only the first few `!` errors with context (`LATEX ERRORS`), exit 1.
- On success prints only the PDF path.

## 5. Mistakes already hit (do not repeat)

- `/bin/sh` does not support brace expansion (`mkdir -p a/{b,c}` created a junk folder). Use separate `mkdir` calls.
- `lmodern.sty` was missing on the test machine, so the font is now configurable via `font_setup` in `theme.json` (default `\usepackage{mathpazo}`).
- `\captionof` needs the `caption` package; it was missing at first.
- Circuit label collisions: the first voltage-divider and non-inverting op-amp drawings overlapped labels or crossed wires without a dot. Fixed by relative offsets, `l_=` for label side, and flipping the op-amp (`yscale=-1`) so the feedback network sits below.
- In JSON, every LaTeX backslash must be doubled.

## 6. What to do now

1. Extract the reference skill and read every file.
2. Install it where Antigravity loads skills (check Antigravity's own docs for the correct folder and SKILL.md format, and adapt the frontmatter if needed).
3. Run `python scripts/build.py examples/inverting-amplifier.json --out out/`, then rasterize the PDF (`pdftoppm -r 70 -png`) and look at every page. Compile and look after any change to a circuit.
4. Test on at least two new topics (suggested: MOSFET common-source amplifier, Schmitt trigger). Add a snippet for each to `assets/circuits/` and register it in `library/circuits.json`.
5. Check circuit logic by hand: ground present, feedback sign correct, every part labelled, junction dots where wires connect.

## 7. Acceptance criteria

- Spec with a missing required field, bad snippet id, or unknown param fails with a clear error before LaTeX runs.
- All snippets compile with no overlapping labels and no unmarked wire crossings.
- A fresh note takes one JSON file plus one build command, with no planning message.
- The user can change colors, fonts, required/optional fields, components, circuits and sources by editing JSON or dropping a `.tex` file, without touching `build.py`.

## 8. Known limits (state honestly, do not hide)

- The script cannot verify circuit correctness, only structure. A human must check topology.
- Source list is book-level citations only; the user should add or edit entries to suit their syllabus.
