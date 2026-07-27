"""CLI tests for tools/validate_phyphox.py."""

from __future__ import annotations

from pathlib import Path

from validate_phyphox import main

from tests.test_phyphox_validate import MINIMAL_VALID_XML

REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIR = REPO_ROOT / "experiments"


class TestMainCli:
    """Tests for the validate_phyphox.main() CLI entry point."""

    def test_valid_generated_file_returns_zero(self) -> None:
        """main() with a known-good generated experiment should return 0."""
        sample = next(GENERATED_DIR.glob("*.phyphox"), None)
        assert sample is not None, "No generated .phyphox files found in experiments/"
        assert main([str(sample)]) == 0

    def test_invalid_file_returns_one_and_prints_to_stderr(self, tmp_path, capsys) -> None:
        """main() with a file that fails validation should return 1 and print errors."""
        bad_xml = MINIMAL_VALID_XML.replace(
            'char="cddf1002-30f7-4671-8b43-5e40ba53514a"',
            'char="deadbeef-0000-0000-0000-000000000000"',
        )
        path = tmp_path / "invalid.phyphox"
        path.write_text(bad_xml, encoding="utf-8")
        result = main([str(path)])
        captured = capsys.readouterr()
        assert result == 1
        assert captured.err  # at least one error line must appear on stderr

    def test_nonexistent_path_returns_one(self, capsys) -> None:
        """main() with a path that does not exist should return 1."""
        result = main(["/nonexistent/path/that/cannot/exist.phyphox"])
        captured = capsys.readouterr()
        assert result == 1
        assert captured.err

    def test_multiple_valid_files_all_pass(self) -> None:
        """main() accepts multiple file arguments and passes when all are valid."""
        samples = list(GENERATED_DIR.glob("*.phyphox"))
        assert samples, "No generated .phyphox files found in experiments/"
        assert main([str(p) for p in samples]) == 0
