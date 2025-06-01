from pathlib import Path
import json
import re
from collections import defaultdict
import math

def clean_text(text):
    """Clean and normalize text"""
    # Remove extra whitespace and normalize spaces
    text = ' '.join(text.split())
    # Remove special characters but keep periods and basic punctuation
    text = re.sub(r'[^\w\s.,;:?!-]', '', text)
    # Normalize multiple periods/dots
    text = re.sub(r'\.{2,}', '.', text)
    # Ensure proper spacing after punctuation
    text = re.sub(r'([.,;:?!])([^\s])', r'\1 \2', text)
    return text

def split_into_sentences(text):
    """Split text into sentences"""
    # Split on sentence endings
    sentences = re.split(r'[.!?]+', text)
    # Remove empty sentences and strip whitespace
    return [s.strip() for s in sentences if s.strip()]

def calculate_word_frequencies(sentences):
    """Calculate word frequencies across all sentences"""
    word_freq = defaultdict(int)
    for sentence in sentences:
        words = sentence.lower().split()
        for word in words:
            word_freq[word] += 1
    return word_freq

def score_sentences(sentences, word_freq):
    """Score sentences based on word frequencies"""
    scores = []
    for sentence in sentences:
        words = sentence.lower().split()
        if not words:
            scores.append(0)
            continue
        
        # Calculate score as average word frequency
        score = sum(word_freq[word] for word in words) / len(words)
        # Boost score for longer sentences (but not too much)
        length_factor = min(len(words) / 10.0, 1.0)
        scores.append(score * length_factor)
    
    return scores

def generate_summary(text, num_sentences=2):
    """Generate summary by selecting most important sentences"""
    try:
        # Clean the text
        cleaned_text = clean_text(text)
        
        # Split into sentences
        sentences = split_into_sentences(cleaned_text)
        if len(sentences) <= num_sentences:
            return text
        
        # Calculate word frequencies
        word_freq = calculate_word_frequencies(sentences)
        
        # Score sentences
        scores = score_sentences(sentences, word_freq)
        
        # Get indices of top scoring sentences while preserving order
        indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:num_sentences]
        indices = sorted(indices)  # Sort to maintain original order
        
        # Join selected sentences
        summary = '. '.join(sentences[i] for i in indices)
        return summary + '.'
        
    except Exception as e:
        print(f"Error in generate_summary: {e}")
        return None

def test_summarization():
    # Path to your test JSON file
    TEXT_JSON_DIR = Path("/Users/imakia/Google Drive/My Drive/Kitsune/Fase1_Estructuracion_base/brasil/text_json_es")
    
    # Get the first JSON file
    json_files = list(TEXT_JSON_DIR.glob('*.json'))
    if not json_files:
        print("No JSON files found in directory")
        return
    
    first_file = json_files[0]
    print(f"\nTesting summarization with file: {first_file.name}")
    
    try:
        with open(first_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            print(f"Successfully loaded JSON data from file")
            print(f"JSON ID: {json_data.get('id', 'Not found')}")
            
            # Get the full text
            full_text = json_data['full_text']
            print(f"\nOriginal text length: {len(full_text)} characters")
            
            # Show original text for comparison
            print("\nOriginal text:")
            print("-------------------")
            print(full_text)
            print("-------------------")
            
            # Generate summary
            print("\nGenerating summary...")
            summary = generate_summary(full_text)
            
            if summary:
                print(f"\nSummary length: {len(summary)} characters")
                print("\nSummary preview:")
                print("-------------------")
                print(summary)
                print("-------------------")
            else:
                print("Failed to generate summary")
            
    except Exception as e:
        print(f"Error during summarization test: {e}")

if __name__ == "__main__":
    test_summarization()