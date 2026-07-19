"""Provision the semantic-search stack: source table + Vector Search endpoint + index.

Idempotent and phase-aware — endpoint provisioning is async and can take 10+ minutes,
so the script does whatever the current state allows and reports what remains:
  phase 1: build acme_gold.ai.customer_profile_text (CDF on) from customer_narratives
  phase 2: create endpoint 'acme-vs' if absent (returns immediately, provisions async)
  phase 3: when the endpoint is ONLINE, create the delta-sync index (auto-embeddings
           via databricks-gte-large-en). Rerun the script until phase 3 completes.
Uses databricks-sdk (not the databricks-vectorsearch client) so job/local auth both work.
"""
import sys

ENDPOINT = "acme-vs"
INDEX = "acme_gold.ai.customer_profile_idx"
SOURCE = "acme_gold.ai.customer_profile_text"


def get_spark():
    try:
        from pyspark.sql import SparkSession
        return SparkSession.builder.getOrCreate()
    except Exception:
        from databricks.connect import DatabricksSession
        return DatabricksSession.builder.serverless(True).getOrCreate()


def main():
    from databricks.sdk import WorkspaceClient
    spark = get_spark()
    w = WorkspaceClient()

    spark.sql("CREATE SCHEMA IF NOT EXISTS acme_gold.ai")
    spark.sql(f"""
        CREATE OR REPLACE TABLE {SOURCE}
        TBLPROPERTIES (delta.enableChangeDataFeed = true) AS
        SELECT customer_hk, narrative AS profile_text
        FROM acme_gold.sales.customer_narratives""")
    n = spark.sql(f"SELECT count(*) FROM {SOURCE}").collect()[0][0]
    print(f"phase 1 OK: {SOURCE} rebuilt ({n} rows, CDF enabled)")

    try:
        ep = w.vector_search_endpoints.get_endpoint(ENDPOINT)
        state = ep.endpoint_status.state.value if ep.endpoint_status else "UNKNOWN"
        print(f"phase 2: endpoint '{ENDPOINT}' exists, state={state}")
    except Exception:
        try:
            from databricks.sdk.service.vectorsearch import EndpointType
            w.vector_search_endpoints.create_endpoint(
                name=ENDPOINT, endpoint_type=EndpointType.STANDARD)
            print(f"phase 2 OK: endpoint '{ENDPOINT}' creation started (async, ~10 min)")
            state = "PROVISIONING"
        except Exception as e:
            print(f"phase 2 FAILED: cannot create endpoint — {str(e)[:250]}")
            print("Vector Search may not be enabled for this workspace tier; "
                  "index creation is blocked until it is.")
            return

    if state != "ONLINE":
        print(f"phase 3 pending: endpoint state={state} — rerun this script once ONLINE")
        return

    try:
        w.vector_search_indexes.get_index(INDEX)
        print(f"phase 3: index '{INDEX}' already exists")
    except Exception:
        from databricks.sdk.service.vectorsearch import (
            DeltaSyncVectorIndexSpecRequest, EmbeddingSourceColumn,
            PipelineType, VectorIndexType)
        w.vector_search_indexes.create_index(
            name=INDEX, endpoint_name=ENDPOINT, primary_key="customer_hk",
            index_type=VectorIndexType.DELTA_SYNC,
            delta_sync_index_spec=DeltaSyncVectorIndexSpecRequest(
                source_table=SOURCE, pipeline_type=PipelineType.TRIGGERED,
                embedding_source_columns=[EmbeddingSourceColumn(
                    name="profile_text",
                    embedding_model_endpoint_name="databricks-gte-large-en")]))
        print(f"phase 3 OK: delta-sync index '{INDEX}' created (initial sync async)")


if __name__ == "__main__":
    main()
    sys.exit(0)
