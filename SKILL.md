---
name: circtex
description: Make clean, consistent LaTeX study notes with circuit diagrams (circuitikz), block diagrams, formulas and revision boxes, compiled to PDF. Use whenever the user asks for LaTeX notes, study notes, a circuit diagram, op-amp, BJT, MOSFET, filter, logic-gate, diode, 555 timer, regulator, or signals notes, "circtex", "circuitex", "CircuiteX", or anything involving circuitikz/TikZ for electronics and ECE topics, even if they don't say "skill". Components come from a predefined library of 20+ circuits, facts come from predefined trusted sources, and the note is written as an editable JSON spec, so no planning chatter or hand-written LaTeX is needed.
---

# circtex (CircuiteX)

Notes are structured as a **JSON spec**, not hand-written LaTeX. `scripts/build.py` compiles the spec into clean `.tex` and publication-quality PDF using a standardized, robust preamble and predefined Circuitikz components. This guarantees visual consistency, prevents syntax errors, and saves context tokens.

## Workflow (follow exactly)

1. **No preamble chatter.** Do not announce an implementation plan or repeat the prompt. Go straight to step 2.
2. **Check libraries silently:**
   - `library/circuits.json`: 20 ready-made circuit snippets. Use one by id whenever it fits:
     - Op-Amps: `inverting-opamp`, `noninverting-opamp`, `summing-amplifier`, `difference-amplifier`, `opamp-integrator`, `opamp-differentiator`, `schmitt-trigger`
     - Transistors: `common-emitter` (BJT CE), `bjt-common-collector` (BJT CC/Follower), `mosfet-common-source` (NMOS CS), `mosfet-source-follower` (NMOS CD)
     - Filters & Passive: `rc-lowpass`, `rc-highpass`, `rlc-bandpass`, `voltage-divider`
     - Diodes & Power: `half-wave-rectifier`, `full-wave-bridge-rectifier`, `zener-voltage-regulator`
     - Digital & Timers: `cmos-inverter`, `555-astable`
   - `library/components.json`: Exact circuitikz component syntax. For circuits without a snippet, write a `custom` circuit block using only these forms. Never invent symbols.
   - `library/sources.json`: Trusted reference textbooks per topic (`sedra-smith`, `mancini-opamps`, `razavi-analog`, `alexander-sadiku`, `horowitz-hill`, `mano-digital`, `oppenheim-signals`). Take formulas, behaviour, and typical values ONLY from these. List the referenced keys in `meta.references`.
   - If a topic is not covered by any source, state it in one line and mark the claim "unverified" in the note. Never pull unverified facts from random search hits.
3. **Write the note spec** to `<name>.json`, following `spec/note-schema.json`. See `examples/` for structure.
4. **Build:**
   ```bash
   python <skill-dir>/scripts/build.py <name>.json --out out/ --png
   ```
   - Validation runs first. If errors are reported (`SPEC ERRORS`), fix the JSON and rebuild.
   - Build engine automatically discovers local compilers (`pdflatex` or portable `tectonic`).
   - Use `--png` to automatically generate high-resolution PNG page previews alongside the PDF.
5. **Deliver** the PDF path, page previews (if generated), and the `.json` spec. The JSON spec is what the user edits to customize component values or text. Keep closing comments to at most two sentences.

## Spec rules

- Required vs. optional fields per block are defined in `spec/note-schema.json`.
- Block types:
  - `text`: Regular narrative prose.
  - `definition`: Colored conceptual definition box (`defbox`).
  - `formula`: Centered LaTeX math display with optional explanatory note (`formulabox`).
  - `circuit`: Circuit diagram from library (`snippet`) or raw circuitikz (`custom`). Optional `params` overrides and `scale` (e.g. `0.85`).
  - `example`: Step-by-step worked numerical calculation box (`examplebox`).
  - `warning`: Common pitfalls, design limits, and saturation warnings (`warnbox`).
  - `code`: Monospace syntax/code box (`codebox`) for embedded C, Verilog, or SPICE netlists.
  - `list`: Ordered or unordered list.
  - `table`: Booktabs LaTeX table with columns, rows, and caption.
  - `summary`: High-level takeaway bullet points (`summarybox`).
  - `check`: Self-assessment questions (`checkbox`).
- Prose auto-escaping: characters like `&`, `%`, `#`, and `_` outside math mode are automatically sanitized by the build engine.
- Hand-verify circuit logic: ground node must be present, feedback polarity correct, every terminal and component labelled, and junction dots present at wire intersections.

## Customization

Everything is plain JSON editable by hand:
- `spec/theme.json`: Color palette (hex values), font package, paper size, margins, header title.
- `spec/note-schema.json`: Field definitions and required/optional block rules.
- `library/*.json`: Predefined components, circuit snippets, and trusted references.
- To add a circuit snippet: drop a `.tex` file with `<<param>>` placeholders into `assets/circuits/` and register it in `library/circuits.json`.
