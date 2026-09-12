"""Sobe os DataFrames tratados pro BigQuery."""

import pandas as pd
from google.cloud import bigquery
from google.cloud.bigquery import LoadJobConfig, WriteDisposition

from config import PROJECT_ID, DATASET_ID


def subir_bigquery(df: pd.DataFrame, tabela: str, modo: str = "append"):
    """modo="append" adiciona linhas, modo="replace" substitui a tabela inteira."""
    cliente = bigquery.Client(project=PROJECT_ID)
    tabela_id = f"{PROJECT_ID}.{DATASET_ID}.{tabela}"

    disposicao = WriteDisposition.WRITE_APPEND if modo == "append" else WriteDisposition.WRITE_TRUNCATE
    config = LoadJobConfig(write_disposition=disposicao)

    print(f"Subindo {len(df)} linhas para {tabela_id} (modo={modo}) ...")
    job = cliente.load_table_from_dataframe(df, tabela_id, job_config=config)
    job.result()
    print(f"Concluído: {tabela_id}")
