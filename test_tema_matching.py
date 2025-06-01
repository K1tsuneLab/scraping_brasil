from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from datetime import datetime

# Spanish stop words
SPANISH_STOP_WORDS = [
    'a', 'al', 'ante', 'bajo', 'cabe', 'con', 'contra', 'de', 'desde', 'durante',
    'en', 'entre', 'hacia', 'hasta', 'mediante', 'para', 'por', 'según', 'sin',
    'sobre', 'tras', 'y', 'e', 'ni', 'o', 'u', 'pero', 'sino', 'porque',
    'pues', 'que', 'si', 'más', 'menos', 'el', 'la', 'los', 'las', 'un',
    'una', 'unos', 'unas', 'este', 'esta', 'estos', 'estas', 'ese', 'esa',
    'esos', 'esas', 'aquel', 'aquella', 'aquellos', 'aquellas', 'del'
]

# Sample test data
SAMPLE_TEMAS = [
    (1, "Educación", "Temas relacionados con la educación pública y privada"),
    (2, "Salud", "Sistema de salud, hospitales y atención médica"),
    (3, "Economía", "Presupuesto, finanzas y desarrollo económico"),
    (4, "Medio Ambiente", "Protección ambiental y cambio climático"),
    (5, "Transporte", "Infraestructura y sistemas de transporte público")
]

SAMPLE_PROYECTOS = [
    (1, "Mejoras en Escuelas Públicas", "Comisión de Educación"),
    (2, "Presupuesto para Hospitales", "Comisión de Salud"),
    (3, "Plan de Transporte Urbano", "Departamento de Infraestructura")
]

def test_matching_speed():
    """Test the speed of topic matching with sample data."""
    print("Initializing TF-IDF vectorizer...")
    vectorizer = TfidfVectorizer(
        min_df=1,
        ngram_range=(1, 2),  # Use both unigrams and bigrams
        stop_words=SPANISH_STOP_WORDS
    )
    
    print("\nPreparing text data...")
    tema_texts = [f"{tema[1]} {tema[2]}" for tema in SAMPLE_TEMAS]
    proyecto_texts = [f"{proyecto[1]} {proyecto[2]}" for proyecto in SAMPLE_PROYECTOS]
    
    print("\nComputing TF-IDF and similarities...")
    start_time = datetime.now()
    
    # Fit and transform all texts together
    all_texts = tema_texts + proyecto_texts
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    
    # Split the matrix back into temas and proyectos
    tema_vectors = tfidf_matrix[:len(tema_texts)].toarray()
    proyecto_vectors = tfidf_matrix[len(tema_texts):].toarray()
    
    # Calculate similarity matrix
    similarity_matrix = cosine_similarity(proyecto_vectors, tema_vectors)
    
    end_time = datetime.now()
    processing_time = (end_time - start_time).total_seconds()
    
    print(f"\nProcessing completed in {processing_time:.2f} seconds")
    
    # Print results and feature importance
    print("\nTop features (terms) by importance:")
    feature_names = vectorizer.get_feature_names_out()
    for i, proyecto in enumerate(SAMPLE_PROYECTOS):
        print(f"\nProyecto: {proyecto[1]}")
        
        # Get top terms for this proyecto
        proyecto_vector = proyecto_vectors[i]
        term_importance = [(term, score) for term, score in zip(feature_names, proyecto_vector) if score > 0]
        term_importance.sort(key=lambda x: x[1], reverse=True)
        print("Top terms:")
        for term, score in term_importance[:3]:
            print(f"- {term}: {score:.3f}")
        
        # Get matching temas
        similarities = similarity_matrix[i]
        top_2_indices = np.argsort(similarities)[-2:][::-1]
        
        print("Top 2 matching temas:")
        for idx in top_2_indices:
            print(f"- {SAMPLE_TEMAS[idx][1]}: {similarities[idx]:.3f}")
        
        # Find recommended tema (excluding top 2)
        mask = np.ones(len(SAMPLE_TEMAS), dtype=bool)
        mask[top_2_indices] = False
        remaining_similarities = similarities[mask]
        remaining_temas = [tema for i, tema in enumerate(SAMPLE_TEMAS) if mask[i]]
        recommended_idx = np.argmax(remaining_similarities)
        
        print(f"Recommended additional tema:")
        print(f"- {remaining_temas[recommended_idx][1]}: {remaining_similarities[recommended_idx]:.3f}")

if __name__ == "__main__":
    test_matching_speed() 