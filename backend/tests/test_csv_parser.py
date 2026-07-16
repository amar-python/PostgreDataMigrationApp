"""Unit tests for services.csv_parser.CsvParser.

Covers the failure modes the parser must handle defensively:
zero-byte files, ragged rows, encoding mismatches, and malicious
(SQL-injection-style) header names.
"""
import json

import pytest

from services.csv_parser import CsvParser


@pytest.fixture
def parser() -> CsvParser:
    return CsvParser()


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

class TestHappyPath:

    def test_simple_csv(self, parser):
        result = parser.parse(b"id,name,email\n1,Alice,a@x.com\n2,Bob,b@x.com\n")
        assert result.ok
        assert result.row_count == 2
        assert result.column_count == 3
        assert result.columns == ["id", "name", "email"]
        assert result.encoding == "utf-8"
        assert result.issues == []

    def test_utf8_bom_is_stripped(self, parser):
        result = parser.parse("id,name\n1,Ünïcode\n".encode("utf-8-sig"))
        assert result.ok
        assert result.columns == ["id", "name"]
        assert result.row_count == 1

    def test_columns_json_matches_legacy_format(self, parser):
        result = parser.parse(b"a,b\n1,2\n")
        assert json.loads(result.columns_json()) == ["a", "b"]

    def test_blank_lines_are_skipped(self, parser):
        result = parser.parse(b"a,b\n1,2\n\n\n3,4\n")
        assert result.ok
        assert result.row_count == 2

    def test_quoted_fields_with_commas(self, parser):
        result = parser.parse(b'id,note\n1,"hello, world"\n')
        assert result.ok
        assert result.row_count == 1


# ---------------------------------------------------------------------------
# Zero-byte / empty files
# ---------------------------------------------------------------------------

class TestEmptyFiles:

    def test_zero_byte_file(self, parser):
        result = parser.parse(b"", "empty.csv")
        assert not result.ok
        assert result.row_count is None
        assert any(i.check == "empty_file" for i in result.errors)

    def test_whitespace_only_file(self, parser):
        result = parser.parse(b"   \n  \n", "blank.csv")
        assert not result.ok
        assert any(i.check == "empty_file" for i in result.errors)

    def test_header_only_file_is_ok_with_zero_rows(self, parser):
        result = parser.parse(b"id,name\n")
        assert result.ok
        assert result.row_count == 0
        assert result.column_count == 2


# ---------------------------------------------------------------------------
# Ragged rows (inconsistent column counts)
# ---------------------------------------------------------------------------

class TestRaggedRows:

    def test_row_with_too_few_columns(self, parser):
        result = parser.parse(b"a,b,c\n1,2,3\n1,2\n")
        assert not result.ok
        issue = next(i for i in result.errors if i.check == "ragged_rows")
        assert "1 row(s)" in issue.message
        assert "3" in issue.message  # line number of the bad row

    def test_row_with_too_many_columns(self, parser):
        result = parser.parse(b"a,b\n1,2\n1,2,3,4\n")
        assert not result.ok
        assert any(i.check == "ragged_rows" for i in result.errors)

    def test_multiple_ragged_rows_reported_with_line_numbers(self, parser):
        content = b"a,b\n" + b"1\n" * 10
        result = parser.parse(content)
        assert not result.ok
        issue = next(i for i in result.errors if i.check == "ragged_rows")
        assert "10 row(s)" in issue.message
        assert "more" in issue.message  # truncated example list

    def test_consistent_rows_have_no_ragged_issue(self, parser):
        result = parser.parse(b"a,b\n1,2\n3,4\n")
        assert not any(i.check == "ragged_rows" for i in result.issues)


# ---------------------------------------------------------------------------
# Encoding mismatches
# ---------------------------------------------------------------------------

class TestEncodingMismatch:

    def test_latin1_falls_back_with_warning(self, parser):
        content = "id,name\n1,Caf\xe9\n".encode("latin-1")  # 0xE9 is invalid UTF-8
        result = parser.parse(content)
        assert result.ok  # decodable, so parse succeeds…
        assert result.encoding == "latin-1"
        assert any(i.check == "encoding_fallback" for i in result.warnings)

    def test_utf16_content_is_not_silently_accepted(self, parser):
        content = "id,name\n1,Alice\n".encode("utf-16")
        result = parser.parse(content)
        # UTF-16 bytes decode as latin-1 garbage — the fallback warning must fire
        assert any(i.check == "encoding_fallback" for i in result.warnings)

    def test_valid_utf8_has_no_encoding_warning(self, parser):
        result = parser.parse("id,name\n1,Zoë\n".encode("utf-8"))
        assert result.ok
        assert result.encoding == "utf-8"
        assert not result.warnings


# ---------------------------------------------------------------------------
# Malicious / SQL-injection-style headers
# ---------------------------------------------------------------------------

class TestMaliciousHeaders:

    @pytest.mark.parametrize("header", [
        "name; DROP TABLE users",
        "name;--",
        "name'--",
        'name"',
        "name/*comment*/",
        "DROP",
        "1; DELETE FROM runs",
        "col`name",
        "a\\b",
    ])
    def test_injection_symbols_are_flagged(self, parser, header):
        content = f"id,{header}\n1,x\n".encode("utf-8")
        result = parser.parse(content)
        assert not result.ok, f"header {header!r} should be rejected"
        assert any(i.check == "suspicious_header" for i in result.errors)

    @pytest.mark.parametrize("header", [
        "name", "first_name", "e-mail", "Order Total", "année", "drop_zone_id",
    ])
    def test_legitimate_headers_are_allowed(self, parser, header):
        content = f"id,{header}\n1,x\n".encode("utf-8")
        result = parser.parse(content)
        assert result.ok, f"header {header!r} should be accepted"

    def test_overlong_header_is_rejected(self, parser):
        long_header = "h" * 200
        result = parser.parse(f"id,{long_header}\n1,x\n".encode("utf-8"))
        assert not result.ok
        assert any(i.check == "header_too_long" for i in result.errors)

    def test_empty_header_produces_warning(self, parser):
        result = parser.parse(b"id,,name\n1,2,3\n")
        assert any(i.check == "empty_header" for i in result.warnings)
