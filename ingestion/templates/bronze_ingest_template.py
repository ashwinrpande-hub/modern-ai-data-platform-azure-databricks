"""
Generic config-driven Bronze ingestion (Lakeflow Spark Declarative Pipelines).
Covers patterns: goldengate (ADLS landing), litmus_adls, autoloader_file.
ANY new source = a row in config/replication_sources.yaml. Do not copy this file.
Pipeline config must set:  spark.conf 'source_name' = <name from YAML>
2026 update: AUTO CDC (create_auto_cdc_flow) is the current API; apply_changes is the
deprecated alias — fallback kept for older runtimes.
"""
import dlt, yaml
from pyspark.sql import functions as F

CFG = yaml.safe_load(open("/Workspace/Repos/platform/config/replication_sources.yaml"))
SRC = next(s for s in CFG["sources"] if s["name"] == spark.conf.get("source_name"))
LAND = f'{CFG["defaults"]["landing_root"]}/{SRC["landing_path"]}'
FMT = SRC.get("format", "avro")           # GoldenGate default: avro
TGT = SRC["target"].split(".")            # bronze.<schema>.<table>

def with_envelope(df):
    return (df
        .withColumn("_source_system", F.lit(SRC["system"]))
        .withColumn("_ingest_ts", F.current_timestamp())
        .withColumn("_batch_id", F.lit(spark.conf.get("pipelines.id", "manual")))
        .withColumn("_raw", F.to_json(F.struct("*"))))

@dlt.table(name=f"{TGT[1]}_{TGT[2]}_staging", temporary=True)
def staging():
    return with_envelope(
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", FMT)
        .option("cloudFiles.schemaLocation", f"{LAND}/_schema")
        .option("cloudFiles.inferColumnTypes", "true")
        .load(LAND))

# Expectations from YAML; drops are logged to audit tables by dq/quarantine_writer.py
# (reads the pipeline event log after each update — see pipelines/jobs/lakeflow_jobs.yaml)
EXPECTATIONS = SRC.get("expectations", {})

if SRC["pattern"] == "goldengate":
    # CDC apply: GoldenGate emits op_type (I/U/D) + csn
    dlt.create_streaming_table(name=f"{TGT[1]}_{TGT[2]}", expect_all_or_drop=EXPECTATIONS)
    cdc_args = dict(
        target=f"{TGT[1]}_{TGT[2]}",
        source=f"{TGT[1]}_{TGT[2]}_staging",
        keys=SRC["primary_key"],
        sequence_by=F.col(SRC["sequence_col"]),
        apply_as_deletes=F.expr("op_type = 'D'"),
        except_column_list=["op_type"],
        stored_as_scd_type=1)             # Bronze = current mirror; history kept in Silver
    if hasattr(dlt, "create_auto_cdc_flow"):     # 2026 API
        dlt.create_auto_cdc_flow(**cdc_args)
    else:                                        # pre-AUTO-CDC runtimes
        dlt.apply_changes(**cdc_args)
else:
    @dlt.table(name=f"{TGT[1]}_{TGT[2]}")
    @dlt.expect_all_or_drop(EXPECTATIONS)
    def bronze_table():
        return dlt.read_stream(f"{TGT[1]}_{TGT[2]}_staging")
