# Databricks notebook source
# MAGIC %md
# MAGIC # ASHA Sahayak — Vector Search Index Setup
# MAGIC Creates Databricks Vector Search endpoint and indexes for RAG retrieval.

# COMMAND ----------

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

ENDPOINT_NAME = "asha_vs_endpoint"
CATALOG = "asha_sahayak"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Create Vector Search Endpoint

# COMMAND ----------

try:
    endpoint = w.vector_search_endpoints.create_endpoint(
        name=ENDPOINT_NAME,
        endpoint_type="STANDARD",
    )
    print(f"Created endpoint: {ENDPOINT_NAME}")
except Exception as e:
    print(f"Endpoint may already exist: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Create Guideline Index

# COMMAND ----------

try:
    index = w.vector_search_indexes.create_index(
        name=f"{CATALOG}.serving.guideline_vs_index",
        endpoint_name=ENDPOINT_NAME,
        primary_key="chunk_id",
        index_type="DELTA_SYNC",
        delta_sync_index_spec={
            "source_table": f"{CATALOG}.serving.guideline_chunks",
            "pipeline_type": "TRIGGERED",
            "embedding_source_columns": [
                {"name": "chunk_text", "embedding_model_endpoint_name": "databricks-bge-large-en"}
            ],
        },
    )
    print("Created guideline vector index")
except Exception as e:
    print(f"Index creation note: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Create Patient Memory Index

# COMMAND ----------

try:
    index = w.vector_search_indexes.create_index(
        name=f"{CATALOG}.serving.patient_memory_vs_index",
        endpoint_name=ENDPOINT_NAME,
        primary_key="chunk_id",
        index_type="DELTA_SYNC",
        delta_sync_index_spec={
            "source_table": f"{CATALOG}.serving.patient_memory_chunks",
            "pipeline_type": "TRIGGERED",
            "embedding_source_columns": [
                {"name": "chunk_text", "embedding_model_endpoint_name": "databricks-bge-large-en"}
            ],
        },
    )
    print("Created patient memory vector index")
except Exception as e:
    print(f"Index creation note: {e}")

# COMMAND ----------

print("Vector search setup complete!")
print(f"Endpoint: {ENDPOINT_NAME}")
print("Indexes: guideline_vs_index, patient_memory_vs_index")
print("\nNote: For demo/free tier, the FAISS fallback retriever will be used automatically.")
