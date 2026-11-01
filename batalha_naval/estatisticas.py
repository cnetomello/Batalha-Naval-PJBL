from datetime import datetime

from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator

# Paleta igual à da interface (interface.COR). Duplicada aqui de propósito:
# importar a interface criaria um import circular quando ela usar este módulo.
COR = {
    "fundo": "#0b2540", "painel": "#123a5e", "texto": "#e8f1f8",
    "vitoria": "#4caf7a", "derrota": "#d64545", "destaque": "#2d8fd5",
    "grade": "#2a4d73",
}
TAMANHO_FIGURA = (5.0, 3.5)
MAX_JOGADORES_RANKING = 8


# ---------------------------------------------------------------------------
# Limpeza dos dados
# ---------------------------------------------------------------------------

def _inteiro_nao_negativo(valor):
    try:
        return max(0, int(valor))
    except (TypeError, ValueError):
        return 0


def normalizar_historico(historico):
    if not isinstance(historico, (list, tuple)):
        return []
    limpos = []
    for reg in historico:
        if not isinstance(reg, dict):
            continue
        tiros = _inteiro_nao_negativo(reg.get("tiros"))
        acertos = min(_inteiro_nao_negativo(reg.get("acertos")), tiros)
        jogador = str(reg.get("jogador") or "").strip() or "Jogador"
        limpos.append({
            "data_hora": str(reg.get("data_hora") or ""),
            "jogador": jogador,
            "venceu": bool(reg.get("venceu")),
            "tiros": tiros,
            "acertos": acertos,
            "tiros_inimigo": _inteiro_nao_negativo(reg.get("tiros_inimigo")),
            "duracao_s": _inteiro_nao_negativo(reg.get("duracao_s")),
        })
    return limpos


def filtrar_por_jogador(historico, jogador):
    alvo = jogador.strip().lower()
    return [r for r in normalizar_historico(historico) if r["jogador"].lower() == alvo]


# ---------------------------------------------------------------------------
# Funções de estatística (T43)
# ---------------------------------------------------------------------------

def total_partidas(historico):
    return len(normalizar_historico(historico))


def vitorias_derrotas(historico):
    regs = normalizar_historico(historico)
    vitorias = sum(1 for r in regs if r["venceu"])
    return vitorias, len(regs) - vitorias


def taxa_vitoria(historico):
    vitorias, derrotas = vitorias_derrotas(historico)
    total = vitorias + derrotas
    return 100 * vitorias / total if total else 0.0


def precisao(registro):
    if registro["tiros"] <= 0:
        return None
    return 100 * registro["acertos"] / registro["tiros"]


def precisao_media(historico):
    valores = [p for p in map(precisao, normalizar_historico(historico)) if p is not None]
    return sum(valores) / len(valores) if valores else 0.0


def melhor_partida(historico):
    vitorias = [r for r in normalizar_historico(historico) if r["venceu"] and r["tiros"] > 0]
    if not vitorias:
        return None
    return min(vitorias, key=lambda r: (r["tiros"], -precisao(r)))


def ranking_por_jogador(historico):
    por_jogador = {}
    for reg in normalizar_historico(historico):
        por_jogador.setdefault(reg["jogador"].lower(), []).append(reg)

    ranking = []
    for regs in por_jogador.values():
        vitorias = sum(1 for r in regs if r["venceu"])
        precisoes = [p for p in map(precisao, regs) if p is not None]
        ranking.append({
            "jogador": regs[0]["jogador"],  # grafia do primeiro registro
            "partidas": len(regs),
            "vitorias": vitorias,
            "derrotas": len(regs) - vitorias,
            "taxa_vitoria": 100 * vitorias / len(regs),
            "precisao_media": sum(precisoes) / len(precisoes) if precisoes else 0.0,
        })
    ranking.sort(key=lambda j: (-j["vitorias"], -j["taxa_vitoria"], -j["precisao_media"]))
    return ranking


def resumo(historico):
    vitorias, derrotas = vitorias_derrotas(historico)
    return {
        "partidas": vitorias + derrotas,
        "vitorias": vitorias,
        "derrotas": derrotas,
        "taxa_vitoria": taxa_vitoria(historico),
        "precisao_media": precisao_media(historico),
        "melhor_partida": melhor_partida(historico),
    }


# ---------------------------------------------------------------------------
# Formatação para exibição
# ---------------------------------------------------------------------------

def formatar_duracao(segundos):
    segundos = _inteiro_nao_negativo(segundos)
    horas, resto = divmod(segundos, 3600)
    minutos, seg = divmod(resto, 60)
    if horas:
        return f"{horas}:{minutos:02d}:{seg:02d}"
    return f"{minutos}:{seg:02d}"


def formatar_data(data_hora):
    try:
        return datetime.fromisoformat(data_hora).strftime("%d/%m/%Y %H:%M")
    except (TypeError, ValueError):
        return str(data_hora or "—")


# ---------------------------------------------------------------------------
# Gráficos (T44 a T47)
# ---------------------------------------------------------------------------

def _nova_figura():
    fig = Figure(figsize=TAMANHO_FIGURA, dpi=100, facecolor=COR["fundo"])
    return fig


