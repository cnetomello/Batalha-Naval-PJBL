import json
import os
from pathlib import Path

PASTA_DADOS = Path(__file__).resolve().parent.parent / "dados"
ARQUIVO_HISTORICO = PASTA_DADOS / "historico.json"


def carregar_historico():
    try:
        with open(ARQUIVO_HISTORICO, encoding="utf-8") as f:
            dados = json.load(f)
    except FileNotFoundError:
        return []
    except (OSError, ValueError):
        return []
    return dados if isinstance(dados, list) else []


def salvar_partida(registro):
    historico = carregar_historico()
    historico.append(registro)
    temporario = ARQUIVO_HISTORICO.with_suffix(".tmp")
    try:
        PASTA_DADOS.mkdir(parents=True, exist_ok=True)
        with open(temporario, "w", encoding="utf-8") as f:
            json.dump(historico, f, ensure_ascii=False, indent=2)
        os.replace(temporario, ARQUIVO_HISTORICO)
    except (OSError, TypeError, ValueError):
        return False
    return True