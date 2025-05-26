"""
Test the translation functionality.
"""
import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.utils.translator import translate_text_pt_to_es

async def test_translate():
    """Test the translation functionality."""
    
    # Sample Portuguese text
    text_pt = "Este é um teste de tradução do português para o espanhol."
    
    print("Original text (Portuguese):")
    print(text_pt)
    print("\n" + "-"*80 + "\n")
    
    # Translate to Spanish
    translated = await translate_text_pt_to_es(text_pt)
    
    print("Translated text (Spanish):")
    print(translated)

if __name__ == "__main__":
    asyncio.run(test_translate())
