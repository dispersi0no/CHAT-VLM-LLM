"""Markdown rendering utilities."""

import re
from typing import Dict, List


class MarkdownRenderer:
    """Utilities for rendering text with Markdown formatting."""

    @staticmethod
    def format_ocr_result(text: str, confidence: float = None) -> str:
        """
        Format OCR result with Markdown.

        Args:
            text: OCR extracted text
            confidence: Optional confidence score

        Returns:
            Formatted Markdown string
        """
        output = "### Extracted Text\n\n"

        if confidence is not None:
            output += f"**Confidence:** {confidence:.1%}\n\n"

        output += "```\n"
        output += text
        output += "\n```"

        return output

    @staticmethod
    def format_fields_table(
        fields: Dict[str, str], title: str = "Extracted Fields"
    ) -> str:
        """
        Format extracted fields as Markdown table.

        Args:
            fields: Dictionary of field names and values
            title: Table title

        Returns:
            Formatted Markdown table
        """
        output = f"### {title}\n\n"
        output += "| Field | Value |\n"
        output += "|-------|-------|\n"

        for field, value in fields.items():
            # Escape pipe characters in values
            safe_value = str(value).replace("|", "\\|")
            output += f"| **{field}** | {safe_value} |\n"

        return output

    @staticmethod
    def format_comparison(results: Dict[str, Dict[str, any]]) -> str:
        """
        Format model comparison results.

        Args:
            results: Dictionary mapping model names to their metrics

        Returns:
            Formatted Markdown comparison
        """
        output = "## Model Comparison\n\n"
        output += "| Model | Accuracy | Speed | Memory |\n"
        output += "|-------|----------|-------|--------|\n"

        for model_name, metrics in results.items():
            accuracy = metrics.get("accuracy", "N/A")
            speed = metrics.get("speed", "N/A")
            memory = metrics.get("memory", "N/A")
            output += f"| {model_name} | {accuracy} | {speed} | {memory} |\n"

        return output

    @staticmethod
    def highlight_entities(text: str, entities: Dict[str, List[str]]) -> str:
        """
        Highlight extracted entities in text.

        Args:
            text: Original text
            entities: Dictionary mapping entity types to lists of values

        Returns:
            Text with Markdown highlights
        """
        highlighted = text

        for entity_type, values in entities.items():
            for value in values:
                # Escape special regex characters
                escaped_value = re.escape(value)
                highlighted = re.sub(
                    f"\\b{escaped_value}\\b", f"**{value}**", highlighted
                )

        return highlighted

    @staticmethod
    def create_collapsible_section(title: str, content: str) -> str:
        """
        Create a collapsible Markdown section.

        Args:
            title: Section title
            content: Section content

        Returns:
            Markdown with collapsible section
        """
        return f"<details>\n<summary>{title}</summary>\n\n{content}\n\n</details>"

    @staticmethod
    def format_chat_message(role: str, content: str) -> str:
        """
        Format chat message with role indicator.

        Args:
            role: Message role (user/assistant)
            content: Message content

        Returns:
            Formatted message
        """
        icon = "👤" if role == "user" else "🤖"
        return f"{icon} **{role.capitalize()}:**\n\n{content}"
