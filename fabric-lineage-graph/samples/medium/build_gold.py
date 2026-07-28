"""Medium scenario: PySpark notebook reading the silver Delta table and writing
a gold aggregate. Exercises the NotebookHarvester AST walker.

Expected: 1 spark_save_as_table edge silver.customer_orders -> gold.customer_metrics.
"""
df = spark.read.table("silver.customer_orders")
agg = df.groupBy("customer_id").count()
agg.write.format("delta").mode("overwrite").saveAsTable("gold.customer_metrics")
