"""Configurações do projeto CAGED - Movimentação de Empregos na Indústria (Nordeste)."""

from pathlib import Path

# --- BigQuery ---
PROJECT_ID = "caged-pressao-salarial"
DATASET_ID = "caged_pressao_salarial"

TABLE_MENSAL = "movimentacao_mensal"    # série mensal agregada, 2020 até hoje - alimenta o BQML e o gráfico de linha do BI
TABLE_PESSOA = "movimentacao_pessoa"    # 1 linha por evento (admissão/desligamento), a partir de PESSOA_INICIO - drill-down do BI

# a partir de qual competência (AAAAMM) a gente também gera a tabela por
# pessoa. meses mais antigos entram só na mensal, senão o volume explode
# e estoura o storage gratuito do BigQuery
PESSOA_INICIO = "202505"

# --- recorte de dado ---

# só Nordeste por enquanto (códigos IBGE): MA, PI, CE, RN, PB, PE, AL, SE, BA
UF_NORDESTE = [21, 22, 23, 24, 25, 26, 27, 28, 29]

# acima disso o salário praticamente certeza é erro de digitação na
# declaração do CAGED - já encontramos registro de mais de R$1 bilhão
SALARIO_TETO = 100_000

COLUNAS_NECESSARIAS = [
    "competênciamov", "uf", "município", "seção", "cbo2002ocupação",
    "salário", "saldomovimentação",
]

# de-para de seção CNAE -> Grande Grupamento (classificação oficial
# que a Secretaria de Trabalho adotou junto com o IBGE)
SECAO_PARA_GRUPAMENTO = {
    "A": "Agricultura",
    "B": "Indústria Geral",
    "C": "Indústria Geral",
    "D": "Indústria Geral",
    "E": "Indústria Geral",
    "F": "Construção Civil",
    "G": "Comércio",
}
GRANDE_GRUPAMENTO_PADRAO = "Serviços"  # tudo de H a U cai aqui

# --- caminhos locais ---

BASE_DIR = Path(__file__).parent
DOWNLOAD_DIR = BASE_DIR / "dados"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

DIM_CBO_PATH = BASE_DIR / "dim_cbo.csv"
DIM_MUNICIPIO_PATH = BASE_DIR / "dim_municipio.csv"
DIM_UF_PATH = BASE_DIR / "dim_uf.csv"
DIM_SECAO_PATH = BASE_DIR / "dim_secao.csv"

FTP_BASE = "ftp://ftp.mtps.gov.br/pdet/microdados/NOVO%20CAGED"
