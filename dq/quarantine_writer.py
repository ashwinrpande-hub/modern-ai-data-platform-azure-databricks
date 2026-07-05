"""
Quarantine + batch logger (fills gaps A2/A3 in docs/GAP_ANALYSIS.md).
Runs as a Lakeflow Job task after every pipeline update (see pipelines/jobs/lakeflow_jobs.yaml).

What it does — from each pipeline's event log (event_log() TVF, no direct storage paths):
 1. flow_progress metrics  -> nucor_bronze.audit.batch_log   (rows read/written/dropped, status)
 2. expectation failures   -> nucor_bronze.audit.rejected_records (rule + DAMA dimension)
DAMA dimension is inferred from the expectation name prefix used in replication_sources.yaml
(valid_* = VALIDITY, complete_/*_pk = COMPLETENESS, ts/timely = TIMELINESS, etc.).
"""
from pyspark.sql import SparkSession, functions as F
import sys

spark = SparkSession.builder.getOrCreate()
PIPELINE_IDS = sys.argv[1:] or [r[0] for r in spark.sql(
    "SELECT pipeline_id FROM nucor_bronze.cfg.pipeline_registry WHERE active").collect()]

DIM_MAP = [("pk", "COMPLETENESS"), ("complete", "COMPLETENESS"), ("valid", "VALIDITY"),
           ("ts", "TIMELINESS"), ("timely", "TIMELINESS"), ("uniq", "UNIQUENESS"),
           ("quality", "ACCURACY"), ("format", "CONSISTENCY")]

def dama_dim(col):  # SQL CASE from expectation-name conventions
    case = "CASE "
    for token, dim in DIM_MAP:
        case += f"WHEN lower({col}) LIKE '%{token}%' THEN '{dim}' "
    return case + "ELSE 'VALIDITY' END"

for pid in PIPELINE_IDS:
    ev = spark.sql(f"SELECT * FROM event_log('{pid}')")

    # ---- 1. batch_log from flow_progress ----
    (ev.filter("event_type = 'flow_progress' AND details:flow_progress.metrics IS NOT NULL")
       .selectExpr(
           "origin.update_id            AS batch_id",
           "origin.flow_name            AS source_name",
           "'bronze'                    AS layer",
           "cast(details:flow_progress.metrics.num_output_rows AS BIGINT)  AS rows_written",
           "cast(details:flow_progress.data_quality.dropped_records AS BIGINT) AS rows_rejected",
           "timestamp                   AS finished_at",
           "details:flow_progress.status AS status")
       .withColumn("rows_read", F.col("rows_written") + F.coalesce("rows_rejected", F.lit(0)))
       .withColumn("started_at", F.col("finished_at"))   # per-flow granularity; update span in job UI
       .withColumn("error", F.lit(None).cast("string"))
       .select("batch_id","source_name","layer","rows_read","rows_written",
               "rows_rejected","started_at","finished_at","status","error")
       .write.mode("append").saveAsTable("nucor_bronze.audit.batch_log"))

    # ---- 2. rejected_records from expectation drops (rule-level; row payloads stay in
    #         the failing flow's quarantine view when expect_all_or_drop is used) ----
    exp = ev.filter("event_type = 'flow_progress'").selectExpr(
        "origin.update_id AS batch_id", "origin.flow_name AS source_name",
        "explode_outer(from_json(details:flow_progress.data_quality.expectations, "
        "'array<struct<name:string,dataset:string,passed_records:bigint,failed_records:bigint>>')) AS e"
    ).filter("e.failed_records > 0")
    (exp.selectExpr(
            "uuid() AS reject_id", "batch_id", "source_name",
            "e.dataset AS target_table", "'bronze' AS layer",
            "e.name AS failed_rule",
            f"{dama_dim('e.name')} AS dq_dimension",
            "to_json(named_struct('failed_records', e.failed_records)) AS record_payload",
            "current_timestamp() AS rejected_at")
        .write.mode("append").saveAsTable("nucor_bronze.audit.rejected_records"))

print(f"quarantine_writer: processed {len(PIPELINE_IDS)} pipeline event logs")
