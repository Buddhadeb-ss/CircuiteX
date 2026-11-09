# CircuiteX (circtex)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Antigravity Skill](https://img.shields.io/badge/Antigravity-Skill%20Ready-purple.svg)](https://github.com/Buddhadeb-ss/CircuiteX)

> **Publication-quality LaTeX study notes and Circuitikz schematics compiler for AI coding assistants and ECE students.**

---

## ⚡ The Problem: Why AI Electronics Notes Look Bad

When LLMs are prompted to write LaTeX notes with circuit diagrams:
1. **Blind Coordinate Guessing:** AI cannot visually see TikZ coordinates, resulting in overlapping labels, missing junction dots, floating grounds, and crossing wires without connection dots.
2. **Hallucinated Syntax:** Random symbol names and conflicting packages are invented on the fly.
3. **Preamble Chatter:** LLMs waste precious context tokens explaining their plan before writing any LaTeX.
4. **Fragile Edits:** Modifying a single component in a raw 300-line `.tex` file often breaks the layout.

## 💡 The CircuiteX Solution

CircuiteX replaces blind LaTeX generation with a **structured JSON note specification** and a **deterministic build engine**:

```
AI Agent generates JSON spec  ──▶  CircuiteX Validator  ──▶  LaTeX Engine (pdflatex)  ──▶  PDF & .tex
    (Clean, concise, fast)           (Strict schema check)     (Fixed, vetted preamble)     (Ready to study)
```

- **Predefined Circuit Topology:** Every circuit is drawn from hand-verified snippet templates (`assets/circuits/`).
- **Academic Source Authority:** Formulas and behaviors are mapped strictly to canonical textbooks (Sedra & Smith, Mancini, Razavi, Alexander & Sadiku).
- **Strict Pre-LaTeX Validation:** Catches missing fields, unknown parameters, or invalid snippet IDs before LaTeX ever runs.
- **Human-Editable:** You or the AI edit clean JSON key-values (e.g. resistor values), not raw TikZ coordinates.

---

## 📦 Ready-Made Circuits Library

| Snippet ID | Circuit Description | Canonical Source | Configurable Parameters |
| :--- | :--- | :--- | :--- |
| `inverting-opamp` | Inverting Op-Amp Amplifier | Mancini / TI SLOD006 | `R1`, `Rf` |
| `noninverting-opamp` | Non-Inverting Op-Amp Amplifier | Mancini / TI SLOD006 | `R1`, `Rf` |
| `schmitt-trigger` | Inverting Op-Amp Schmitt Trigger | Sedra & Smith | `R1`, `R2` |
| `mosfet-common-source` | Discrete NMOS Common-Source Stage (4-resistor bias) | Sedra & Smith / Razavi | `RD`, `RS`, `RG1`, `RG2`, `Cin` |
| `common-emitter` | NPN Common-Emitter Stage (voltage-divider bias) | Sedra & Smith | `R1`, `R2`, `RC`, `RE`, `Cin` |
| `rc-lowpass` | 1st-Order Passive RC Low-Pass Filter | Alexander & Sadiku | `R`, `C` |
| `rc-highpass` | 1st-Order Passive RC High-Pass Filter | Alexander & Sadiku | `C`, `R` |
| `voltage-divider` | Resistive Voltage Divider | Alexander & Sadiku | `R1`, `R2` |
| `custom` | Custom Circuitikz block | User-defined | Any circuitikz code |

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

#### Standalone Python CLI
No external Python dependencies needed (standard library only for compilation; `pytest` for running tests):
```bash
git clone https://github.com/Buddhadeb-ss/CircuiteX.git
cd CircuiteX
```

### 2. Compiling Notes

Compile any JSON note into a `.tex` source and compiled PDF:

```bash
# Compile to PDF
python scripts/build.py examples/inverting-amplifier.json --out out/

# Generate .tex only (if pdflatex is not installed)
python scripts/build.py examples/mosfet-amplifier.json --out out/ --no-pdf

# Validate note spec without compiling
python scripts/build.py examples/schmitt-trigger.json --check
```

---

## 📝 Note Spec Example

Here is what an AI or human writes (`inverting-amplifier.json`):

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

## 🎨 Block Types Supported

- `text`: Regular formatted paragraph body.
- `definition`: Colored definition container (`defbox`).
- `formula`: Highlighted equation block with optional explanatory notes (`formulabox`).
- `circuit`: Standard circuit snippet with param overrides, or a verified custom circuitikz block.
- `example`: Step-by-step worked numerical or conceptual example (`examplebox`).
- `warning`: Common pitfalls, design limits, and saturation warnings (`warnbox`).
- `list`: Numbered or bulleted takeaway list.
- `table`: Clean booktabs LaTeX table with caption.
- `summary`: High-level bulleted takeaway box (`summarybox`).
- `check`: Interactive self-check review questions (`checkbox`).

---

## 🛠️ Customization

CircuiteX is built to be customized without touching python code:

- **Theme & Styles (`spec/theme.json`):** Customize accent colors, font packages (e.g. `mathpazo`, `lmodern`), paper geometry, and page headers.
- **Circuit Snippets (`assets/circuits/*.tex`):** Drop any `.tex` file with `<<param>>` placeholders and register it in `library/circuits.json`.
- **Predefined Components (`library/components.json`):** Exact circuitikz macros for resistors, BJTs, MOSFETs, gates, and op-amps.
- **Trusted References (`library/sources.json`):** Add textbooks, course notes, or official component datasheets.

---

## 🧪 Testing

CircuiteX includes comprehensive automated tests covering schema validation, circuit snippet parameter matching, and LaTeX rendering:

```bash
python -m pytest tests/test_circtex.py -v
```

---

## 📦 Packaging Distribution

Create a standalone distributable `.skill` bundle anytime:

```bash
python scripts/package_skill.py
```
This produces `circtex.skill` (a standard zipped skill bundle ready to import into any agent).

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).
Contributions, circuit submissions, and improvements are welcome!

