"""Junta nome de ocupação, município, UF e seção direto na tabela - evita ter que fazer blend no Looker Studio."""

from pathlib import Path

import pandas as pd

from config import (
    DIM_CBO_PATH, DIM_MUNICIPIO_PATH, DIM_UF_PATH, DIM_SECAO_PATH,
    SECAO_PARA_GRUPAMENTO, GRANDE_GRUPAMENTO_PADRAO, BASE_DIR,
)


def enriquecer_com_dims(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["ano"] = pd.to_datetime(df["competencia"]).dt.year
    df["mes"] = pd.to_datetime(df["competencia"]).dt.month

    # cbo só existe na tabela por pessoa, não na mensal
    if "cbo" in df.columns:
        if DIM_CBO_PATH.exists():
            dim_cbo = pd.read_csv(DIM_CBO_PATH)
            dim_cbo.columns = ["cbo", "descricao_ocupacao"]
            dim_cbo["descricao_ocupacao"] = dim_cbo["descricao_ocupacao"].str.strip().str.title()
            df = df.merge(dim_cbo, on="cbo", how="left")
        else:
            print(f"[aviso] {DIM_CBO_PATH.name} não encontrado, descricao_ocupacao vai ficar vazia")
            df["descricao_ocupacao"] = None

    if DIM_MUNICIPIO_PATH.exists():
        dim_mun = pd.read_csv(DIM_MUNICIPIO_PATH)
        dim_mun.columns = ["municipio_codigo", "descricao_municipio"]
        dim_mun["descricao_municipio"] = dim_mun["descricao_municipio"].str.strip().str.title()
        df = df.merge(dim_mun, on="municipio_codigo", how="left")
    else:
        print(f"[aviso] {DIM_MUNICIPIO_PATH.name} não encontrado, descricao_municipio vai ficar vazia")
        df["descricao_municipio"] = None

    if DIM_UF_PATH.exists():
        dim_uf = pd.read_csv(DIM_UF_PATH)
        dim_uf.columns = ["uf", "sigla_uf"]
        df = df.merge(dim_uf, on="uf", how="left")
    else:
        print(f"[aviso] {DIM_UF_PATH.name} não encontrado, sigla_uf vai ficar vazia")
        df["sigla_uf"] = None

    # útil pro geo chart do Looker, e resolve município com nome
    # repetido em estados diferentes
    df["municipio_uf"] = df["descricao_municipio"] + " - " + df["sigla_uf"]

    if "secao" in df.columns:
        if DIM_SECAO_PATH.exists():
            dim_secao = pd.read_csv(DIM_SECAO_PATH)
            dim_secao.columns = ["secao", "descricao_secao"]
            dim_secao["descricao_secao"] = dim_secao["descricao_secao"].str.strip().str.title()
            df = df.merge(dim_secao, on="secao", how="left")
        else:
            print(f"[aviso] {DIM_SECAO_PATH.name} não encontrado, descricao_secao vai ficar vazia")
            df["descricao_secao"] = None

        df["grande_grupamento"] = df["secao"].map(SECAO_PARA_GRUPAMENTO).fillna(GRANDE_GRUPAMENTO_PADRAO)

    return df


def preparar_dims_locais():
    """Gera os csv de-para a partir dos layouts do MTE. Roda uma vez só (ou quando o layout mudar).

    O layout de Estabelecimento chega em .numbers - exporta ele primeiro
    pra .xlsx pelo próprio app (Arquivo > Exportar Para > Excel) antes de
    rodar essa função.
    """
    layout_movimentacao = BASE_DIR / "Layout_Não-identificado_Novo_Caged_Movimentação.xlsx"
    layout_estabelecimento = BASE_DIR / "Layout_Novo_Caged_Estabelecimento.xlsx"

    cbo = pd.read_excel(layout_movimentacao, sheet_name="cbo2002ocupação")
    cbo.to_csv(DIM_CBO_PATH, index=False)
    print(f"gerado: {DIM_CBO_PATH} ({len(cbo)} linhas)")

    municipio = pd.read_excel(layout_estabelecimento, sheet_name="Município")
    municipio.to_csv(DIM_MUNICIPIO_PATH, index=False)
    print(f"gerado: {DIM_MUNICIPIO_PATH} ({len(municipio)} linhas)")

    uf = pd.read_excel(layout_estabelecimento, sheet_name="UF")
    uf.to_csv(DIM_UF_PATH, index=False)
    print(f"gerado: {DIM_UF_PATH} ({len(uf)} linhas)")

    secao = pd.read_excel(layout_estabelecimento, sheet_name="seção")
    secao.to_csv(DIM_SECAO_PATH, index=False)
    print(f"gerado: {DIM_SECAO_PATH} ({len(secao)} linhas)")
