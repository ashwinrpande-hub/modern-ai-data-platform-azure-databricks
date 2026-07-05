"""
Sales RAG agent (fills gap B5 — previously a comment in vector_search_rag.py).
Mosaic AI Agent Framework: UC-registered retriever tool over the customer-profile
Vector Search index + a served agent endpoint 'nucor-sales-rag'. Grounded answers
with citations; region row filters still apply because retrieval reads governed tables.
For multi-agent (healer + RCA + this), wrap with the Supervisor Agent SDK (2026).
"""
from databricks.sdk import WorkspaceClient
import mlflow

INDEX = "nucor_gold.ai.customer_profile_idx"
LLM_ENDPOINT = "databricks-claude-sonnet"      # any Databricks-hosted FM endpoint

# 1) Retriever as a UC SQL function -> callable by ANY agent (Genie, Agent Bricks, custom)
RETRIEVER_SQL = f"""
CREATE OR REPLACE FUNCTION nucor_gold.ai.search_customer_profiles(question STRING)
RETURNS TABLE (customer_hk STRING, profile_text STRING, score DOUBLE)
COMMENT 'Semantic search over customer profiles (Vector Search delta-sync index)'
RETURN SELECT customer_hk, profile_text, search_score
       FROM VECTOR_SEARCH(index => '{INDEX}', query => question, num_results => 5)
"""

# 2) Agent definition (ChatAgent) — logged to UC, served via Model Serving
AGENT_SYSTEM_PROMPT = (
    "You are a sales analyst for a steel manufacturer. Answer ONLY from the retrieved "
    "customer profiles; cite customer_hk for every claim; say 'not in the data' otherwise.")

def build_and_deploy():
    w = WorkspaceClient()
    w.statement_execution.execute_statement(
        warehouse_id=w.config.warehouse_id, statement=RETRIEVER_SQL)

    from databricks_langchain import ChatDatabricks, VectorSearchRetrieverTool
    from mlflow.models.resources import DatabricksVectorSearchIndex, DatabricksServingEndpoint
    tool = VectorSearchRetrieverTool(index_name=INDEX, num_results=5,
                                     columns=["customer_hk", "profile_text"])
    llm = ChatDatabricks(endpoint=LLM_ENDPOINT)
    agent = llm.bind_tools([tool])

    with mlflow.start_run():
        mlflow.langchain.log_model(
            agent, "agent", registered_model_name="nucor_gold.ai.sales_rag_agent",
            resources=[DatabricksVectorSearchIndex(index_name=INDEX),
                       DatabricksServingEndpoint(endpoint_name=LLM_ENDPOINT)],
            input_example={"messages": [{"role": "user",
                "content": "Which customers buy rebar and slowed orders this quarter?"}]})
    # 3) Serve: agents.deploy handles endpoint + review app + inference tables (audit)
    from databricks import agents
    agents.deploy("nucor_gold.ai.sales_rag_agent", model_version=1,
                  endpoint_name="nucor-sales-rag")

if __name__ == "__main__":
    build_and_deploy()
