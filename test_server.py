from server import get_checklist_recommendations
import json

def test_clarification():
    print("\n--- Test 1: Clarification Loop ---")
    result = get_checklist_recommendations(query="I have a human sample", provided_attributes=["sample_name"])
    print(f"Result: {json.dumps(json.loads(result), indent=2)}")

def test_confident_match():
    print("\n--- Test 2: Confident Match ---")
    result = get_checklist_recommendations(query="human sample from liver", provided_attributes=["tissue", "sample_name"], taxon="human")
    print(f"Result: {json.dumps(json.loads(result), indent=2)}")

def test_viral_match():
    print("\n--- Test 3: Viral Match ---")
    result = get_checklist_recommendations(query="SARS-CoV-2 viral sample", provided_attributes=["virus_identifier"], taxon="virus")
    print(f"Result: {json.dumps(json.loads(result), indent=2)}")

def test_low_confidence():
    print("\n--- Test 4: Low Confidence Guesses ---")
    result = get_checklist_recommendations(query="environmental soil sample", taxon="metagenome")
    print(f"Result: {json.dumps(json.loads(result), indent=2)}")

if __name__ == "__main__":
    test_clarification()
    test_confident_match()
    test_viral_match()
    test_low_confidence()
