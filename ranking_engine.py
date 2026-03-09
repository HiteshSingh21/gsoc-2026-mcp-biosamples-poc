import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Tuple
from logger import get_logger

logger = get_logger("ranking_engine")

# Basic Ontology Master Dictionary
ONTOLOGY_MAP = {
    "lung": "UBERON:0002048",
    "brain": "UBERON:0000955",
    "blood": "UBERON:0000178",
    "heart": "UBERON:0000948",
    "human": "NCBITaxon:9606",
    "virus": "NCBITaxon:10239",
    "sars-cov-2": "NCBITaxon:2697049"
}

class RankingEngine:
    def __init__(self):
        # Initialize the Sentence Transformer model
        # Using a small, fast model suitable for PoC
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Hardcoded checklists metadata
        self.checklists = [
            {
                "id": "ENA_HUMAN_v2.0",
                "description": "Human sample checklist version 2. Biological sample from Homo sapiens.",
                "taxon": "human",
                "attributes": ["sample_name", "tissue", "disease", "age"]
            },
            {
                "id": "ENA_HUMAN_v1.2",
                "description": "Human sample checklist. Basic human biological sample.",
                "taxon": "human",
                "attributes": ["sample_name", "tissue", "age"]
            },
            {
                "id": "VIRAL_v2",
                "description": "Viral sample checklist. Virus pathogen and host information.",
                "taxon": "virus",
                "attributes": ["sample_name", "virus_identifier", "host"]
            }
        ]
        
        # Pre-compute embeddings for checklist descriptions
        self.checklist_embeddings = self.model.encode(
            [c["description"] for c in self.checklists]
        )
        
        # Weights
        self.W1 = 0.3  # Attribute Match
        self.W2 = 0.5  # Semantic Similarity
        self.W3 = 0.2  # Taxon Weight

    def calculate_attr_match(self, query_attrs: List[str], checklist_attrs: List[str]) -> float:
        if not query_attrs:
            return 0.5 # Neutral if no attrs provided
        matched = sum(1 for attr in query_attrs if attr in checklist_attrs)
        return matched / len(query_attrs)
        
    def calculate_taxon_weight(self, query_taxon: str, checklist_taxon: str) -> float:
        if not query_taxon:
            return 0.5
        return 1.0 if query_taxon.lower() == checklist_taxon.lower() else 0.0

    def standardize_term(self, term: str) -> str:
        """Looks up a term in the ontology dictionary"""
        if not term:
            return term
        term_lower = term.lower()
        return ONTOLOGY_MAP.get(term_lower, term_lower)

    def rank(self, query: str, provided_attrs: List[str] = None, taxon: str = None) -> List[Dict[str, Any]]:
        provided_attrs = provided_attrs or []
        
        # OBTOLOGY MAPPING: Standardize query terms
        standardized_query = []
        for word in query.split():
            mapped = self.standardize_term(word)
            standardized_query.append(mapped)
        standardized_query_str = " ".join(standardized_query)
        
        logger.info("ontology_normalization", original_query=query, standardized=standardized_query_str)
        
        # 1. Semantic Similarity using standardized query
        query_embedding = self.model.encode([standardized_query_str])[0]
        # Cosine similarity
        similarities = np.dot(self.checklist_embeddings, query_embedding) / (
            np.linalg.norm(self.checklist_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        results = []
        for i, checklist in enumerate(self.checklists):
            sem_sim = float(similarities[i])
            attr_match = self.calculate_attr_match(provided_attrs, checklist["attributes"])
            
            # Standardize taxonomies before compare
            std_query_taxon = self.standardize_term(taxon)
            std_checklist_taxon = self.standardize_term(checklist["taxon"])
            taxon_weight = self.calculate_taxon_weight(std_query_taxon, std_checklist_taxon)
            
            # Application of the Multi-Factor Formula
            score = (self.W1 * attr_match) + (self.W2 * sem_sim) + (self.W3 * taxon_weight)
            
            decision_reasoning = (
                f"Calculated Score {score:.2f} for {checklist['id']} because of "
                f"SemanticSim ({sem_sim:.2f}), AttrMatch ({attr_match:.2f}), and TaxonMatch ({taxon_weight:.2f})."
            )
            
            logger.info("ranking_score_calculated", 
                checklist_id=checklist["id"], 
                score=score, 
                semantic_sim=sem_sim,
                attr_match=attr_match,
                taxon_weight=taxon_weight,
                decision_reasoning=decision_reasoning
            )
            
            results.append({
                "checklist_id": checklist["id"],
                "score": score,
                "factors": {
                    "attr_match": attr_match,
                    "semantic_sim": sem_sim,
                    "taxon_weight": taxon_weight
                },
                "reasoning": decision_reasoning
            })
            
        # Sort descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

# Global instance
ranking_engine = RankingEngine()
