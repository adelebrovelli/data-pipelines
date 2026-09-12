"""Transforma o .txt bruto do Caged nos dois formatos que a gente usa: mensal e por pessoa."""

from pathlib import Path

import pandas as pd

from config import COLUNAS_NECESSARIAS, SALARIO_TETO, UF_NORDESTE


def agregar_mensal(caminho_txt: Path, tamanho_chunk: int = 500_000) -> pd.DataFrame:
    """Agrega por competência + UF + município + seção, separando admissão de desligamento.

    Formato leve - é o que alimenta a série temporal (ML) e o gráfico de
    linha do BI. Pra drill-down pessoa a pessoa usa tratar_microdado().
    """
    agregados = []

    leitor = pd.read_csv(
        caminho_txt,
        sep=";",
        decimal=",",
        usecols=COLUNAS_NECESSARIAS,
        chunksize=tamanho_chunk,
        encoding="utf-8",
    )

    chaves = ["competênciamov", "uf", "município", "seção", "tipo"]

    for i, chunk in enumerate(leitor):
        chunk = chunk[chunk["uf"].isin(UF_NORDESTE)]
        chunk["tipo"] = chunk["saldomovimentação"].map({1: "admissao", -1: "desligamento"})
        chunk = chunk.dropna(subset=["tipo"])
        chunk["salário"] = pd.to_numeric(chunk["salário"], errors="coerce")

        agg_total = chunk.groupby(chaves).agg(qtd=("salário", "size")).reset_index()

        # a soma de salário e a contagem "válida" ficam separadas da
        # contagem total - assim dá pra filtrar outlier de salário sem
        # perder ninguém da contagem de admitidos/desligados
        chunk_valido = chunk[(chunk["salário"] > 0) & (chunk["salário"] <= SALARIO_TETO)]
        agg_salario = (
            chunk_valido.groupby(chaves)
            .agg(qtd_valido=("salário", "size"), soma_salario=("salário", "sum"))
            .reset_index()
        )

        agg = agg_total.merge(agg_salario, on=chaves, how="left")
        agregados.append(agg)
        print(f"  [mensal] chunk {i + 1} processado ({len(chunk)} linhas)")

    bruto = pd.concat(agregados, ignore_index=True)
    bruto = (
        bruto.groupby(chaves)
        .agg(qtd=("qtd", "sum"), qtd_valido=("qtd_valido", "sum"), soma_salario=("soma_salario", "sum"))
        .reset_index()
    )

    final = bruto.pivot_table(
        index=["competênciamov", "uf", "município", "seção"],
        columns="tipo",
        values=["qtd", "qtd_valido", "soma_salario"],
        fill_value=0,
    )
    final.columns = ["_".join(col) for col in final.columns]
    final = final.reset_index()

    final = final.rename(columns={
        "competênciamov": "competencia",
        "município": "municipio_codigo",
        "seção": "secao",
    })
    final["competencia"] = pd.to_datetime(final["competencia"].astype(str), format="%Y%m").dt.date

    print(f"Agregação mensal: {len(final)} linhas (competência + UF + município + seção)")
    return final


def tratar_microdado(caminho_txt: Path, tamanho_chunk: int = 500_000) -> pd.DataFrame:
    """Retorna o dado em nível de pessoa - uma linha por admissão ou desligamento.

    Salário fora de faixa plausível (quase sempre erro de digitação na
    declaração original) vira NULL em vez da linha ser descartada. Assim a
    pessoa continua contando pro total oficial de admitidos/desligados,
    só não entra na média salarial - o BigQuery ignora NULL em AVG().
    """
    partes = []

    leitor = pd.read_csv(
        caminho_txt,
        sep=";",
        decimal=",",
        usecols=COLUNAS_NECESSARIAS,
        chunksize=tamanho_chunk,
        encoding="utf-8",
    )

    for i, chunk in enumerate(leitor):
        chunk = chunk[chunk["uf"].isin(UF_NORDESTE)]
        chunk["tipo"] = chunk["saldomovimentação"].map({1: "admissao", -1: "desligamento"})
        chunk = chunk.dropna(subset=["tipo"])
        chunk["salário"] = pd.to_numeric(chunk["salário"], errors="coerce")

        zerado_negativo = chunk["salário"] <= 0
        acima_teto = chunk["salário"] > SALARIO_TETO
        chunk.loc[zerado_negativo | acima_teto, "salário"] = pd.NA

        chunk = chunk.drop(columns=["saldomovimentação"])
        partes.append(chunk)
        print(
            f"  chunk {i + 1} processado ({len(chunk)} linhas) - "
            f"salário NULL: {zerado_negativo.sum()} zerado/negativo, {acima_teto.sum()} acima de R${SALARIO_TETO:,}"
        )

    df = pd.concat(partes, ignore_index=True)
    df = df.rename(columns={
        "competênciamov": "competencia",
        "cbo2002ocupação": "cbo",
        "município": "municipio_codigo",
        "salário": "salario",
        "seção": "secao",
    })
    df["competencia"] = pd.to_datetime(df["competencia"].astype(str), format="%Y%m").dt.date

    print(f"Tratamento final: {len(df)} linhas (uma por pessoa/evento)")
    return df
