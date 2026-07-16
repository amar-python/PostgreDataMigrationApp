"""Robust CSV parsing for uploaded migration files.

``CsvParser`` centralises every defensive check that used to be scattered (or
silently swallowed) in ``migration_service._parse_csv_metadata``:

  * zero-byte / header-only files
  * encoding fallback (UTF-8 with BOM → Latin-1) with an explicit warning
  * ragged rows (data rows whose column count differs from the header)
  * suspicious header names that could smuggle SQL fragments into generated
    DDL (``;``, ``--``, quotes, comment markers, DROP/DELETE/... keywords)

The parser never raises for malformed *content* — it returns a
``CsvParseResult`` whose ``issues`` list explains everything found, so the
caller decides whether to reject the file or store it with warnings.
"""
from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass, field
from typing import Optional

# Characters/sequences in a header that are never legitimate column names and
# are classic SQL-injection vectors when identifiers are interpolated in DDL.
_FORBIDDEN_HEADER_PATTERN = re.compile(r"""[;'"`\\]|--|/\*|\*/""")

# Statement keywords that should never appear as a standalone word inside a
# column header (e.g. ``name; DROP TABLE users``).
_FORBIDDEN_KEYWORDS = re.compile(
    r"\b(drop|delete|truncate|insert|update|alter|grant|revoke|exec|execute)\b",
    re.IGNORECASE,
)

# Maximum header length we accept — anything longer is suspicious and would
# exceed PostgreSQL's 63-byte identifier limit anyway.
MAX_HEADER_LENGTH = 128


@dataclass
class CsvIssue:
    """A single problem found while parsing a CSV file."""

    severity: str  # "error" | "warning"
    check: str     # machine-readable check name
    message: str   # human-readable explanation

    def as_dict(self) -> dict:
        return {"severity": self.severity, "check": self.check, "message": self.message}


@dataclass
class CsvParseResult:
    """Outcome of parsing one CSV payload."""

    ok: bool = False
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    columns: Optional[list[str]] = None
    encoding: Optional[str] = None
    issues: list[CsvIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[CsvIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[CsvIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    def columns_json(self) -> Optional[str]:
        """Column names serialised as JSON, matching the legacy DB format."""
        return json.dumps(self.columns) if self.columns is not None else None


class CsvParser:
    """Defensive CSV parser used by the upload pipeline."""

    def __init__(self, max_ragged_examples: int = 5) -> None:
        # How many ragged-row line numbers to include in the issue message.
        self.max_ragged_examples = max_ragged_examples

    # -- decoding ----------------------------------------------------------

    def _decode(self, content: bytes, result: CsvParseResult) -> Optional[str]:
        """Decode bytes to text, preferring UTF-8 (BOM-aware), falling back
        to Latin-1 with a warning. Returns None if undecodable."""
        try:
            result.encoding = "utf-8"
            return content.decode("utf-8-sig")
        except UnicodeDecodeError:
            pass
        try:
            text = content.decode("latin-1")
            result.encoding = "latin-1"
            result.issues.append(CsvIssue(
                severity="warning",
                check="encoding_fallback",
                message="File is not valid UTF-8; decoded as Latin-1. "
                        "Non-ASCII characters may be misinterpreted.",
            ))
            return text
        except UnicodeDecodeError:  # pragma: no cover — latin-1 never fails
            result.issues.append(CsvIssue(
                severity="error",
                check="undecodable",
                message="File could not be decoded as UTF-8 or Latin-1.",
            ))
            return None

    # -- header checks -----------------------------------------------------

    def _check_headers(self, headers: list[str], result: CsvParseResult) -> None:
        for idx, header in enumerate(headers):
            stripped = header.strip()
            if not stripped:
                result.issues.append(CsvIssue(
                    severity="warning",
                    check="empty_header",
                    message=f"Column {idx + 1} has an empty header name.",
                ))
                continue
            if len(stripped) > MAX_HEADER_LENGTH:
                result.issues.append(CsvIssue(
                    severity="error",
                    check="header_too_long",
                    message=f"Header {idx + 1} exceeds {MAX_HEADER_LENGTH} characters.",
                ))
            if _FORBIDDEN_HEADER_PATTERN.search(stripped) or _FORBIDDEN_KEYWORDS.search(stripped):
                result.issues.append(CsvIssue(
                    severity="error",
                    check="suspicious_header",
                    message=(
                        f"Header {idx + 1} ({stripped[:64]!r}) contains characters or "
                        "SQL keywords that are not allowed in column names."
                    ),
                ))

    # -- main entry point ----------------------------------------------------

    def parse(self, content: bytes, filename: str = "upload.csv") -> CsvParseResult:
        """Parse CSV bytes and return a fully-populated ``CsvParseResult``.

        Never raises for malformed content; every problem is reported in
        ``result.issues`` and ``result.ok`` is False when any error exists.
        """
        result = CsvParseResult()

        # 1. Zero-byte / whitespace-only guard
        if not content or not content.strip():
            result.issues.append(CsvIssue(
                severity="error",
                check="empty_file",
                message=f"File {filename!r} is empty (0 bytes of data).",
            ))
            return result

        # 2. Decode with fallback
        text = self._decode(content, result)
        if text is None:
            return result

        # 3. Header row
        reader = csv.reader(io.StringIO(text))
        try:
            headers = next(reader, None)
        except csv.Error as exc:
            result.issues.append(CsvIssue(
                severity="error",
                check="malformed_csv",
                message=f"CSV structure could not be parsed: {exc}",
            ))
            return result

        if not headers or all(not h.strip() for h in headers):
            result.issues.append(CsvIssue(
                severity="error",
                check="missing_header",
                message="No header row found.",
            ))
            return result

        result.columns = [h.strip() for h in headers]
        result.column_count = len(headers)
        self._check_headers(headers, result)

        # 4. Data rows — count and detect ragged rows
        expected = len(headers)
        row_count = 0
        ragged: list[int] = []
        try:
            for line_no, row in enumerate(reader, start=2):
                if not row:  # skip completely blank lines
                    continue
                row_count += 1
                if len(row) != expected:
                    ragged.append(line_no)
        except csv.Error as exc:
            result.issues.append(CsvIssue(
                severity="error",
                check="malformed_csv",
                message=f"CSV structure broke mid-file: {exc}",
            ))
            return result

        result.row_count = row_count
        if ragged:
            sample = ", ".join(map(str, ragged[: self.max_ragged_examples]))
            more = f" (+{len(ragged) - self.max_ragged_examples} more)" \
                if len(ragged) > self.max_ragged_examples else ""
            result.issues.append(CsvIssue(
                severity="error",
                check="ragged_rows",
                message=(
                    f"{len(ragged)} row(s) have a column count different from the "
                    f"header ({expected} expected). Lines: {sample}{more}."
                ),
            ))

        result.ok = not result.errors
        return result
