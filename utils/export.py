"""Export utilities for OCR results."""

import csv
import json
from datetime import datetime
from io import StringIO
from typing import Any, Dict, List


def export_to_json(data: Dict[str, Any], pretty: bool = True) -> str:
    """
    Export data to JSON string.

    Args:
        data: Data to export
        pretty: Whether to format with indentation

    Returns:
        JSON string
    """
    return json.dumps(data, indent=2 if pretty else None, ensure_ascii=False)


def export_to_csv(data: Dict[str, Any]) -> str:
    """
    Export data to CSV string.

    Args:
        data: Data to export (flat dictionary or list of dictionaries)

    Returns:
        CSV string
    """
    output = StringIO()

    if isinstance(data, dict):
        # Single record
        writer = csv.DictWriter(output, fieldnames=data.keys())
        writer.writeheader()
        writer.writerow(data)
    elif isinstance(data, list) and data:
        # Multiple records
        fieldnames = data[0].keys() if isinstance(data[0], dict) else ["value"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            if isinstance(row, dict):
                writer.writerow(row)
            else:
                writer.writerow({"value": row})

    return output.getvalue()


def export_to_txt(text: str, metadata: Dict[str, Any] = None) -> str:
    """
    Export text with optional metadata.

    Args:
        text: Text content
        metadata: Optional metadata dictionary

    Returns:
        Formatted text string
    """
    output = []

    if metadata:
        output.append("=" * 50)
        output.append("Metadata")
        output.append("=" * 50)
        for key, value in metadata.items():
            output.append(f"{key}: {value}")
        output.append("\n" + "=" * 50)
        output.append("Extracted Text")
        output.append("=" * 50 + "\n")

    output.append(text)

    return "\n".join(output)


def create_export_package(ocr_result: Dict[str, Any]) -> Dict[str, str]:
    """
    Create export package with multiple formats.

    Args:
        ocr_result: OCR result dictionary

    Returns:
        Dictionary with format names and export strings
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Prepare data for export
    export_data = {
        "timestamp": timestamp,
        "text": ocr_result.get("text", ""),
        "confidence": ocr_result.get("confidence", 0.0),
        "model": ocr_result.get("model", "unknown"),
        "processing_time": ocr_result.get("processing_time", 0.0),
    }

    # Add extracted fields if present
    if "fields" in ocr_result:
        export_data.update(ocr_result["fields"])

    return {
        "json": export_to_json(export_data),
        "csv": export_to_csv(export_data),
        "txt": export_to_txt(
            ocr_result.get("text", ""),
            metadata={
                "Timestamp": timestamp,
                "Confidence": f"{export_data['confidence']:.2%}",
                "Model": export_data["model"],
                "Processing Time": f"{export_data['processing_time']:.2f}s",
            },
        ),
    }
