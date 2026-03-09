from fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Optional, List, Union

from ranking_engine import ranking_engine
from auth_manager import get_internal_webin_token
from schema_resolver import resolver

# Initialize the FastMCP server
mcp = FastMCP("BioSamples-Mediator-PoC")

# Deterministic Input Schema
class ChecklistRecommendationsInput(BaseModel):
    query: str = Field(description="Natural language query for the sample type (e.g., 'human sample', 'viral culture')")
    provided_attributes: Optional[List[str]] = Field(default=[], description="List of attributes already provided by the user (e.g., ['sample_name', 'tissue'])")
    taxon: Optional[str] = Field(default=None, description="The taxonomic group if known (e.g., 'human', 'virus')")

# Response Schemas for Deterministic Output
class FactorScores(BaseModel):
    attr_match: float
    semantic_sim: float
    taxon_weight: float

class ChecklistMatch(BaseModel):
    checklist_id: str
    description: str
    score: float
    factors: FactorScores
    schema_fields: dict

class ClarificationObject(BaseModel):
    status: str = "CLARIFY"
    missing_field: str
    message: str

class RecommendationOutput(BaseModel):
    status: str = "SUCCESS"
    best_fit: Optional[ChecklistMatch] = None
    alternatives: List[ChecklistMatch] = []
    
# Union type for the return to allow either clarification or recommendation result
RecommendationResult = Union[ClarificationObject, RecommendationOutput]

@mcp.tool()
def get_checklist_recommendations(
    query: str, 
    provided_attributes: list[str] = None, 
    taxon: str = None
) -> str:
    """
    Analyzes the natural language query, computes compatibility scores against schemas,
    and returns deterministic recommendations or requests clarification for missing fields.
    Returns a strict JSON string.
    """
    
    # Validation from Input Model
    input_data = ChecklistRecommendationsInput(
        query=query, 
        provided_attributes=provided_attributes or [], 
        taxon=taxon
    )
    
    # SECURITY GATEWAY: The "Black Box" Proof
    # Fetch internal token but NEVER return it in the final output JSON
    internal_token = get_internal_webin_token()
    
    # 4. Clarification Loop Mock
    # If a query like "human sample" is missing the tissue field, return clarification object
    if "human" in input_data.query.lower() and "tissue" not in input_data.provided_attributes:
        return ClarificationObject(
            missing_field="tissue",
            message="Please specify the tissue type."
        ).model_dump_json()
        
    # Query Ranking Engine
    rankings = ranking_engine.rank(
        query=input_data.query,
        provided_attrs=input_data.provided_attributes,
        taxon=input_data.taxon
    )
    
    # Threshold Logic
    THRESHOLD = 0.85
    valid_matches = []
    
    for rank in rankings:
        if rank["score"] >= THRESHOLD:
            # Fetch Schema dynamically using the internal mock resolution / L3 Cache
            schema_data = resolver.get_schema(rank["checklist_id"])
            if schema_data:
                valid_matches.append(ChecklistMatch(
                    checklist_id=rank["checklist_id"],
                    description=schema_data.get("description", ""),
                    score=rank["score"],
                    factors=FactorScores(**rank["factors"]),
                    schema_fields=schema_data.get("fields", {})
                ))
            
    if not valid_matches:
        # Avoid low confidence guesses
        return RecommendationOutput(status="NO_CONFIDENT_MATCH", alternatives=[]).model_dump_json()
        
    return RecommendationOutput(
        status="SUCCESS",
        best_fit=valid_matches[0],
        alternatives=valid_matches[1:]
    ).model_dump_json()

if __name__ == "__main__":
    mcp.run()
