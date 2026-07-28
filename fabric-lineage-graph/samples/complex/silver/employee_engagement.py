"""Complex scenario, silver layer: PySpark notebook that joins HR comp data
with web sessions for an "employee analytics" Power BI tile.

Demonstrates how a HIGHLY-CONFIDENTIAL source (hr_compensation) gets pulled
into a notebook-derived table. The DLP gate must flag any downstream report
that is not explicitly cleared for HR data.
"""
hr = spark.read.table("bronze.hr_compensation")
sess = spark.read.table("bronze.web_sessions")

joined = hr.join(sess, hr.employee_id == sess.customer_id, "left")
joined.write.format("delta").mode("overwrite").saveAsTable("silver.employee_engagement")
