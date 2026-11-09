# CircuiteX (circtex)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Antigravity Skill](https://img.shields.io/badge/Antigravity-Skill%20Ready-purple.svg)](https://github.com/Buddhadeb-ss/CircuiteX)
[![Tests Passing](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)

> **Publication-quality LaTeX study notes and Circuitikz schematics compiler for AI coding assistants and ECE students.**

---

## ⚡ The Problem: Why AI Electronics Notes Look Bad

When LLMs are prompted to write LaTeX notes with circuit diagrams:
1. **Blind Coordinate Guessing:** AI cannot visually see TikZ coordinates, resulting in overlapping labels, missing junction dots, floating grounds, and crossing wires without connection dots.
2. **Character Collisions:** Bare characters like `&` in headings, `%` in percentages, or `_` in names crash `pdflatex` instantly.
3. **Preamble Chatter:** LLMs waste precious context tokens explaining their plan before writing any LaTeX.
4. **Fragile Edits:** Modifying a single component in a raw 300-line `.tex` file often breaks the layout.

## 💡 The CircuiteX Solution

CircuiteX replaces blind LaTeX generation with a **structured JSON note specification** and a **deterministic, fail-proof build engine**:

```
AI Agent generates JSON spec  ──▶  CircuiteX Validator  ──▶  LaTeX Engine (Tectonic / pdflatex)  ──▶  PDF & PNG
    (Clean, concise, fast)           (Strict schema check)         (Fixed, vetted preamble)          (Ready to study)
```

- **20+ Predefined Circuit Topologies:** Every circuit is drawn from hand-verified snippet templates (`assets/circuits/`).
- **Academic Source Authority:** Formulas and behaviors are mapped strictly to canonical textbooks (Sedra & Smith, Mancini, Razavi, Alexander & Sadiku).
- **Fail-Proof Auto-Escaping:** Automatically sanitizes bare characters (`&`, `%`, `#`, `_`) in titles, headings, and prose while preserving exact math mode (`$...$`, `$$...$$`, `\[...\]`).
- **Self-Contained Compiler:** Automatically detects local `pdflatex` or portable `tectonic` (zero-setup cross-platform TeX engine).
- **Human-Editable:** You or the AI edit clean JSON key-values (e.g. resistor values), not raw TikZ coordinates.

---

## 📦 Comprehensive Circuits Library (20 Ready-Made Schematics)

| Category | Snippet ID | Circuit Description | Canonical Source | Configurable Parameters |
| :--- | :--- | :--- | :--- | :--- |
| **Op-Amps** | `inverting-opamp` | Inverting Op-Amp Amplifier | Mancini / TI SLOD006 | `R1`, `Rf` |
| | `noninverting-opamp` | Non-Inverting Op-Amp Amplifier | Mancini / TI SLOD006 | `R1`, `Rf` |
| | `summing-amplifier` | 3-Input Inverting Summing Amplifier | Mancini / TI SLOD006 | `R1`, `R2`, `R3`, `Rf` |
| | `difference-amplifier` | 4-Resistor Difference Amplifier | Mancini / TI SLOD006 | `R1`, `R2`, `R3`, `R4` |
| | `opamp-integrator` | Ideal Inverting Integrator Stage | Sedra & Smith | `R1`, `Cf` |
| | `opamp-differentiator` | Ideal Inverting Differentiator Stage | Sedra & Smith | `C1`, `Rf` |
| | `schmitt-trigger` | Inverting Schmitt Trigger with Hysteresis | Sedra & Smith | `R1`, `R2` |
| **Transistors** | `common-emitter` | NPN Common-Emitter Stage (divider bias) | Sedra & Smith | `R1`, `R2`, `RC`, `RE`, `Cin` |
| | `bjt-common-collector` | NPN Common-Collector Buffer (Emitter Follower) | Sedra & Smith | `R1`, `R2`, `RE`, `Cin` |
| | `mosfet-common-source` | NMOS Common-Source Stage (divider bias) | Sedra & Smith / Razavi | `RD`, `RS`, `RG1`, `RG2`, `Cin` |
| | `mosfet-source-follower` | NMOS Common-Drain Buffer (Source Follower) | Razavi | `RG1`, `RG2`, `RS`, `Cin` |
| **Filters** | `rc-lowpass` | 1st-Order Passive RC Low-Pass Filter | Alexander & Sadiku | `R`, `C` |
| | `rc-highpass` | 1st-Order Passive RC High-Pass Filter | Alexander & Sadiku | `C`, `R` |
| | `rlc-bandpass` | Series RLC Resonant Band-Pass Filter | Alexander & Sadiku | `L`, `C`, `R` |
| | `voltage-divider` | Resistive Voltage Divider | Alexander & Sadiku | `R1`, `R2` |
| **Diodes & Power**| `half-wave-rectifier` | Half-Wave Rectifier with Filter Cap & Load | Sedra & Smith | `D1`, `CL`, `RL` |
| | `full-wave-bridge-rectifier` | Full-Wave 4-Diode Bridge Rectifier | Sedra & Smith | `D1`, `D2`, `D3`, `D4`, `RL` |
| | `zener-voltage-regulator` | Zener Diode Shunt Voltage Regulator | Sedra & Smith | `Rs`, `DZ`, `RL` |
| **Digital & ICs** | `cmos-inverter` | Static CMOS Inverter (PMOS + NMOS) | Sedra & Smith | `MP`, `MN` |
| | `555-astable` | NE555 Timer in Astable Multivibrator Mode | Sedra & Smith | `RA`, `RB`, `C` |
| **Custom** | `custom` | Custom raw Circuitikz schematic | User-defined | Any circuitikz syntax |

---

## 🚀 Quick Start

### 1. Installation

#### In Google Antigravity (as a Skill)
Clone directly into your project's workspace:
```bash
git clone https://github.com/Buddhadeb-ss/CircuiteX.git .agents/skills/circtex
```
Or install globally across all workspaces:
```bash
# Windows
git clone https://github.com/Buddhadeb-ss/CircuiteX.git "$env:USERPROFILE\.gemini\config\skills\circtex"

# Linux / macOS
git clone https://github.com/Buddhadeb-ss/CircuiteX.git ~/.gemini/config/skills/circtex
```

#### Standalone CLI Setup
```bash
git clone https://github.com/Buddhadeb-ss/CircuiteX.git
cd CircuiteX

# (Optional) Install portable Tectonic compiler if pdflatex is not installed:
python scripts/setup_compiler.py
```

---

### 2. Compiling Notes

Compile any JSON note into `.tex`, `.pdf`, and `.png` page previews:

```bash
# Compile to PDF with automatic PNG preview images:
python scripts/build.py examples/inverting-amplifier.json --out out/ --png

# Compile MOSFET common-source notes:
python scripts/build.py examples/mosfet-amplifier.json --out out/ --png

# Compile CMOS digital inverter notes with Verilog code:
python scripts/build.py examples/cmos-inverter.json --out out/ --png

# Validate note specification without compiling:
python scripts/build.py examples/schmitt-trigger.json --check

# Watch mode (automatically rebuilds on file save):
python scripts/build.py examples/inverting-amplifier.json --watch --out out/
```

---

## 📝 Note Spec Example (`inverting-amplifier.json`)

```json
{
  "meta": {
    "title": "Inverting Op-Amp Amplifier",
    "subject": "Analog Electronics",
    "author": "Buddhadeb",
    "references": ["mancini-opamps", "sedra-smith"]
  },
  "sections": [
    {
      "heading": "Concept & Topology",
      "blocks": [
        {
          "type": "definition",
          "title": "Inverting Amplifier",
          "body": "An op-amp configuration where input signal enters the inverting terminal through $R_1$, feedback resistor $R_f$ connects output back to the input, and the non-inverting terminal is tied to ground."
        },
        {
          "type": "circuit",
          "snippet": "inverting-opamp",
          "params": {"R1": "$10\\,\\mathrm{k}\\Omega$", "Rf": "$100\\,\\mathrm{k}\\Omega$"},
          "scale": 0.9,
          "caption": "Inverting amplifier with closed-loop gain $A_v = -10$"
        },
        {
          "type": "formula",
          "title": "Closed-Loop Gain",
          "tex": "A_v = \\frac{V_\\mathrm{out}}{V_\\mathrm{in}} = -\\frac{R_f}{R_1}",
          "note": "Derived from the virtual ground approximation at the inverting terminal."
        }
      ]
    },
    {
      "heading": "Summary & Check",
      "blocks": [
        {
          "type": "summary",
          "points": [
            "Gain is solely determined by external resistor ratio $R_f / R_1$.",
            "Inverting terminal acts as a virtual ground ($V_- \\approx 0\\,\\mathrm{V}$).",
            "Output is $180^\\circ$ out of phase with input."
          ]
        },
        {
          "type": "check",
          "questions": [
            "What is the input resistance seen by the signal source?",
            "How does finite open-loop gain $A_0$ affect the actual closed-loop gain?"
          ]
        }
      ]
    }
  ]
}
```

---

## 🎨 Supported Block Types

- `text`: Regular narrative prose with auto-escaping.
- `definition`: Conceptual definition container (`defbox`).
- `formula`: Centered display equation with optional explanatory note (`formulabox`).
- `circuit`: Circuit diagram from library (`snippet`) or raw circuitikz (`custom`). Supports `scale` (e.g. `0.85`).
- `code`: Monospace syntax-highlighted code block (`codebox`) for Verilog, C, or SPICE netlists.
- `example`: Step-by-step worked numerical or conceptual example (`examplebox`).
- `warning`: Common pitfalls, design limits, and saturation warnings (`warnbox`).
- `list`: Numbered or bulleted takeaway list.
- `table`: Clean booktabs LaTeX table with caption.
- `summary`: High-level bulleted takeaway box (`summarybox`).
- `check`: Interactive self-check review questions (`checkbox`).

---

## 🧪 Comprehensive Automated Testing

CircuiteX includes a rigorous test suite that verifies schema rules, parameter bindings, prose sanitization, and compiles all 20 circuits to PDF:

```bash
python -m pytest tests/ -v
```

---

## 📦 Packaging Distribution

Create a standalone distributable `.skill` bundle anytime:

```bash
python scripts/package_skill.py
```
This produces `circtex.skill` containing all 20 circuits, schemas, templates, build engines, and examples.

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).
Contributions, circuit submissions, and improvements are welcome!
