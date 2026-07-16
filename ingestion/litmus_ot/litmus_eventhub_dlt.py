"""Litmus Edge UNS topics -> Event Hubs (Kafka API) -> Bronze OT tables. Config-driven."""
import dlt, yaml
from pyspark.sql import functions as F, types as T

CFG = yaml.safe_load(open("/Workspace/Repos/platform/config/replication_sources.yaml"))
SRC = next(s for s in CFG["sources"] if s["name"] == spark.conf.get("source_name"))
EH = f'{SRC["eventhub_namespace"]}.servicebus.windows.net:9093'

OT_SCHEMA = T.StructType([
    T.StructField("deviceID", T.StringType()), T.StructField("tagName", T.StringType()),
    T.StructField("value", T.DoubleType()),    T.StructField("timestamp", T.LongType()),
    T.StructField("quality", T.StringType()),  T.StructField("metadata", T.MapType(T.StringType(), T.StringType()))])

@dlt.table(name=SRC["target"].split(".",1)[1].replace(".","_"),
           comment="OT telemetry, UNS-normalized at edge by Litmus")
@dlt.expect_all_or_drop(SRC.get("expectations", {}))
def ot_bronze():
    raw = (spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", EH)
        .option("subscribePattern", SRC["topic_filter"].replace("+", "[^/]+").replace("#", ".*"))
        .option("kafka.security.protocol", "SASL_SSL")
        .option("kafka.sasl.mechanism", "OAUTHBEARER")   # Entra ID auth, no conn strings
        .load())
    parsed = raw.select(
        F.col("topic"),
        F.from_json(F.col("value").cast("string"), OT_SCHEMA).alias("p"),
        F.col("timestamp").alias("_kafka_ts"))
    # UNS topic: acme/<site>/<area>/<asset>/<tag>
    parts = F.split("topic", "/")
    return (parsed
        .select(parts[1].alias("site"), parts[2].alias("area"), parts[3].alias("asset"),
                F.col("p.tagName").alias("tag"),
                F.to_timestamp(F.col("p.timestamp")/1000).alias("ts"),
                F.col("p.value"), F.col("p.quality"),
                F.to_json("p").alias("_raw"))
        .withWatermark("ts", SRC.get("watermark", "10 minutes"))
        .withColumn("_source_system", F.lit("LITMUS"))
        .withColumn("_ingest_ts", F.current_timestamp()))

