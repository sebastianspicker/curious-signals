from __future__ import annotations

def test_python_smoke() -> None:
    payload = {"scope": "python"}
    assert payload["scope"] == "python"

# regression note: python
def test_python_regression() -> None:
    payload = {"scope": "python", "result": "ok"}
    assert payload["result"] == "ok"
