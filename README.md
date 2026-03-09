# BioSamples "Micro-Mediator" FastMCP PoC

This repository contains a Proof of Concept (PoC) for the **BioSamples Message Content Protocol (MCP) Server**. It serves as an intelligent "Micro-Mediator" that connects conversational AI agents (LLMs) with the strict, structured data requirements of the BioSamples and BioValidator services at EBI. 

By utilizing the newly emerging **FastMCP** framework, this PoC demonstrates how to securely bridge the gap between unstructured scientific inquiries and standardized metadata schemas while enforcing deterministic outputs, security boundaries, observability, and advanced normalization pipelines.

## 🚀 Key Concepts Demonstrated

1. **FastMCP Integration & Tool Definition**
   - The server publishes a tool (`get_checklist_recommendations`) using the MCP protocol.
   - It enforces a strict Pydantic JSON Schema for input and output, ensuring the LLM cannot hallucinate arbitrary schema definitions.

2. **Multi-Factor Ranking Engine (Intelligent Matching)**
   - Instead of simplistic keyword matching, the tool evaluates queries using a mathematical formula:
     $$S = (W_1 \cdot AttrMatch) + (W_2 \cdot SemanticSim) + (W_3 \cdot TaxonMatch)$$
   - It leverages `sentence-transformers` for calculating cosine semantic similarities ($SemanticSim$) between the user's natural language query and hardcoded ENA checklist descriptions.
   - Enforces a high-confidence threshold ($S \ge 0.85$), refusing to guess if data quality is poor.

3. **Zoned Security Model (The "Black Box" Proof)**
   - Simulates a Trusted Zone (Zone 2) protecting sensitive API operations.
   - The tool internally retrieves a mocked `WEBIN_REST_TOKEN` through `auth_manager.py`. Tests verify that this internal token is **never leaked** into the returned JSON payload parsed by the Untrusted AI (Zone 1).

4. **The Clarification Loop (Metadata Gap Handling)**
   - Built to handle missing mandatory metadata gracefully.
   - If a generic query like "human sample" is submitted but lacks the required "tissue" attribute, the tool returns a `ClarificationObject` (`{"status": "CLARIFY", "missing_field": "tissue"}`) instead of causing a validation error, prompting the LLM to ask the researcher for more details.

5. **Formal Schema Version Resolution**
   - Implements advanced version detection. If the provided metadata perfectly matches a legacy schema (e.g., `ENA_HUMAN_v1.2`), but a newer version exists (`ENA_HUMAN_v2.0`) and passes the confidence threshold, the tool issues an upgrade clarification prompt.

6. **Ontology Mapping (Semantic Normalization)**
   - Features an internal `ONTOLOGY_MAP` dictionary logic. 
   - Non-standard terms in the query (e.g., "lung") are mapped to official ontology terms (e.g., `UBERON:0002048`) *before* semantic similarity scoring occurs, proving the transition from simple keywords to standardized metadata.

7. **Asynchronous External Service Mocking (L3 Cache Fallback)**
   - Replicates non-blocking communication with the BioValidator API.
   - Uses `httpx.AsyncClient` to simulate fetching schemas externally with an aggressive simulated timeout constraint.
   - Upon network timeout, the tool gracefully falls back to the mocked Local Schema Cache (L3, `schemas.json`), ensuring high availability.

8. **Observability & JSON Audit Trails**
   - Integrated with `structlog`.
   - The system outputs structured JSON logs for every tool invocation. It explicitly logs the `decision_reasoning` capturing exact calculations (e.g., *SemanticSim (0.92), AttrMatch (0.43)*) for audit transparency.

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.11+
- Virtual Environment (Recommended)

### Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/HiteshSingh21/gsoc-2026-mcp-biosamples-poc.git
   cd gsoc-2026-mcp-biosamples-poc
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install "mcp[cli]" fastmcp sentence-transformers httpx structlog pydantic numpy
   ```

## 🧪 Running the Verification Tests

To see the system in action and verify its behaviors, run the integrated test script:

```bash
python test_server.py
```

### What You Will See in the Output:

The test script automatically runs 6 distinct scenarios proving the PoC's logic:

1. **Test 1: Clarification Loop**
   - **Input:** "I have a human sample"
   - **Output:** Returns a `CLARIFY` status asking specifically for the missing `tissue` type.
2. **Test 2: Confident Match**
   - **Input:** "human sample from liver"
   - **Output:** Returns a `SUCCESS` status, successfully mapping to schema `ENA_HUMAN_v2.0` with calculated Multi-Factor scores natively attached to the response.
3. **Test 3: Viral Match**
   - **Input:** "SARS-CoV-2 viral sample"
   - **Output:** Matches the `VIRAL_v2` checklist cleanly through semantic and taxonomic logic.
4. **Test 4: Low Confidence Guesses**
   - **Input:** "environmental soil sample" mapped as "metagenome" taxonomy.
   - **Output:** Drops below the 0.85 similarity threshold natively returning `NO_CONFIDENT_MATCH`. Proves the tool will not accept low-quality inferences.
5. **Test 5: Version Upgrade Clarification**
   - **Input:** Matches exact attributes of legacy `v1.2` human schema.
   - **Output:** Returns `{"missing_field": "UPGRADE_VERSION"}` prompting the user to upgrade their data structure to `v2.0`.
6. **Test 6: Ontology Normalization**
   - **Input:** "lung sample"
   - **Output:** Safely passes normalization mapping "lung" -> "UBERON:0002048" before logging the result successfully.

Throughout the execution, you will see the **JSON Structlogs** explicitly tracking tool invocations, the mock BioValidator `TimeoutExceptions`, fallback events, and the exact arithmetic reasoning for every candidate checklist!

## 🔧 Architecture & Core Files

- **`server.py`**: The FastMCP server orchestrator containing the core tool logic and Pydantic models.
- **`ranking_engine.py`**: The intelligent Multi-Factor ranking engine handling Sentence-BERT embeddings, Ontology matching, and strict arithmetic scoring heuristics.
- **`auth_manager.py`**: The trusted zone wrapper simulating credential injection.
- **`schema_resolver.py`**: Handles external `httpx` async calls to mock APIs with L3 local fallback mechanics.
- **`logger.py`**: Centralized configuration for `structlog` audit trails.
- **`schemas.json`**: The Local Mock L3 Cache mimicking retrieved schema datasets.
