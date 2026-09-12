"""
Pipeline do Novo Caged - Movimentação de Empregos na Indústria (Nordeste).

Baixa os microdados mensais direto do FTP do MTE, trata em dois formatos
(mensal agregado e por pessoa) e sobe pro BigQuery.

Uso:
    python run.py 202601              # um mês só
    python run.py 202401 202605       # intervalo
    python run.py                     # tenta o mês mais recente publicado
"""

import sys

from config import PESSOA_INICIO, TABLE_MENSAL, TABLE_PESSOA
from extract import baixar_7z, extrair_7z, competencia_mais_recente
from transform import agregar_mensal, tratar_microdado
from enrich import enriquecer_com_dims
from load import subir_bigquery


def listar_competencias(inicio: str, fim: str) -> list[str]:
    ano_i, mes_i = int(inicio[:4]), int(inicio[4:])
    ano_f, mes_f = int(fim[:4]), int(fim[4:])

    competencias = []
    ano, mes = ano_i, mes_i
    while (ano, mes) <= (ano_f, mes_f):
        competencias.append(f"{ano}{mes:02d}")
        mes += 1
        if mes > 12:
            mes = 1
            ano += 1
    return competencias


def rodar(competencia: str = None, manter_arquivos: bool = False):
    competencia = competencia or competencia_mais_recente()
    print(f"=== Processando competência {competencia} ===")

    caminho_7z = baixar_7z(competencia)
    caminho_txt = extrair_7z(caminho_7z)

    # a mensal sempre é gerada - é a base do histórico pro modelo de ML
    df_mensal = enriquecer_com_dims(agregar_mensal(caminho_txt))
    subir_bigquery(df_mensal, TABLE_MENSAL, modo="append")

    # a de pessoa só entra a partir de PESSOA_INICIO, senão o volume
    # não cabe no storage gratuito do BigQuery
    if competencia >= PESSOA_INICIO:
        df_pessoa = enriquecer_com_dims(tratar_microdado(caminho_txt))
        subir_bigquery(df_pessoa, TABLE_PESSOA, modo="append")
    else:
        print(f"[info] {competencia} é anterior a {PESSOA_INICIO}, pulando movimentacao_pessoa")

    if not manter_arquivos:
        caminho_7z.unlink(missing_ok=True)
        caminho_txt.unlink(missing_ok=True)
        print(f"arquivos brutos de {competencia} removidos do disco")

    print(f"=== Competência {competencia} concluída ===\n")


def rodar_intervalo(inicio: str, fim: str, manter_arquivos: bool = False):
    competencias = listar_competencias(inicio, fim)
    print(f"Processando {len(competencias)} competências: {competencias[0]} a {competencias[-1]}")

    falhas = []
    for comp in competencias:
        try:
            rodar(comp, manter_arquivos=manter_arquivos)
        except Exception as e:
            # um mês ruim (download corrompido, FTP fora do ar) não pode
            # derrubar o processamento dos outros 70+ meses
            print(f"[aviso] falha em {comp}, pulando: {type(e).__name__}: {e}")
            falhas.append(comp)

    print("=== Intervalo concluído ===")
    if falhas:
        print(f"meses que falharam, revisar manualmente: {falhas}")


if __name__ == "__main__":
    args = sys.argv[1:]

    if len(args) == 2:
        rodar_intervalo(args[0], args[1])
    elif len(args) == 1:
        rodar(args[0])
    else:
        rodar()
