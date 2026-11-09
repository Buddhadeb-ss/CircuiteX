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
    schema = build.load("spec/note-schema.json")
    circuits = build.load("library/circuits.json")["circuits"]
    sources = build.load("library/sources.json")["sources"]
    theme = build.load("spec/theme.json")
    comps = build.load("library/components.json")
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
    for btype in ["text", "definition", "formula", "circuit", "table", "summary", "check"]:
        assert btype in schema["blocks"]


def test_all_snippets_exist_and_match_params(loaded_library):
    circuits = loaded_library["circuits"]
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
    assert len(examples) >= 3, "Expected at least 3 examples"
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


def test_validation_catches_unknown_meta_field(loaded_library):
    schema = loaded_library["schema"]
    circuits = loaded_library["circuits"]
    sources = loaded_library["sources"]
    bad_spec = {
        "meta": {"title": "Test", "bogus_field": "val"},
        "sections": [{"heading": "Sec1", "blocks": [{"type": "text", "body": "hello"}]}],
    }
    errs = build.validate(bad_spec, schema, circuits, sources)
    assert any("unknown field 'bogus_field'" in e for e in errs)


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


def test_validation_catches_bad_reference(loaded_library):
    schema = loaded_library["schema"]
    circuits = loaded_library["circuits"]
    sources = loaded_library["sources"]
    bad_spec = {
        "meta": {"title": "Test", "references": ["made-up-book"]},
        "sections": [{"heading": "Sec1", "blocks": [{"type": "text", "body": "hello"}]}],
    }
    errs = build.validate(bad_spec, schema, circuits, sources)
    assert any("meta.references: 'made-up-book' not in library/sources.json" in e for e in errs)


def test_build_generates_tex_for_all_examples(tmp_path):
    examples = list((ROOT / "examples").glob("*.json"))
    for ex in examples:
        code = build.build(str(ex), out_dir=str(tmp_path), compile_pdf=False)
        assert code == 0, f"build failed for {ex.name}"
        tex_file = tmp_path / f"{ex.stem}.tex"
        assert tex_file.exists(), f"Tex file not created for {ex.name}"
        content = tex_file.read_text(encoding="utf-8")
        assert "\\documentclass" in content
        assert "\\begin{document}" in content
        assert "\\end{document}" in content
        assert "\\begin{circuitikz}" in content


def test_cli_check_flag():
    example = ROOT / "examples" / "inverting-amplifier.json"
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build.py"), str(example), "--check"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0
    assert "VALID:" in r.stdout
