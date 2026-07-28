# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "11111111-1111-1111-1111-111111111111",
# META       "default_lakehouse_name": "lh_silver",
# META       "default_lakehouse_workspace_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
# META     }
# META   }
# META }

# MARKDOWN ********************

# ## Sales Pipeline Demo
# Deployed by **fabric-cicd**. The `default_lakehouse` / `default_lakehouse_workspace_id`
# GUIDs above are the DEV values; `parameter.yml` (the variable library) swaps them
# to the correct TEST / PROD GUIDs at deploy time.

# CELL ********************

# Reads from whichever lh_silver the environment is bound to (DEV/TEST/PROD).
df = spark.sql("SELECT stage, COUNT(*) AS opps FROM lh_silver.opportunities GROUP BY stage ORDER BY opps DESC")
display(df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
