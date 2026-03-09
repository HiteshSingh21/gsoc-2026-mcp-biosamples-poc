from server import get_checklist_recommendations
import json
import asyncio

async def test_clarification():
    print("\n--- Test 1: Clarification Loop ---")
    result = await get_checklist_recommendations(query="I have a human sample", provided_attributes=["sample_name"])
    print(f"Result: {json.dumps(json.loads(result), indent=2)}")

async def test_confident_match():
    print("\n--- Test 2: Confident Match ---")
    result = await get_checklist_recommendations(query="human sample from liver", provided_attributes=["tissue", "sample_name"], taxon="human")
    print(f"Result: {json.dumps(json.loads(result), indent=2)}")

async def test_viral_match():
    print("\n--- Test 3: Viral Match ---")
    result = await get_checklist_recommendations(query="SARS-CoV-2 viral sample", provided_attributes=["virus_identifier"], taxon="virus")
    print(f"Result: {json.dumps(json.loads(result), indent=2)}")

async def test_low_confidence():
    print("\n--- Test 4: Low Confidence Guesses ---")
    # Using 'environmental soil sample' without matching taxon
    result = await get_checklist_recommendations(query="environmental soil sample", taxon="metagenome")
    print(f"Result: {json.dumps(json.loads(result), indent=2)}")

async def test_version_upgrade():
    print("\n--- Test 5: Version Upgrade Clarification ---")
    # Provide exactly the attributes for v1.2 (no 'disease') so v1.2 ranks slightly higher on AttrMatch
    result = await get_checklist_recommendations(query="human sample", provided_attributes=["sample_name", "tissue", "age"], taxon="human")
    print(f"Result: {json.dumps(json.loads(result), indent=2)}")
    
async def test_ontology_normalization():
    print("\n--- Test 6: Ontology Normalization ---")
    # 'lung' should map to UBERON code and still capture semantic intent for human
    result = await get_checklist_recommendations(query="lung sample", provided_attributes=["tissue", "sample_name"], taxon="human")
    print(f"Result: {json.dumps(json.loads(result), indent=2)}")

async def main():
    await test_clarification()
    await test_confident_match()
    await test_viral_match()
    await test_low_confidence()
    await test_version_upgrade()
    await test_ontology_normalization()

if __name__ == "__main__":
    asyncio.run(main())
