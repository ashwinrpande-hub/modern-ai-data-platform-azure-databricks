"""AI-ready Gold: Mosaic AI Vector Search over customer/product profiles for semantic search + RAG.
Genie handles NL->SQL on agg_sales_daily; this covers unstructured/semantic asks."""
from databricks.vector_search.client import VectorSearchClient

vsc = VectorSearchClient()
ENDPOINT = "nucor-vs"

# Delta Sync index: auto-embeds (databricks-gte-large-en) and stays in sync via CDF
vsc.create_delta_sync_index(
    endpoint_name=ENDPOINT,
    index_name="nucor_gold.ai.customer_profile_idx",
    source_table_name="nucor_gold.ai.customer_profile_text",  # built from dim_customer + features
    pipeline_type="TRIGGERED",
    primary_key="customer_hk",
    embedding_source_column="profile_text",
    embedding_model_endpoint_name="databricks-gte-large-en")

def semantic_search(q: str, k: int = 5):
    idx = vsc.get_index(ENDPOINT, "nucor_gold.ai.customer_profile_idx")
    return idx.similarity_search(query_text=q, num_results=k,
                                 columns=["customer_hk", "profile_text"])

# RAG agent (Agent Bricks / Mosaic AI Agent Framework) grounds answers in retrieved profiles:
# retriever -> prompt with citations -> served via Model Serving endpoint 'nucor-sales-rag'
