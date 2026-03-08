"""Field parsing for structured documents."""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional


class FieldParser:
    """Parser for extracting structured fields from documents."""

    # Field patterns for different document types
    FIELD_PATTERNS = {
        "passport_number": r"\b[A-Z]{1,2}\d{6,9}\b",
        "date": r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b",
        "amount": r"\d+(?:[.,]\d{2})?",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    }

    @staticmethod
    def parse_passport(text: str) -> Dict[str, str]:
        """
        Parse passport document fields.

        Args:
            text: OCR text from passport

        Returns:
            Dictionary of extracted fields
        """
        fields = {
            "surname": "",
            "given_names": "",
            "passport_number": "",
            "date_of_birth": "",
            "date_of_issue": "",
            "date_of_expiry": "",
            "nationality": "",
        }

        lines = text.split("\n")

        for i, line in enumerate(lines):
            line_lower = line.lower()

            # Surname
            if "surname" in line_lower or "фамилия" in line_lower:
                fields["surname"] = FieldParser._extract_value_after_keyword(lines, i)

            # Given names
            elif "given name" in line_lower or "имя" in line_lower:
                fields["given_names"] = FieldParser._extract_value_after_keyword(
                    lines, i
                )

            # Passport number
            elif "passport" in line_lower and "number" in line_lower:
                fields["passport_number"] = FieldParser._extract_value_after_keyword(
                    lines, i
                )

            # Date of birth
            elif "birth" in line_lower or "рождения" in line_lower:
                fields["date_of_birth"] = FieldParser._extract_date(lines, i)

            # Issue date
            elif "issue" in line_lower or "выдачи" in line_lower:
                fields["date_of_issue"] = FieldParser._extract_date(lines, i)

            # Expiry date
            elif "expir" in line_lower or "действия" in line_lower:
                fields["date_of_expiry"] = FieldParser._extract_date(lines, i)

        return fields

    @staticmethod
    def parse_invoice(text: str) -> Dict[str, Any]:
        """
        Parse invoice document fields.

        Args:
            text: OCR text from invoice

        Returns:
            Dictionary of extracted fields
        """
        fields = {
            "invoice_number": "",
            "invoice_date": "",
            "due_date": "",
            "vendor_name": "",
            "total_amount": "",
            "currency": "",
            "items": [],
        }

        lines = text.split("\n")

        for i, line in enumerate(lines):
            line_lower = line.lower()

            # Invoice number
            if "invoice" in line_lower and "number" in line_lower:
                fields["invoice_number"] = FieldParser._extract_value_after_keyword(
                    lines, i
                )

            # Dates
            elif "invoice date" in line_lower:
                fields["invoice_date"] = FieldParser._extract_date(lines, i)

            elif "due date" in line_lower:
                fields["due_date"] = FieldParser._extract_date(lines, i)

            # Total
            elif "total" in line_lower or "amount" in line_lower:
                amount_match = re.search(r"([\$€£¥₽])\s?(\d+(?:[.,]\d+)?)", line)
                if amount_match:
                    fields["currency"] = amount_match.group(1)
                    fields["total_amount"] = amount_match.group(2)

        return fields

    @staticmethod
    def parse_receipt(text: str) -> Dict[str, Any]:
        """
        Parse receipt document fields.

        Args:
            text: OCR text from receipt

        Returns:
            Dictionary of extracted fields
        """
        fields = {
            "store_name": "",
            "date": "",
            "time": "",
            "total": "",
            "items": [],
            "payment_method": "",
        }

        lines = text.split("\n")

        # Store name is usually at the top
        if lines:
            fields["store_name"] = lines[0].strip()

        for line in lines:
            # Extract date
            date_match = re.search(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b", line)
            if date_match:
                fields["date"] = date_match.group()

            # Extract time
            time_match = re.search(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", line)
            if time_match:
                fields["time"] = time_match.group()

            # Extract total
            if "total" in line.lower():
                amount_match = re.search(r"\d+[.,]\d{2}", line)
                if amount_match:
                    fields["total"] = amount_match.group()

        return fields

    @staticmethod
    def _extract_value_after_keyword(lines: List[str], index: int) -> str:
        """Extract value from same line or next line after keyword."""
        if index >= len(lines):
            return ""

        line = lines[index]

        # Try to extract from same line after colon or dash
        match = re.search(r"[:-]\s*(.+)$", line)
        if match:
            return match.group(1).strip()

        # Try next line
        if index + 1 < len(lines):
            return lines[index + 1].strip()

        return ""

    @staticmethod
    def _extract_date(lines: List[str], index: int) -> str:
        """Extract date from line or surrounding lines."""
        # Check current line
        if index < len(lines):
            date_match = re.search(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b", lines[index])
            if date_match:
                return date_match.group()

        # Check next line
        if index + 1 < len(lines):
            date_match = re.search(
                r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b", lines[index + 1]
            )
            if date_match:
                return date_match.group()

        return ""

    @staticmethod
    def parse_custom_fields(text: str, field_names: List[str]) -> Dict[str, str]:
        """
        Parse custom fields from text.

        Args:
            text: Source text
            field_names: List of field names to extract

        Returns:
            Dictionary of field values
        """
        result = {}
        lines = text.split("\n")

        for field_name in field_names:
            field_lower = field_name.lower()

            for i, line in enumerate(lines):
                if field_lower in line.lower():
                    result[field_name] = FieldParser._extract_value_after_keyword(
                        lines, i
                    )
                    break

            if field_name not in result:
                result[field_name] = ""

        return result
