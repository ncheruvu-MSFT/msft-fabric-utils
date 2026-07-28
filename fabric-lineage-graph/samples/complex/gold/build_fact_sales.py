"""Complex scenario, gold layer: column-level PySpark transformations.

This notebook-style module exercises the column-provenance scanner end to end:
read -> select -> withColumn -> withColumnRenamed -> selectExpr -> saveAsTable.
Scanning it produces (src_col -> tgt_col) lineage with a transform name per hop,
so `scan_repo --column "gold.fact_sales.NetAmount"` can trace the journey.
"""
from pyspark.sql.functions import col


def build_fact_sales():
    # CELL: read silver orders
    orders = spark.read.table("silver.orders_valid")

    # CELL: project + cast the money columns
    typed = orders.select("CustomerId", "Amount", "Discount", "Qty")
    typed = typed.withColumn("GrossAmount", col("Amount").cast("decimal(18,2)"))
    typed = typed.withColumn("NetAmount", col("GrossAmount") * (1 - col("Discount")))

    # CELL: rename + derive units
    renamed = typed.withColumnRenamed("Qty", "Units")
    enriched = renamed.selectExpr(
        "CustomerId",
        "GrossAmount",
        "NetAmount",
        "Units",
        "NetAmount / Units as UnitPrice",
    )

    enriched.write.format("delta").mode("overwrite").saveAsTable("gold.fact_sales")


def build_region_rollup():
    # CELL: aggregate net amount by region via spark.sql
    spark.sql(
        """
        CREATE TABLE gold.agg_sales_region AS
        SELECT Region,
               SUM(NetAmount) AS TotalNet,
               SUM(Units)     AS TotalUnits
        FROM gold.fact_sales_secured
        GROUP BY Region
        """
    )
