# Databricks notebook source
# ============================================================
# Loan Credit Risk Analytics - Databricks ETL Pipeline
# ============================================================
# Purpose:
#   1. Read raw loan data from Azure Storage
#   2. Clean and transform the dataset using PySpark
#   3. Create credit-risk and financial features
#   4. Generate a credit-risk summary
#   5. Save transformed data as Delta
#   6. Load transformed data into Azure SQL Database
#
# NOTE:
#   Credentials are intentionally replaced with placeholders.
#   Never commit real passwords, access keys, or tokens to GitHub.
# ============================================================


# ============================================================
# 1. Configuration
# ============================================================

storage_account_name = "<STORAGE_ACCOUNT_NAME>"
storage_account_key = "<STORAGE_ACCOUNT_KEY>"
container_name = "<CONTAINER_NAME>"

bronze_path = (
    f"abfss://{container_name}@"
    f"{storage_account_name}.dfs.core.windows.net/"
    f"datasets/loan_approval_dataset.csv"
)

gold_path = (
    f"abfss://{container_name}@"
    f"{storage_account_name}.dfs.core.windows.net/"
    f"gold/delta_cleaned_loan_data"
)

summary_path = (
    f"abfss://{container_name}@"
    f"{storage_account_name}.dfs.core.windows.net/"
    f"gold/delta_risk_summary"
)


# ============================================================
# 2. Import PySpark Functions
# ============================================================

from pyspark.sql.functions import (
    col,
    trim,
    round as spark_round,
    when,
    avg,
    count
)


# ============================================================
# 3. Read Raw CSV from Azure Storage
# ============================================================

df = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "true")
    .option(
        f"fs.azure.account.key."
        f"{storage_account_name}.dfs.core.windows.net",
        storage_account_key
    )
    .csv(bronze_path)
)


# ============================================================
# 4. Clean Column Headers
# ============================================================

df = df.toDF(*[c.strip() for c in df.columns])


# ============================================================
# 5. Clean String Columns
# ============================================================

for col_name, col_type in df.dtypes:
    if col_type == "string":
        df = df.withColumn(
            col_name,
            trim(col(col_name))
        )


# ============================================================
# 6. Feature Engineering
# ============================================================

# Total Assets
df = df.withColumn(
    "total_assets",
    col("residential_assets_value")
    + col("commercial_assets_value")
    + col("luxury_assets_value")
    + col("bank_asset_value")
)


# Loan-to-Income Ratio
df = df.withColumn(
    "lti_ratio",
    spark_round(
        col("loan_amount") / col("income_annum"),
        2
    )
)


# Loan-to-Asset Ratio
df = df.withColumn(
    "ltv_ratio",
    spark_round(
        col("loan_amount") / col("total_assets"),
        2
    )
)


# ============================================================
# 7. Create Credit Risk Band
# ============================================================

df = df.withColumn(
    "credit_risk_band",
    when(
        col("cibil_score") >= 750,
        "Excellent (Prime)"
    )
    .when(
        col("cibil_score") >= 650,
        "Good"
    )
    .when(
        col("cibil_score") >= 550,
        "Fair"
    )
    .otherwise(
        "Poor (High Risk)"
    )
)


# ============================================================
# 8. Create Credit Risk Summary
# ============================================================

risk_summary = (
    df
    .groupby("credit_risk_band")
    .agg(
        count("loan_id").alias("total_applicants"),

        spark_round(
            avg("income_annum"),
            2
        ).alias("avg_income"),

        spark_round(
            avg("loan_amount"),
            2
        ).alias("avg_loan_amount"),

        spark_round(
            avg("lti_ratio"),
            2
        ).alias("avg_lti"),

        spark_round(
            avg("ltv_ratio"),
            2
        ).alias("avg_ltv"),

        spark_round(
            avg("cibil_score"),
            2
        ).alias("avg_cibilscore")
    )
    .orderBy(
        "avg_cibilscore",
        ascending=False
    )
)


# ============================================================
# 9. Display Risk Summary
# ============================================================

display(risk_summary)


# ============================================================
# 10. Save Cleaned Data as Delta
# ============================================================

(
    df.write
    .mode("overwrite")
    .format("delta")
    .option(
        f"fs.azure.account.key."
        f"{storage_account_name}.dfs.core.windows.net",
        storage_account_key
    )
    .save(gold_path)
)


# ============================================================
# 11. Save Risk Summary as Delta
# ============================================================

(
    risk_summary.write
    .mode("overwrite")
    .format("delta")
    .option(
        f"fs.azure.account.key."
        f"{storage_account_name}.dfs.core.windows.net",
        storage_account_key
    )
    .save(summary_path)
)


print(
    "PySpark transformation completed successfully. "
    "Cleaned data and risk summary saved to Delta."
)


# ============================================================
# 12. Load Transformed Data into Azure SQL Database
# ============================================================

sql_host = "<SQL_SERVER>.database.windows.net"
sql_database = "<DATABASE_NAME>"
sql_user = "<SQL_USERNAME>"
sql_password = "<SQL_PASSWORD>"


(
    df.write
    .format("sqlserver")
    .option("host", sql_host)
    .option("port", "1433")
    .option("database", sql_database)
    .option("user", sql_user)
    .option("password", sql_password)
    .option("encrypt", "true")
    .option("trustServerCertificate", "true")
    .mode("overwrite")
    .save()
)


print(
    "Transformed loan data successfully loaded "
    "into Azure SQL Database."
)
