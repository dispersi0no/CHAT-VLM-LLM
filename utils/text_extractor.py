"""Text extraction and post-processing utilities."""

import re
from typing import List, Dict, Optional


class TextExtractor:
    """Text extraction and cleaning utilities."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize extracted text.
        
        Args:
            text: Raw text from OCR
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common OCR errors
        text = TextExtractor.fix_common_errors(text)
        
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        return text.strip()
    
    @staticmethod
    def fix_common_errors(text: str) -> str:
        """Fix common OCR recognition errors."""
        replacements = {
            'l\'': 'I',  # l apostrophe to I
            '\u00a7': 'S',    # Section sign to S
        }
        
        # Apply replacements (context-aware logic can be added)
        for wrong, correct in replacements.items():
            text = text.replace(wrong, correct)
        
        return text
    
    @staticmethod
    def extract_numbers(text: str) -> List[str]:
        """Extract all numbers from text."""
        return re.findall(r'\b\d+(?:[.,]\d+)?\b', text)
    
    @staticmethod
    def extract_dates(text: str) -> List[str]:
        """Extract date patterns from text."""
        date_patterns = [
            r'\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b',  # DD/MM/YYYY, DD-MM-YYYY, etc.
            r'\b\d{4}[./-]\d{1,2}[./-]\d{1,2}\b',    # YYYY-MM-DD
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b'  # Month DD, YYYY
        ]
        
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, text, re.IGNORECASE))
        
        return dates
    
    @staticmethod
    def extract_emails(text: str) -> List[str]:
        """Extract email addresses from text."""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(pattern, text)
    
    @staticmethod
    def extract_phone_numbers(text: str) -> List[str]:
        """Extract phone numbers from text."""
        patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',  # International
            r'\(\d{3}\)\s*\d{3}[-.]?\d{4}',  # (123) 456-7890
            r'\d{3}[-.]?\d{3}[-.]?\d{4}'     # 123-456-7890
        ]
        
        phones = []
        for pattern in patterns:
            phones.extend(re.findall(pattern, text))
        
        return list(set(phones))  # Remove duplicates
    
    @staticmethod
    def extract_amounts(text: str) -> List[Dict[str, str]]:
        """Extract monetary amounts with currencies."""
        pattern = r'([\$\u20ac\u00a3\u00a5\u20bd])\s?(\d+(?:[.,]\d+)?)'
        matches = re.findall(pattern, text)
        
        return [
            {"currency": currency, "amount": amount}
            for currency, amount in matches
        ]
    
    @staticmethod
    def split_into_lines(text: str) -> List[str]:
        """Split text into lines, removing empty lines."""
        lines = text.split('\n')
        return [line.strip() for line in lines if line.strip()]
    
    @staticmethod
    def extract_key_value_pairs(text: str) -> Dict[str, str]:
        """
        Extract key-value pairs from text (e.g., "Name: John Doe").
        
        Args:
            text: Source text
            
        Returns:
            Dictionary of extracted key-value pairs
        """
        pairs = {}
        lines = TextExtractor.split_into_lines(text)
        
        for line in lines:
            # Look for patterns like "Key: Value" or "Key - Value"
            match = re.match(r'^([^:]+?)\s*[:-]\s*(.+)$', line)
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                pairs[key] = value
        
        return pairs
    
    @staticmethod
    def calculate_confidence_score(text: str) -> float:
        """
        Calculate a simple confidence score based on text characteristics.
        
        Args:
            text: Extracted text
            
        Returns:
            Confidence score between 0 and 1
        """
        if not text:
            return 0.0
        
        score = 1.0
        
        # Penalize for excessive special characters
        special_char_ratio = len(re.findall(r'[^\w\s]', text)) / len(text)
        if special_char_ratio > 0.3:
            score -= 0.2
        
        # Penalize for lack of spaces (gibberish)
        space_ratio = text.count(' ') / len(text)
        if space_ratio < 0.1:
            score -= 0.3
        
        # Penalize for too many consecutive capitals
        if re.search(r'[A-Z]{10,}', text):
            score -= 0.1
        
        return max(0.0, min(1.0, score))
