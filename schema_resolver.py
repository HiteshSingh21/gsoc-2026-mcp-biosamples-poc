import json
from pathlib import Path

SCHEMA_FILE = Path(__file__).parent / "schemas.json"

class SchemaResolver:
    def __init__(self):
        self.schemas = self._load_schemas()

    def _load_schemas(self):
        try:
            with open(SCHEMA_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading schemas: {e}")
            return {}

    def get_schema(self, schema_id: str):
        return self.schemas.get(schema_id)

    def list_schemas(self):
        return list(self.schemas.keys())

# Global instance for mock cache
resolver = SchemaResolver()
