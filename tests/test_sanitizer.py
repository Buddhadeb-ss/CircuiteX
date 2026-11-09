import re
import pytest

def escape_latex_prose(text):
    if not isinstance(text, str):
        return text
    # Split by display math \[...\], $$, or inline $...$
    pattern = r'(\\\[[\s\S]*?\\\]|\$\$(?:\\.|[^$])*\$\$|\$(?:\\.|[^$])*\$)'
    tokens = re.split(pattern, text)
    result = []
    for token in tokens:
        if not token:
            continue
        if (token.startswith('$') and token.endswith('$') and len(token) >= 2) or \
           (token.startswith(r'\[') and token.endswith(r'\]')):
            result.append(token)
        else:
            t = re.sub(r'(?<!\\)&', r'\&', token)
            t = re.sub(r'(?<!\\)%', r'\%', t)
            t = re.sub(r'(?<!\\)#', r'\#', t)
            t = re.sub(r'(?<!\\)_', r'\_', t)
            result.append(t)
    return ''.join(result)


def test_escape_prose_basic():
    assert escape_latex_prose("R & C") == r"R \& C"
    assert escape_latex_prose("100% duty") == r"100\% duty"
    assert escape_latex_prose("circuit_test") == r"circuit\_test"
    assert escape_latex_prose("item #1") == r"item \#1"


def test_escape_prose_preserves_math():
    res = escape_latex_prose("Gain of 10% with $V_{in} & V_{out}$ and $R_1$")
    assert res == r"Gain of 10\% with $V_{in} & V_{out}$ and $R_1$"


def test_escape_prose_preserves_already_escaped():
    res = escape_latex_prose(r"Already \& and \% and \_ and \#")
    assert res == r"Already \& and \% and \_ and \#"


def test_escape_prose_display_math():
    res = escape_latex_prose(r"Formula for 50% case: \[ A_v = \frac{R_f}{R_1} \] end_of_formula")
    assert res == r"Formula for 50\% case: \[ A_v = \frac{R_f}{R_1} \] end\_of\_formula"
