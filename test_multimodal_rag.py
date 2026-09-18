import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.rag import ingestion, vector_store, fusion_context, prompts
from src.agent import tools, agent

def test_pipeline():
    print("--- 1. Testing RAG Knowledge Ingestion ---")
    chunks = ingestion.get_all_knowledge_chunks()
    assert len(chunks) > 0, "No chunks ingested!"
    print(f"[OK] Ingested {len(chunks)} chunks successfully.")

    print("\n--- 2. Testing Vector Retrieval Store ---")
    store = vector_store.get_vector_store()
    results = store.search("Fani Puri evacuation standard", top_k=3)
    assert len(results) > 0, "Vector search returned no results!"
    print(f"[OK] Vector store retrieved {len(results)} chunks. Top score: {results[0]['score']:.3f}")

    print("\n--- 3. Testing CV + RAG Fusion Engine ---")
    fusion = fusion_context.get_cv_rag_fusion_context(46, user_query="What districts are impacted?")
    assert "error" not in fusion, f"Fusion error: {fusion.get('error')}"
    assert "cv_summary" in fusion, "Missing cv_summary in fusion!"
    print(f"[OK] Fusion context generated for Event #46 (IMD Category: {fusion['cv_summary']['intensity_category']}).")

    print("\n--- 4. Testing Advisory Generation ---")
    adv = tools.generate_advisory(46)
    assert "advisory_report" in adv, "Missing advisory_report!"
    assert len(adv["citations"]) > 0, "Missing citations!"
    print(f"[OK] Generated advisory report with {len(adv['citations'])} citations.")

    print("\n--- 5. Testing Agent Ask Routing ---")
    res = agent.ask("tell me the evacuation guidelines for cyclone Fani in Puri")
    assert "answer" in res, "Missing answer in agent ask response!"
    print(f"[OK] Agent returned answer (Mode: {res.get('mode')}, Tools used: {res.get('tools_used')}).")

    print("\nSUCCESS: ALL MULTIMODAL RAG PIPELINE TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_pipeline()
