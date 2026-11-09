import json
import pytest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build


@pytest.fixture
def circuits_registry():
    return build.load_json("library/circuits.json")["circuits"]


def test_every_circuit_compiles_to_pdf(tmp_path, circuits_registry):
    for cid, cinfo in circuits_registry.items():
        spec = {
            "meta": {
                "title": f"Circuit Test: {cinfo['title']}",
                "subject": "Automated Circuit Verification",
                "author": "CircuiteX CI",
                "references": [cinfo["source"]],
            },
            "sections": [
                {
                    "heading": "Schematic",
                    "blocks": [
                        {
                            "type": "definition",
                            "title": cinfo["title"],
                            "body": f"Automated test for circuit snippet {cid} with default parameters.",
                        },
                        {
                            "type": "circuit",
                            "snippet": cid,
                            "caption": cinfo["title"],
                        },
                    ],
                }
            ],
        }
        test_json = tmp_path / f"test_{cid}.json"
        test_json.write_text(json.dumps(spec), encoding="utf-8")

        # Compile to PDF
        code = build.build(str(test_json), out_dir=str(tmp_path), compile_pdf=True)
        assert code == 0, f"Compilation failed for circuit snippet '{cid}'"
        pdf_out = tmp_path / f"test_{cid}.pdf"
        assert pdf_out.exists(), f"PDF not generated for '{cid}'"
        assert pdf_out.stat().st_size > 5000, f"PDF file size too small for '{cid}'"
