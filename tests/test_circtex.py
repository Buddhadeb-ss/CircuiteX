import json
import subprocess
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build


@pytest.fixture
def loaded_library():
    schema = build.load_json("spec/note-schema.json")
    circuits = build.load_json("library/circuits.json")["circuits"]
    sources = build.load_json("library/sources.json")["sources"]
    theme = build.load_json("spec/theme.json")
    comps = build.load_json("library/components.json")
    return {
        "schema": schema,
        "circuits": circuits,
        "sources": sources,
        "theme": theme,
        "comps": comps,
    }


def test_schema_structure(loaded_library):
    schema = loaded_library["schema"]
    assert "meta" in schema
    assert "title" in schema["meta"]["required"]
    assert "blocks" in schema
    for btype in ["text", "definition", "formula", "circuit", "code", "table", "summary", "check"]:
        assert btype in schema["blocks"]


def test_all_snippets_exist_and_match_params(loaded_library):
    circuits = loaded_library["circuits"]
    assert len(circuits) >= 20, f"Expected at least 20 circuits, got {len(circuits)}"
    for cid, cdata in circuits.items():
        tex_path = ROOT / "assets" / "circuits" / f"{cid}.tex"
        assert tex_path.exists(), f"Snippet file missing for {cid}: {tex_path}"
        content = tex_path.read_text(encoding="utf-8")
        assert "\\begin{circuitikz}" in content
        assert "\\end{circuitikz}" in content
        for param in cdata["params"]:
            assert f"<<{param}>>" in content, f"Param <<{param}>> not found in {cid}.tex"


def test_all_examples_validate_cleanly(loaded_library):
    schema = loaded_library["schema"]
    circuits = loaded_library["circuits"]
    sources = loaded_library["sources"]
    examples = list((ROOT / "examples").glob("*.json"))
    assert len(examples) >= 4, "Expected at least 4 examples"
    for ex in examples:
        spec = json.loads(ex.read_text(encoding="utf-8"))
        errs = build.validate(spec, schema, circuits, sources)
        assert errs == [], f"Validation errors in {ex.name}: {errs}"


def test_validation_catches_missing_required_meta(loaded_library):
    schema = loaded_library["schema"]
    circuits = loaded_library["circuits"]
    sources = loaded_library["sources"]
    bad_spec = {
        "meta": {"subject": "Electronics"},
        "sections": [{"heading": "Sec1", "blocks": [{"type": "text", "body": "hello"}]}],
    }
    errs = build.validate(bad_spec, schema, circuits, sources)
    assert any("meta: missing required 'title'" in e for e in errs)


def test_validation_catches_type_mismatches(loaded_library):
    schema = loaded_library["schema"]
    circuits = loaded_library["circuits"]
    sources = loaded_library["sources"]
    bad_spec = {
        "meta": {"title": "Test"},
        "sections": [
            {
                "heading": "Sec1",
                "blocks": [
                    {"type": "list", "items": "not-a-list"},
                    {"type": "summary", "points": "not-a-list"},
                ],
            }
        ],
    }
    errs = build.validate(bad_spec, schema, circuits, sources)
    assert any("'items' must be a list" in e for e in errs)
    assert any("'points' must be a list" in e for e in errs)


def test_validation_catches_bad_snippet(loaded_library):
    schema = loaded_library["schema"]
    circuits = loaded_library["circuits"]
    sources = loaded_library["sources"]
    bad_spec = {
        "meta": {"title": "Test"},
        "sections": [
            {
                "heading": "Sec1",
                "blocks": [{"type": "circuit", "snippet": "phantom-circuit"}],
            }
        ],
    }
    errs = build.validate(bad_spec, schema, circuits, sources)
    assert any("snippet 'phantom-circuit' not in library/circuits.json" in e for e in errs)


def test_validation_catches_unknown_circuit_param(loaded_library):
    schema = loaded_library["schema"]
    circuits = loaded_library["circuits"]
    sources = loaded_library["sources"]
    bad_spec = {
        "meta": {"title": "Test"},
        "sections": [
            {
                "heading": "Sec1",
                "blocks": [
                    {
                        "type": "circuit",
                        "snippet": "rc-lowpass",
                        "params": {"INVALID_PARAM": "100"},
                    }
                ],
            }
        ],
    }
    errs = build.validate(bad_spec, schema, circuits, sources)
    assert any("unknown params ['INVALID_PARAM']" in e for e in errs)


def test_circuit_scale_support(tmp_path):
    spec = {
        "meta": {"title": "Scale Test"},
        "sections": [
            {
                "heading": "Scaled Circuit",
                "blocks": [
                    {
                        "type": "circuit",
                        "snippet": "rc-lowpass",
                        "scale": 0.85,
                        "caption": "Scaled 85%",
                    }
                ],
            }
        ],
    }
    spec_path = tmp_path / "scale_test.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    code = build.build(str(spec_path), out_dir=str(tmp_path), compile_pdf=False)
    assert code == 0
    tex_content = (tmp_path / "scale_test.tex").read_text(encoding="utf-8")
    assert "scale=0.85, transform shape" in tex_content


def test_code_block_support(tmp_path):
    spec = {
        "meta": {"title": "Code Block Test"},
        "sections": [
            {
                "heading": "Verilog Module",
                "blocks": [
                    {
                        "type": "code",
                        "title": "Inverter Module",
                        "code": "module inv(input a, output y);\n  assign y = ~a;\nendmodule",
                    }
                ],
            }
        ],
    }
    spec_path = tmp_path / "code_test.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    code = build.build(str(spec_path), out_dir=str(tmp_path), compile_pdf=False)
    assert code == 0
    tex_content = (tmp_path / "code_test.tex").read_text(encoding="utf-8")
    assert "\\begin{codebox}" in tex_content
    assert "module inv" in tex_content


def test_prose_sanitizer_in_build(tmp_path):
    spec = {
        "meta": {
            "title": "Design #1: RC & RLC with 50% Duty",
            "subject": "Author_Name_Test",
        },
        "sections": [
            {
                "heading": "Analysis & Simulation (100% Verified)",
                "blocks": [
                    {
                        "type": "text",
                        "body": "Testing bare & and % and # and _ without breaking LaTeX.",
                    }
                ],
            }
        ],
    }
    spec_path = tmp_path / "sanitize_test.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    code = build.build(str(spec_path), out_dir=str(tmp_path), compile_pdf=False)
    assert code == 0
    tex_content = (tmp_path / "sanitize_test.tex").read_text(encoding="utf-8")
    assert r"RC \& RLC" in tex_content
    assert r"50\%" in tex_content
    assert r"\#1" in tex_content
    assert r"Author\_Name\_Test" in tex_content
