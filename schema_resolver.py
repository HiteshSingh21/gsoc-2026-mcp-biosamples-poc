import json
import httpx
from pathlib import Path
from logger import get_logger

logger = get_logger("schema_resolver")

SCHEMA_FILE = Path(__file__).parent / "schemas.json"

class SchemaResolver:
    def __init__(self):
        self.schemas = self._load_schemas()

    def _load_schemas(self):
        try:
            with open(SCHEMA_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error("l3_cache_load_error", error=str(e))
            return {}

    async def get_schema_async(self, schema_id: str) -> dict:
        """
        Attempts to fetch externally via httpx (MOCK URL).
        On timeout/failure, falls back to L3 cache schemas.json locally.
        """
        mock_external_url = f"https://mock-biovalidator.ebi.ac.uk/api/schemas/{schema_id}"
        
        try:
            logger.info("fetching_external_schema", url=mock_external_url)
            # Create a client with a very short timeout to ensure it fails for the PoC
            async with httpx.AsyncClient(timeout=0.1) as client:
                response = await client.get(mock_external_url)
                response.raise_for_status()
                logger.info("schema_fetched_externally", schema_id=schema_id)
                return response.json()
        except (httpx.TimeoutException, httpx.RequestError) as e:
            logger.warning("bio_validator_fallback", 
                           reason="External fetch failed or timed out", 
                           schema_id=schema_id, 
                           error=str(e),
                           action="Falling back to L3 Cache (schemas.json)")
            return self.schemas.get(schema_id)

    def list_schemas(self):
        return list(self.schemas.keys())

# Global instance for mock cache
resolver = SchemaResolver()
