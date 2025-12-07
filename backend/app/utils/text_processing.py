"""Text processing utilities for document chunking and sanitization."""
import re
from typing import List


def sanitize_input(text: str) -> str:
    """
    Sanitize input text by removing excessive whitespace and normalizing.
    
    Args:
        text: Raw text input
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Text to chunk
        chunk_size: Maximum size of each chunk in characters
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        # Calculate end position
        end = start + chunk_size
        
        # If this is not the last chunk, try to break at a sentence boundary
        if end < len(text):
            # Look for sentence endings within the last 200 characters
            sentence_endings = ['. ', '.\n', '! ', '!\n', '? ', '?\n']
            best_break = end
            
            for i in range(max(start, end - 200), end):
                for ending in sentence_endings:
                    if text[i:i+len(ending)] == ending:
                        best_break = i + len(ending)
                        break
                if best_break < end:
                    break
            
            end = best_break
        
        # Extract chunk
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start position with overlap
        start = end - overlap
        if start < 0:
            start = 0
        
        # Prevent infinite loop
        if start >= len(text):
            break
    
    return chunks
