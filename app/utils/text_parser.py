def parse_markdown(text: str) -> str:
    """
    Simple markdown parser for paragraphs, italic, and bold.
    """
    if not text:
        return ""
    
    # Split into paragraphs (single newlines)
    paragraphs = text.split('\n')
    
    formatted_paragraphs = []
    for paragraph in paragraphs:
        if not paragraph.strip():
            continue
            
        # Convert **bold** to <strong>bold</strong>
        parsed = paragraph.replace('**', '<strong>', 1)
        while '**' in parsed:
            parsed = parsed.replace('**', '</strong>', 1)
        
        # Convert *italic* to <em>italic</em>
        parsed = parsed.replace('*', '<em>', 1)
        while '*' in parsed:
            parsed = parsed.replace('*', '</em>', 1)
        
        # Wrap in paragraph tags
        formatted_paragraphs.append(f"<p>{parsed}</p>")
    
    return ''.join(formatted_paragraphs)