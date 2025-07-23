"""Template loader module for AI interactions."""

import os
from pathlib import Path
from typing import Dict, Any

from app import config


class TemplateLoader:
    """Loads prompt templates from markdown files."""
    
    def __init__(self, templates_dir: str = None):
        """Initialize the template loader.
        
        Args:
            templates_dir: Directory containing markdown template files.
                          Defaults to the same directory as this module.
        """
        if templates_dir is None:
            templates_dir = Path(__file__).parent
        self.templates_dir = Path(templates_dir)
        self._cache: Dict[str, str] = {}
    
    def _load_template(self, template_name: str) -> str:
        """Load a template from a markdown file.
        
        Args:
            template_name: Name of the template file (without .md extension)
            
        Returns:
            The template content as a string
            
        Raises:
            FileNotFoundError: If the template file doesn't exist
        """
        if template_name in self._cache:
            return self._cache[template_name]
        
        template_path = self.templates_dir / f"{template_name}.md"
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            self._cache[template_name] = content
            return content
    
    def get_template(self, template_name: str, **kwargs: Any) -> str:
        """Get a template and format it with the provided parameters.
        
        Args:
            template_name: Name of the template file (without .md extension)
            **kwargs: Parameters to format the template with
            
        Returns:
            The formatted template string
        """
        template = self._load_template(template_name)
        return template.format(**kwargs)
    
    def clear_cache(self):
        """Clear the template cache."""
        self._cache.clear()
    
    def list_available_templates(self) -> list:
        """List all available template files.
        
        Returns:
            List of template names (without .md extension)
        """
        templates = []
        for file_path in self.templates_dir.glob("*.md"):
            templates.append(file_path.stem)
        return sorted(templates)
    
    def template_exists(self, template_name: str) -> bool:
        """Check if a template exists.
        
        Args:
            template_name: Name of the template file (without .md extension)
            
        Returns:
            True if the template exists, False otherwise
        """
        template_path = self.templates_dir / f"{template_name}.md"
        return template_path.exists()


# Create a default instance
_loader = TemplateLoader()

# Dynamic template loading function
def get_template(template_name: str, **kwargs) -> str:
    """Dynamically load a template by name.
    
    Args:
        template_name: Name of the template file (without .md extension)
        **kwargs: Parameters to format the template with
        
    Returns:
        The formatted template string
        
    Raises:
        FileNotFoundError: If the template file doesn't exist
    """
    try:
        body = _loader.get_template(template_name, **kwargs)
        footer = _loader.get_template("language_footer", language=config.LANGUAGE)
        return f"{body}\n{footer}"
    except FileNotFoundError as e:
        import logging
        logging.error(f"Template '{template_name}' not found: {e}")
        raise

def list_available_templates() -> list:
    """List all available template files.
    
    Returns:
        List of template names (without .md extension)
    """
    return _loader.list_available_templates()

def template_exists(template_name: str) -> bool:
    """Check if a template exists.
    
    Args:
        template_name: Name of the template file (without .md extension)
        
    Returns:
        True if the template exists, False otherwise
    """
    return _loader.template_exists(template_name)

 