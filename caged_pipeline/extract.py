"""Baixa e extrai os arquivos mensais do Novo Caged."""

import subprocess
from datetime import date
from pathlib import Path

from config import DOWNLOAD_DIR, FTP_BASE


def competencia_mais_recente() -> str:
    """Chuta o mês mais recente que provavelmente já foi publicado.

    O Caged divulga com uma defasagem de ~1 mês, então usamos o mês
    anterior ao atual como estimativa. Não é garantido - se o mês ainda
    não saiu, baixar_7z() simplesmente falha e quem chamou decide o que fazer.
    """
    hoje = date.today()
    mes = hoje.month - 1 or 12
    ano = hoje.year if hoje.month > 1 else hoje.year - 1
    return f"{ano}{mes:02d}"


def baixar_7z(competencia: str) -> Path:
    ano = competencia[:4]
    nome_arquivo = f"CAGEDMOV{competencia}.7z"
    url = f"{FTP_BASE}/{ano}/{competencia}/{nome_arquivo}"
    destino = DOWNLOAD_DIR / nome_arquivo

    print(f"Baixando {url} ...")
    resultado = subprocess.run(
        ["curl", "-f", "-o", str(destino), url],
        capture_output=True, text=True,
    )
    if resultado.returncode != 0:
        raise RuntimeError(
            f"Falha ao baixar {competencia}. Verifique se o mês já foi publicado.\n{resultado.stderr}"
        )

    print(f"Baixado: {destino} ({destino.stat().st_size / 1e6:.1f} MB)")
    return destino


def extrair_7z(caminho_7z: Path) -> Path:
    print(f"Extraindo {caminho_7z.name} ...")
    resultado = subprocess.run(
        ["7z", "x", "-y", f"-o{DOWNLOAD_DIR}", str(caminho_7z)],
        capture_output=True, text=True,
    )
    if resultado.returncode != 0:
        raise RuntimeError(
            f"Falha ao extrair {caminho_7z.name}. Tem o p7zip instalado? (brew install p7zip)\n{resultado.stderr}"
        )

    txt_esperado = DOWNLOAD_DIR / caminho_7z.name.replace(".7z", ".txt")
    if not txt_esperado.exists():
        # o nome interno do arquivo varia de mês pra mês às vezes
        candidatos = list(DOWNLOAD_DIR.glob("CAGEDMOV*.txt"))
        if not candidatos:
            raise FileNotFoundError("extração terminou mas não achei nenhum .txt")
        txt_esperado = candidatos[0]

    print(f"Extraído: {txt_esperado}")
    return txt_esperado
