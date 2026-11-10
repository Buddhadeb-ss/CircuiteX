# CircuiteX Complete Step-by-Step Tutorial

Welcome to the **CircuiteX** tutorial! This guide covers everything from writing your very first note in 60 seconds to creating complex custom circuits (such as digital display decoders), adding new circuits to the library, and using CircuiteX with AI agents.

---

## Table of Contents
1. [Core Concept: Content vs. Rendering](#1-core-concept-content-vs-rendering)
2. [Tutorial 1: Your First Note in 60 Seconds](#2-tutorial-1-your-first-note-in-60-seconds)
3. [Tutorial 2: Using Ready-Made Circuits (Snippet Library)](#3-tutorial-2-using-ready-made-circuits-snippet-library)
4. [Tutorial 3: Unsupported Circuits & Custom Schematics](#4-tutorial-3-unsupported-circuits--custom-schematics)
   - *Example: 3-to-8 Line Decoder for an 8×8 Matrix Display*
5. [Tutorial 4: Rich Blocks (Math, Code, Tables, & Callouts)](#5-tutorial-4-rich-blocks-math-code-tables--callouts)
6. [Tutorial 5: Adding a Permanent Circuit to the Library](#6-tutorial-5-adding-a-permanent-circuit-to-the-library)
7. [Tutorial 6: Prompting AI Agents for Perfect Notes](#7-tutorial-6-prompting-ai-agents-for-perfect-notes)
8. [CLI Reference & Cheat Sheet](#8-cli-reference--cheat-sheet)

---

## 1. Core Concept: Content vs. Rendering

Traditionally, creating LaTeX study notes with circuits required writing hundreds of lines of fragile `.tex` code with manual coordinate placements.

**CircuiteX separates what you study from how it looks:**
* **You write:** A clean, human-readable `.json` specification file describing the concepts, component values, and formulas.
* **CircuiteX does:** Validates your spec, injects hand-checked Circuitikz schematics, auto-escapes LaTeX control characters, and compiles a publication-grade PDF and PNG preview in 2 seconds.

```
┌────────────────────────┐      ┌──────────────────────────┐      ┌────────────────────────┐
│   my-note.json         │ ───▶ │  CircuiteX Build Engine  │ ───▶ │  my-note.pdf + .png    │
│  (Clean, editable JSON)│      │  (Validation & Escaping) │      │  (Publication Quality) │
└────────────────────────┘      └──────────────────────────┘      └────────────────────────┘
```

---

## 2. Tutorial 1: Your First Note in 60 Seconds

Let's create a study sheet for a simple **Voltage Divider**.

### Step 1: Create `voltage-divider-note.json`
Save this file anywhere in your workspace:

```json
{
  "meta": {
    "title": "Resistive Voltage Divider",
    "subject": "Basic Circuit Theory",
    "author": "Your Name",
    "references": ["alexander-sadiku"]
  },
  "sections": [
    {
      "heading": "Theory & Circuit",
      "blocks": [
        {
          "type": "definition",
          "title": "Voltage Divider",
          "body": "A linear circuit that produces an output voltage that is a fraction of its input voltage, determined by the ratio of two series resistors."
        },
        {
          "type": "circuit",
          "snippet": "voltage-divider",
          "params": {
            "R1": "$10\\,\\mathrm{k}\\Omega$",
            "R2": "$20\\,\\mathrm{k}\\Omega$"
          },
          "caption": "Resistive voltage divider with 2:1 ratio"
        },
        {
          "type": "formula",
          "title": "Divider Formula",
          "tex": "V_\\mathrm{out} = V_\\mathrm{in} \\cdot \\frac{R_2}{R_1 + R_2}",
          "note": "Valid when load current is negligible ($R_L \\gg R_2$)."
        }
      ]
    },
    {
      "heading": "Summary & Quick Check",
      "blocks": [
        {
          "type": "summary",
          "points": [
            "Output voltage depends strictly on the resistance ratio, not absolute values.",
            "Loading effect occurs when a finite load resistance draws current from the tap node."
          ]
        },
        {
          "type": "check",
          "questions": [
            "What is Vout if Vin = 12V, R1 = 10k, and R2 = 20k?",
            "How does adding a load resistor RL parallel to R2 affect Vout?"
          ]
        }
      ]
    }
  ]
}
```

### Step 2: Compile to PDF & PNG
Open your terminal and run:

```bash
python scripts/build.py voltage-divider-note.json --out out/ --png
```

You will get:
* `out/voltage-divider-note.pdf` (Clean, vector PDF ready to print or study)
* `out/voltage-divider-note-page1.png` (High-resolution image preview)

---

## 3. Tutorial 2: Using Ready-Made Circuits (Snippet Library)

CircuiteX includes **20 pre-built, hand-checked circuit snippets**. You invoke them by name inside a `circuit` block.

### Example: Customizing Resistor Values in an Op-Amp
```json
{
  "type": "circuit",
  "snippet": "inverting-opamp",
  "params": {
    "R1": "$4.7\\,\\mathrm{k}\\Omega$",
    "Rf": "$47\\,\\mathrm{k}\\Omega$"
  },
  "scale": 0.85,
  "caption": "Inverting amplifier configured for gain Av = -10"
}
```

### Parameter Reference for Common Snippets:
* `inverting-opamp` / `noninverting-opamp`: `R1`, `Rf`
* `schmitt-trigger`: `R1`, `R2`
* `mosfet-common-source`: `RD`, `RS`, `RG1`, `RG2`, `Cin`
* `common-emitter`: `R1`, `R2`, `RC`, `RE`, `Cin`
* `rc-lowpass` / `rc-highpass`: `R`, `C`
* `rlc-bandpass`: `L`, `C`, `R`
* `cmos-inverter`: `MP`, `MN`
* `555-astable`: `RA`, `RB`, `C`

*(See the [README](README.md#comprehensive-circuits-library-20-ready-made-schematics) for the complete list of all 20 snippets).*

---

## 4. Tutorial 3: Unsupported Circuits & Custom Schematics

### What if a user asks for something not in the library?
*Example: A digital 3-to-8 line decoder driving an 8×8 LED matrix display.*

Instead of failing, you provide a **`custom`** circuit block. CircuiteX will compile your raw Circuitikz code with the exact same fonts, colors, and styling as the built-in library!

### Complete Example: 3-to-8 Decoder Note
```json
{
  "meta": {
    "title": "3-to-8 Line Decoder for 8x8 Matrix Display",
    "subject": "Digital Logic Design",
    "author": "Buddhadeb",
    "references": ["mano-digital"]
  },
  "sections": [
    {
      "heading": "Row Scanning Architecture",
      "blocks": [
        {
          "type": "definition",
          "title": "Line Decoder in Matrix Displays",
          "body": "In an 8x8 LED matrix display, row selection is performed by a 3-to-8 line decoder. A 3-bit binary address ($A_2, A_1, A_0$) activates exactly one of the 8 row lines at any given time, enabling sequential time-multiplexed row scanning."
        },
        {
          "type": "circuit",
          "custom": "\\draw (0,2) node[american and port] (G0) {}\\draw (0,0) node[american and port] (G1) {}\\draw (0,-2) node[american and port] (G2) {}\\draw (G0.out) to[short, -o] ++(1.4,0) node[right]{$Y_0 = \\overline{A_2}\\,\\overline{A_1}\\,\\overline{A_0}$ (Row 0)};\\draw (G1.out) to[short, -o] ++(1.4,0) node[right]{$Y_1 = \\overline{A_2}\\,\\overline{A_1}\\,A_0$ (Row 1)};\\draw (G2.out) to[short, -o] ++(1.4,0) node[right]{$Y_7 = A_2 A_1 A_0$ (Row 7)};\\path (G1.south) -- (G2.north) node[midway]{\\huge $\\vdots$};\\draw (G0.in 1) to[short, -o] ++(-1.6,0) node[left]{$A_2$};\\draw (G0.in 2) to[short, -o] ++(-1.6,0) node[left]{$A_1$};",
          "scale": 0.85,
          "caption": "AND-gate decoder stage driving active-HIGH matrix rows"
        },
        {
          "type": "formula",
          "title": "Row Refresh Rate",
          "tex": "f_\\mathrm{frame} = \\frac{f_\\mathrm{scan}}{8} \\ge 60\\,\\mathrm{Hz}",
          "note": "To eliminate visual flicker via persistence of vision, each of the 8 rows must be refreshed at least 60 times per second ($f_\\mathrm{scan} \\ge 480\\,\\mathrm{Hz}$)."
        }
      ]
    }
  ]
}
```

### Golden Rules for Writing Custom Circuits:
1. **Use Relative Offsets**: Write `++(2,0)` instead of scattered absolute coordinates like `(5.7, 3.2)`.
2. **Use Named Anchors**: Connect to component terminals by name (e.g. `(G0.out)`, `(M.D)`, `(A.+)`).
3. **Use the Standard Macros** (from `library/components.json`):
   - Logic gates: `node[american and port]`, `node[american or port]`, `node[not port]`
   - Transistors: `node[nmos]`, `node[pmos]`, `node[npn]`, `node[pnp]`
   - Passive: `to[R=$R_1$]`, `to[C=$C_1$]`, `to[L=$L_1$]`, `to[D=$D_1$]`
4. **Mark Connections**: Use `*-*` or `*-o` to put junction dots where wires meet.
5. **Always Set `scale`**: For diagrams with more than 3 gates, add `"scale": 0.8` or `"scale": 0.75` so they never overflow page margins.

---

## 5. Tutorial 4: Rich Blocks (Math, Code, Tables, & Callouts)

CircuiteX notes support 10 specialized block types to build complete, textbook-grade revision sheets:

### 1. `code` Block (Verilog, C, or SPICE)
Renders clean monospace code with line indentation and syntax-safe character escaping:
```json
{
  "type": "code",
  "title": "Verilog Matrix Scanner",
  "code": "always @(posedge clk) begin\n    row_select <= row_select + 1'b1;\n    row_enable <= (8'b00000001 << row_select);\nend"
}
```

### 2. `table` Block (Comparison Tables)
Generates clean `booktabs` formatted tables:
```json
{
  "type": "table",
  "caption": "Display Scanning Modes",
  "columns": ["Method", "Duty Cycle", "Hardware Complexity", "Peak Current"],
  "rows": [
    ["1:8 Multiplexed", "12.5%", "Low (1 decoder)", "Medium (8x LED current)"],
    ["Static Direct Drive", "100%", "Very High (64 lines)", "Low (Continuous)"]
  ]
}
```

### 3. `warning` Block (Common Mistakes & Limits)
```json
{
  "type": "warning",
  "title": "Ghosting & Reverse Breakdown",
  "body": "Ensure column drivers are blanked during row transitions to avoid faint illumination (ghosting) across adjacent LEDs."
}
```

### 4. `example` Block (Worked Numerical Calculations)
```json
{
  "type": "example",
  "title": "Scan Clock Frequency Calculation",
  "body": "For a flicker-free refresh of $75\\,\\mathrm{Hz}$ across 8 rows: $f_\\mathrm{scan} = 8 \\times 75\\,\\mathrm{Hz} = 600\\,\\mathrm{Hz}$. Each row remains active for $T_\\mathrm{row} = 1/600 \\approx 1.67\\,\\mathrm{ms}$."
}
```

---

## 6. Tutorial 5: Adding a Permanent Circuit to the Library

If you find yourself using a circuit repeatedly, turn it into a permanent reusable library snippet in **under 2 minutes**!

### Step 1: Create the snippet file
Create `assets/circuits/my-filter.tex`:
```latex
\begin{circuitikz}
  \draw (0,0) node[left]{$V_\mathrm{in}$} to[short, o-] (0.8,0)
        to[R=<<R>>] (3.6,0) coordinate(tap)
        to[short, *-o] (5.2,0) node[right]{$V_\mathrm{out}$};
  \draw (tap) to[C=<<C>>] (3.6,-2.2) node[ground]{};
\end{circuitikz}
```

### Step 2: Register it in `library/circuits.json`
Add an entry with its default parameters and academic reference:
```json
"my-filter": {
  "title": "Custom RC Low-Pass Filter",
  "params": {"R": "$R$", "C": "$C$"},
  "topics": ["rc", "filters"],
  "source": "alexander-sadiku"
}
```

### Step 3: Run the test suite
```bash
python -m pytest tests/ -v
```
If your circuit compiles cleanly, it is now a permanent part of the library!

---

## 7. Tutorial 6: Prompting AI Agents for Perfect Notes

When using CircuiteX with **Google Antigravity**, **Claude Code**, **Cursor**, or **ChatGPT**, use these effective prompt patterns:

### Pattern 1: Topic with Component Values
> *"Create a CircuiteX study sheet for an Op-Amp Inverting Amplifier. Set R1 = 10k, Rf = 100k. Include the closed-loop gain formula, an input impedance warning, and a worked numerical example."*

### Pattern 2: Unsupported Topic / Digital Circuit
> *"Use CircuiteX to generate notes on an 8x8 LED matrix display driver. Include a custom Circuitikz block for the 3-to-8 row decoder, scan timing calculations, and Verilog HDL scanning code."*

### Pattern 3: Comparison Study Sheet
> *"Generate a revision sheet comparing BJT Common-Emitter vs. MOSFET Common-Source stages. Include schematics for both, small-signal gain formulas, and a comparison table of input/output impedances."*

---

## 8. CLI Reference & Cheat Sheet

```bash
# Standard compilation (outputs .tex and .pdf):
python scripts/build.py note.json --out out/

# Compile with high-resolution PNG page previews:
python scripts/build.py note.json --out out/ --png

# Validate JSON specification without compiling:
python scripts/build.py note.json --check

# Generate LaTeX (.tex) only without PDF compiler:
python scripts/build.py note.json --no-pdf

# Live Watch Mode (auto-recompiles whenever you save the JSON):
python scripts/build.py note.json --watch --out out/

# Auto-install portable Tectonic compiler if missing:
python scripts/build.py note.json --auto-install-compiler

# Re-package the distributable .skill archive:
python scripts/package_skill.py
```
