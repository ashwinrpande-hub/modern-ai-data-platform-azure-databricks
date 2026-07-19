"""Vector / Content agent — owns the Gold AI zone (semantic-search content).

Deterministic: rebuilds acme_gold.sales.customer_narratives — one natural-language
profile per customer (name, country, source, revenue, order count, backlog), the text
a Mosaic AI Vector Search index would embed. LLM pass: samples narratives and QA-reviews
them for retrieval quality (specificity, embedding-friendliness), filing suggestions.
Index provisioning itself (endpoint + delta-sync index) is an infra step outside this job.
"""
import sys
import os
from datetime import datetime, timezone

_HERE = os.path.dirname(os.path.abspath(globals().get("__file__") or sys.argv[0]))
sys.path.insert(0, _HERE)
from agent_core import ensure_audit_tables, get_spark, log_run, run_reasoning, save_report

QA_SYSTEM = """You are the content-QA agent for a semantic-search corpus over customer
profiles in a steel-industry sales lakehouse. Narratives will be embedded for Vector
Search / RAG retrieval. Review the samples for: retrieval-relevant specificity, consistent
structure, units stated, no bare hash keys or codes a query would never contain, and
whether churn/backlog signals are phrased in words a seller would actually search.
You may use run_sql (read-only) to look at more rows. Output a short markdown QA report
with concrete rewrite suggestions. You never execute writes."""


def main():
    started = datetime.now(timezone.utc)
    spark = get_spark()
    ensure_audit_tables(spark)
    log = []

    spark.sql("""
        CREATE OR REPLACE TABLE acme_gold.sales.customer_narratives AS
        SELECT d.customer_hk,
               d.customer_name,
               concat(
                 'Customer: ', d.customer_name, ' (', coalesce(d.country, 'unknown country'),
                 ', source system ', d.source_system, '). ',
                 'Orders: ', coalesce(m.orders, 0),
                 '; total revenue USD ', cast(round(coalesce(m.revenue, 0), 0) AS BIGINT), '. ',
                 'Unshipped backlog: ', coalesce(m.backlog, 0), ' order(s). ',
                 CASE WHEN coalesce(m.backlog, 0) > 0
                      THEN 'Has open fulfillment backlog awaiting shipment.'
                      ELSE 'No open backlog.' END
               ) AS narrative
        FROM acme_gold.sales.dim_customer d
        LEFT JOIN (
          SELECT b.customer_hk,
                 count(*) AS orders,
                 sum(f.order_amount_usd) AS revenue,
                 count_if(NOT b.is_shipped) AS backlog
          FROM acme_gold.sales.bridge_order_fulfillment b
          JOIN acme_gold.sales.fact_sales_orders f ON f.order_hk = b.order_hk
          GROUP BY b.customer_hk
        ) m ON m.customer_hk = d.customer_hk""")
    n = spark.sql("SELECT count(*) FROM acme_gold.sales.customer_narratives").collect()[0][0]
    log.append(f"customer_narratives rebuilt: {n} rows")
    print(f"customer_narratives rebuilt: {n} rows")

    samples = spark.sql(
        "SELECT narrative FROM acme_gold.sales.customer_narratives ORDER BY customer_hk LIMIT 3").collect()
    sample_text = "\n\n".join(r.narrative for r in samples)

    report = run_reasoning(
        spark, "vector_content", QA_SYSTEM,
        f"The corpus has {n} narratives. Three samples:\n\n{sample_text}\n\nQA-review the corpus.", log)
    if report:
        save_report(spark, "vector_content", "Narrative corpus QA review", report)
        print("\n===== QA REVIEW =====\n" + report)

    mode = "llm" if report else "deterministic"
    log_run(spark, "vector_content", mode, "CORPUS_REBUILT", started, log)
    print(f"vector_content finished: mode={mode}")


if __name__ == "__main__":
    main()
