
import sys
import subprocess
from pathlib import Path
from datetime import date
import pandas as pd
 

FTP_BASE = "ftp://ftp.mtps.gov.br/pdet/microdados/NOVO%20CAGED"
DOWNLOAD_DIR = Path(__file__).parent / "dados" 
PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
DATASET_ID = os.environ.get("GCP_DATASET_ID", "caged_pressao_salarial")

if not PROJECT_ID:
    raise ValueError("GCP_PROJECT_ID não definido. Crie um .env com essa variável (veja .env.example).")
TABLE_MENSAL = "movimentacao_mensal"         # série mensal agregada (2020-hoje) - pra ML e gráfico de linha do BI
TABLE_PESSOA = "movimentacao_pessoa"         # detalhe por pessoa (2025-05 em diante) - pra drill-down no BI
TABLE_CBO = "dim_cbo"                        # de-para ocupação
TABLE_MUNICIPIO = "dim_municipio"            # de-para município
TABLE_UF = "dim_uf"                          # de-para UF
 
# a partir de qual competência (AAAAMM) também geramos a tabela detalhada
# por pessoa - meses antes disso só entram na tabela mensal agregada
PESSOA_INICIO = "202505"
 
# teto de sanidade pro salário individual 
SALARIO_TETO = 100_000

DIM_CBO_PATH = Path(__file__).parent / "dim_cbo.csv"
DIM_MUNICIPIO_PATH = Path(__file__).parent / "dim_municipio.csv"
DIM_UF_PATH = Path(__file__).parent / "dim_uf.csv"
 
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
 

def competencia_mais_recente() -> str:
    """
    Estima a competência (AAAAMM) mais recente provavelmente disponível.
    O Caged costuma publicar o mês M com ~1 mês de defasagem, então
    usamos o mês anterior ao atual como chute inicial.
    """
    hoje = date.today()
    mes = hoje.month - 1 or 12
    ano = hoje.year if hoje.month > 1 else hoje.year - 1
    return f"{ano}{mes:02d}"
 
 
def baixar_7z(competencia: str) -> Path:
    """Baixa o CAGEDMOV{competencia}.7z do FTP oficial do MTE."""
    ano = competencia[:4]
    nome_arquivo = f"CAGEDMOV{competencia}.7z"
    url = f"{FTP_BASE}/{ano}/{competencia}/{nome_arquivo}"
    destino = DOWNLOAD_DIR / nome_arquivo
 
    print(f"Baixando {url} ...")
    resultado = subprocess.run(
        ["curl", "-f", "-o", str(destino), url],
        capture_output=True, text=True
    )
    if resultado.returncode != 0:
        raise RuntimeError(
            f"Falha ao baixar {competencia}. "
            f"Verifique se o mês já foi publicado.\n{resultado.stderr}"
        )
    print(f"Baixado: {destino} ({destino.stat().st_size / 1e6:.1f} MB)")
    return destino
 
 
def extrair_7z(caminho_7z: Path) -> Path:
    """Extrai o .7z e retorna o caminho do .txt resultante."""
    print(f"Extraindo {caminho_7z.name} ...")
    resultado = subprocess.run(
        ["7z", "x", "-y", f"-o{DOWNLOAD_DIR}", str(caminho_7z)],
        capture_output=True, text=True
    )
    if resultado.returncode != 0:
        raise RuntimeError(
            f"Falha ao extrair {caminho_7z.name}. "
            f"Confira se o 7z (p7zip) está instalado: brew install p7zip\n"
            f"{resultado.stderr}"
        )
    txt_esperado = DOWNLOAD_DIR / caminho_7z.name.replace(".7z", ".txt")
    if not txt_esperado.exists():
        # em alguns meses o nome interno pode variar levemente
        txts = list(DOWNLOAD_DIR.glob("CAGEDMOV*.txt"))
        if not txts:
            raise FileNotFoundError("Extração não gerou nenhum .txt esperado")
        txt_esperado = txts[0]
    print(f"Extraído: {txt_esperado}")
    return txt_esperado
 
 
COLUNAS_NECESSARIAS = [
    "competênciamov", "uf", "município", "cbo2002ocupação",
    "salário", "saldomovimentação",
]
 
def agregar_mensal(caminho_txt: Path, tamanho_chunk: int = 500_000) -> pd.DataFrame:
    """
    Lê o .txt em pedaços e agrega por competência + UF + município,
    separando admissão/desligamento. Formato leve (soma + contagem),
    pensado pra alimentar série temporal / modelo de ML e o gráfico de
    linha do BI - não pra drill-down pessoa a pessoa (isso é a
    movimentacao_pessoa, tratada por tratar_microdado()).
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
 
    for i, chunk in enumerate(leitor):
        chunk["tipo"] = chunk["saldomovimentação"].map({1: "admissao", -1: "desligamento"})
        chunk = chunk.dropna(subset=["tipo"])
 
        agg_total = (
            chunk.groupby(["competênciamov", "uf", "município", "tipo"])
            .agg(qtd=("salário", "size"))
            .reset_index()
        )
 
        chunk_valido = chunk[(chunk["salário"] > 0) & (chunk["salário"] <= SALARIO_TETO)]
        agg_salario = (
            chunk_valido.groupby(["competênciamov", "uf", "município", "tipo"])
            .agg(qtd_valido=("salário", "size"), soma_salario=("salário", "sum"))
            .reset_index()
        )
 
        agg = agg_total.merge(
            agg_salario, on=["competênciamov", "uf", "município", "tipo"], how="left"
        )
        agregados.append(agg)
        print(f"  [mensal] chunk {i + 1} processado ({len(chunk)} linhas)")
 
    bruto = pd.concat(agregados, ignore_index=True)
    bruto = (
        bruto.groupby(["competênciamov", "uf", "município", "tipo"])
        .agg(qtd=("qtd", "sum"), qtd_valido=("qtd_valido", "sum"), soma_salario=("soma_salario", "sum"))
        .reset_index()
    )
 
    final = bruto.pivot_table(
        index=["competênciamov", "uf", "município"],
        columns="tipo",
        values=["qtd", "qtd_valido", "soma_salario"],
        fill_value=0,
    )
    final.columns = ["_".join(col) for col in final.columns]
    final = final.reset_index()
 
    final = final.rename(columns={
        "competênciamov": "competencia",
        "município": "municipio_codigo",
    })
    final["competencia"] = pd.to_datetime(
        final["competencia"].astype(str), format="%Y%m"
    ).dt.date
 
    print(f"Agregação mensal: {len(final)} linhas (competência+UF+município)")
    return final
 
 
def tratar_microdado(caminho_txt: Path, tamanho_chunk: int = 500_000) -> pd.DataFrame:
    """
    Lê o .txt em pedaços (chunks) e retorna o dado tratado em nível de
    PESSOA - uma linha por evento de admissão/desligamento, não mais
    agregado por grupo. Isso permite usar AVG() direto no Looker Studio,
    sem precisar de campo calculado com SUM()/SUM().
 
    Salários fora de um range plausível (provável erro de digitação na
    declaração original do CAGED) viram NULL em vez de a linha ser
    descartada - assim a pessoa continua contando como admitida/desligada
    (bate com o total oficial do Novo Caged), só não entra na conta de
    salário médio (BigQuery/Looker ignoram NULL em AVG automaticamente).
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
        chunk["tipo"] = chunk["saldomovimentação"].map({1: "admissao", -1: "desligamento"})
        chunk = chunk.dropna(subset=["tipo"])
 
        zerado_negativo = chunk["salário"] <= 0
        acima_teto = chunk["salário"] > SALARIO_TETO
        outlier = zerado_negativo | acima_teto
        chunk.loc[outlier, "salário"] = pd.NA
 
        chunk = chunk.drop(columns=["saldomovimentação"])
        partes.append(chunk)
        print(
            f"  chunk {i + 1} processado ({len(chunk)} linhas) - "
            f"salário NULL: {zerado_negativo.sum()} zerado/negativo, "
            f"{acima_teto.sum()} acima de R${SALARIO_TETO:,}"
        )
 
    df = pd.concat(partes, ignore_index=True)
 
    df = df.rename(columns={
        "competênciamov": "competencia",
        "cbo2002ocupação": "cbo",
        "município": "municipio_codigo",
        "salário": "salario",
    })
 
    # converte competencia de AAAAMM (ex: 202601) pra DATE de verdade
    # (dia 1 do mês), pra Looker Studio reconhecer como série temporal
    df["competencia"] = pd.to_datetime(
        df["competencia"].astype(str), format="%Y%m"
    ).dt.date
 
    print(f"Tratamento final: {len(df)} linhas (uma por pessoa/evento)")
    return df
 
 
def enriquecer_com_dims(df: pd.DataFrame) -> pd.DataFrame:
    """
    Junta os nomes de CBO, Município e UF direto na tabela agregada,
    além de derivar ano/mes como colunas separadas. Isso evita precisar
    de blend no Looker Studio - a tabela já chega "pronta pra usar".
 
    Requer os arquivos dim_cbo.csv, dim_municipio.csv e dim_uf.csv na
    pasta do projeto (gerados uma vez a partir dos layouts do MTE -
    veja preparar_dims_locais() mais abaixo).
    """
    df = df.copy()
 
    # ano/mes como inteiros, além do DATE, facilita filtro no Looker
    df["ano"] = pd.to_datetime(df["competencia"]).dt.year
    df["mes"] = pd.to_datetime(df["competencia"]).dt.month
 
    if "cbo" in df.columns:
        if DIM_CBO_PATH.exists():
            dim_cbo = pd.read_csv(DIM_CBO_PATH)
            dim_cbo.columns = ["cbo", "descricao_ocupacao"]
            dim_cbo["descricao_ocupacao"] = dim_cbo["descricao_ocupacao"].str.strip().str.title()
            df = df.merge(dim_cbo, on="cbo", how="left")
        else:
            print(f"[AVISO] {DIM_CBO_PATH.name} não encontrado - descricao_ocupacao ficará vazia")
            df["descricao_ocupacao"] = None
 
    if DIM_MUNICIPIO_PATH.exists():
        dim_mun = pd.read_csv(DIM_MUNICIPIO_PATH)
        dim_mun.columns = ["municipio_codigo", "descricao_municipio"]
        dim_mun["descricao_municipio"] = dim_mun["descricao_municipio"].str.strip().str.title()
        df = df.merge(dim_mun, on="municipio_codigo", how="left")
    else:
        print(f"[AVISO] {DIM_MUNICIPIO_PATH.name} não encontrado - descricao_municipio ficará vazia")
        df["descricao_municipio"] = None
 
    if DIM_UF_PATH.exists():
        dim_uf = pd.read_csv(DIM_UF_PATH)
        dim_uf.columns = ["uf", "sigla_uf"]
        df = df.merge(dim_uf, on="uf", how="left")
    else:
        print(f"[AVISO] {DIM_UF_PATH.name} não encontrado - sigla_uf ficará vazia")
        df["sigla_uf"] = None
 
    # coluna combinada município + UF, resolve ambiguidade de nome
    # repetido em estados diferentes e ajuda o geo chart do Looker
    df["municipio_uf"] = df["descricao_municipio"] + " - " + df["sigla_uf"]
 
    return df
 
 
def preparar_dims_locais():
    """
    Gera os CSVs de-para (dim_cbo.csv, dim_municipio.csv, dim_uf.csv) na
    pasta do projeto, a partir dos arquivos de layout do MTE.
    Rode isso uma única vez (ou quando o MTE atualizar o layout).
 
    Ajuste os nomes dos arquivos de layout abaixo conforme o que você
    baixou. O de Município/UF está no layout "Estabelecimento" (.numbers -
    exporte antes pra .xlsx pelo próprio app Numbers: Arquivo > Exportar
    Para > Excel). O de CBO está no layout "Movimentação" (.xlsx).
    """
    caminho_layout_mov = Path(__file__).parent / "Layout_Não-identificado_Novo_Caged_Movimentação.xlsx"
    caminho_layout_estab = Path(__file__).parent / "Layout_Novo_Caged_Estabelecimento.xlsx"  # já exportado do Numbers
 
    cbo = pd.read_excel(caminho_layout_mov, sheet_name="cbo2002ocupação")
    cbo.to_csv(DIM_CBO_PATH, index=False)
    print(f"Gerado: {DIM_CBO_PATH} ({len(cbo)} linhas)")
 
    municipio = pd.read_excel(caminho_layout_estab, sheet_name="Município")
    municipio.to_csv(DIM_MUNICIPIO_PATH, index=False)
    print(f"Gerado: {DIM_MUNICIPIO_PATH} ({len(municipio)} linhas)")
 
    uf = pd.read_excel(caminho_layout_estab, sheet_name="UF")
    uf.to_csv(DIM_UF_PATH, index=False)
    print(f"Gerado: {DIM_UF_PATH} ({len(uf)} linhas)")
 

def subir_bigquery(df: pd.DataFrame, tabela: str, modo: str = "append"):
    """
    Sobe um DataFrame pro BigQuery.
    modo="append"    -> adiciona linhas (usar pro fato mensal)
    modo="replace"    -> substitui a tabela inteira (usar pras dimensões CBO/Município)
    """
    from google.cloud import bigquery
    from google.cloud.bigquery import LoadJobConfig, WriteDisposition
 
    cliente = bigquery.Client(project=PROJECT_ID)
    tabela_id = f"{PROJECT_ID}.{DATASET_ID}.{tabela}"
 
    disposicao = (
        WriteDisposition.WRITE_APPEND if modo == "append"
        else WriteDisposition.WRITE_TRUNCATE
    )
    config = LoadJobConfig(write_disposition=disposicao)
 
    print(f"Subindo {len(df)} linhas para {tabela_id} (modo={modo}) ...")
    job = cliente.load_table_from_dataframe(df, tabela_id, job_config=config)
    job.result()  
    print(f"Concluído: {tabela_id}")
 
 
def subir_tabelas_de_para():
    """
    Sobe as tabelas de-para de CBO e Município pro BigQuery.
    Rode isso uma única vez (ou sempre que o layout for atualizado pelo MTE).
    Ajuste os caminhos abaixo pros arquivos de layout que você já baixou.
    """
    caminho_layout_mov = "Layout_Não-identificado_Novo_Caged_Movimentação.xlsx"
    caminho_layout_estab = "Layout_Novo_Caged_Estabelecimento.numbers"
 
    cbo = pd.read_excel(caminho_layout_mov, sheet_name="cbo2002ocupação")
    cbo.columns = ["cbo", "descricao_ocupacao"]
    subir_bigquery(cbo, TABLE_CBO, modo="replace")
 

def listar_competencias(inicio: str, fim: str) -> list[str]:
    """Gera a lista de competências (AAAAMM) entre inicio e fim, inclusive."""
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
 
    # tabela mensal (leve), sempre gerada, é a base do histórico pro ML
    df_mensal = enriquecer_com_dims(agregar_mensal(caminho_txt))
    subir_bigquery(df_mensal, TABLE_MENSAL, modo="append")
 
    # tabela por pessoa (detalhada), só a partir de PESSOA_INICIO,

    if competencia >= PESSOA_INICIO:
        df_pessoa = enriquecer_com_dims(tratar_microdado(caminho_txt))
        subir_bigquery(df_pessoa, TABLE_PESSOA, modo="append")
    else:
        print(f"[info] {competencia} < {PESSOA_INICIO}: pulando movimentacao_pessoa (só tabela mensal)")
 
    if not manter_arquivos:
        caminho_7z.unlink(missing_ok=True)
        caminho_txt.unlink(missing_ok=True)
        print(f"Arquivos brutos de {competencia} removidos do disco local.")
 
    print(f"=== Competência {competencia} concluída ===\n")
 
 
def rodar_intervalo(inicio: str, fim: str, manter_arquivos: bool = False):
    """
    Processa um intervalo de competências, uma de cada vez, apagando
    o bruto de cada mês após subir pro BigQuery (evita lotar o disco
    ao processar vários meses de uma vez, ex: 202401 até 202605).
    """
    competencias = listar_competencias(inicio, fim)
    print(f"Processando {len(competencias)} competências: {competencias[0]} a {competencias[-1]}")
 
    falhas = []
    for comp in competencias:
        try:
            rodar(comp, manter_arquivos=manter_arquivos)
        except RuntimeError as e:
            print(f"[AVISO] Falha em {comp}, pulando: {e}")
            falhas.append(comp)
 
    print("=== Intervalo concluído ===")
    if falhas:
        print(f"Meses que falharam (revisar manualmente): {falhas}")
 
 
if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 2:
        rodar_intervalo(args[0], args[1])
    elif len(args) == 1:
        rodar(args[0])
    else:
        rodar()
