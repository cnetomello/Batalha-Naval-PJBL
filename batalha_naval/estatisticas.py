from datetime import datetime

from matplotlib.figure import Figure

COR = {
    "fundo": "#0b2540", "painel": "#123a5e", "texto": "#e8f1f8",
    "vitoria": "#4caf7a", "derrota": "#d64545", "destaque": "#2d8fd5",
    "grade": "#2a4d73",
}
TAMANHO_FIGURA = (5.0, 3.5)
MAX_JOGADORES_RANKING = 8

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

def _estilizar_eixo(ax, titulo):
    ax.set_facecolor(COR["painel"])
    ax.set_title(titulo, color=COR["texto"], fontsize=13, fontweight="bold", pad=12)
    ax.tick_params(colors=COR["texto"])
    for lado in ax.spines.values():
        lado.set_color(COR["grade"])


def _figura_vazia(titulo, mensagem="Nenhuma partida registrada ainda.\nJogue uma partida para ver o gráfico."):
    fig = _nova_figura()
    ax = fig.add_subplot(111)
    _estilizar_eixo(ax, titulo)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.text(0.5, 0.5, mensagem, ha="center", va="center",
            color=COR["texto"], fontsize=12, transform=ax.transAxes)
    fig.tight_layout()
    return fig

def grafico_vitorias_derrotas(historico):
    titulo = "Vitórias x Derrotas"
    vitorias, derrotas = vitorias_derrotas(historico)

    if vitorias + derrotas == 0:
        return _figura_vazia(titulo)

    fig = _nova_figura()
    ax = fig.add_subplot(111)
    ax.set_facecolor(COR["fundo"])
    ax.set_title(titulo, color=COR["texto"], fontsize=13, fontweight="bold", pad=12)

    valores = [v for v in (vitorias, derrotas) if v > 0]
    cores = [c for v, c in ((vitorias, COR["vitoria"]), (derrotas, COR["derrota"])) if v > 0]
    nomes = [n for v, n in ((vitorias, "Vitórias"), (derrotas, "Derrotas")) if v > 0]

    ax.pie(
        valores, colors=cores, startangle=90, counterclock=False,
        wedgeprops={"width": 0.38, "edgecolor": COR["fundo"], "linewidth": 2},
        autopct=lambda p: f"{round(p * sum(valores) / 100)}",
        pctdistance=0.81,
        textprops={"color": "white", "fontsize": 12, "fontweight": "bold"}
    )

    ax.text(0, 0.06, f"{taxa_vitoria(historico):.0f}%",
            ha="center", va="center", color=COR["texto"], fontsize=24, fontweight="bold")
    ax.text(0, -0.2, "de vitórias", ha="center", va="center",
            color=COR["texto"], fontsize=10)
    ax.legend(nomes, loc="lower center", ncol=2, frameon=False,
              labelcolor=COR["texto"], bbox_to_anchor=(0.5, -0.08))
    ax.set_aspect("equal")
    fig.tight_layout()
    return fig


def grafico_precisao_por_partida(historico):
    titulo = "Precisão por partida"
    pontos = [(r, precisao(r)) for r in normalizar_historico(historico)]
    pontos = [(r, p) for r, p in pontos if p is not None]

    if not pontos:
        return _figura_vazia(titulo)

    numeros = list(range(1, len(pontos) + 1))
    valores = [p for _, p in pontos]
    cores = [COR["vitoria"] if r["venceu"] else COR["derrota"] for r, _ in pontos]
    media = sum(valores) / len(valores)

    fig = _nova_figura()
    ax = fig.add_subplot(111)
    _estilizar_eixo(ax, titulo)
    ax.plot(numeros, valores, color=COR["destaque"], linewidth=2, zorder=2)
    ax.scatter(numeros, valores, c=cores, s=70, zorder=3,
               edgecolors=COR["fundo"], linewidths=1.5)
    ax.axhline(media, color=COR["texto"], linestyle="--", linewidth=1, alpha=0.7, zorder=1)
    ax.text(0.99, media, f" média {media:.0f}%",
            transform=ax.get_yaxis_transform(), ha="right", va="bottom",
            color=COR["texto"], fontsize=9)

    ax.set_ylim(0, 105)
    ax.set_xlim(0.5, len(pontos) + 0.5)
    ax.set_xlabel("Partida", color=COR["texto"])
    ax.set_ylabel("Acertos / tiros (%)", color=COR["texto"])
    ax.grid(color=COR["grade"], alpha=0.6)
    ax.set_axisbelow(True)

    ax.legend(handles=[
    ], loc="lower left", frameon=False, labelcolor=COR["texto"])

    fig.tight_layout()
    return fig


def grafico_ranking_jogadores(historico):
    titulo = "Ranking de jogadores"
    ranking = ranking_por_jogador(historico)[:MAX_JOGADORES_RANKING]

    if not ranking:
        return _figura_vazia(titulo)

    ranking = ranking[::-1]
    nomes = [j["jogador"] for j in ranking]
    vitorias = [j["vitorias"] for j in ranking]
    derrotas = [j["derrotas"] for j in ranking]

    fig = _nova_figura()
    ax = fig.add_subplot(111)
    _estilizar_eixo(ax, titulo)
    ax.barh(nomes, vitorias, color=COR["vitoria"], label="Vitórias", height=0.6)
    ax.barh(nomes, derrotas, left=vitorias, color=COR["derrota"],
            label="Derrotas", height=0.6)

    for i, j in enumerate(ranking):
        ax.text(j["partidas"] + 0.1, i, f"{j['taxa_vitoria']:.0f}%",
                va="center", color=COR["texto"], fontsize=10, fontweight="bold")

    maximo = max(j["partidas"] for j in ranking)
    ax.set_xlim(0, maximo * 1.2 + 0.5)
    ax.set_xlabel("Partidas (percentual = taxa de vitória)", color=COR["texto"])
    ax.grid(axis="x", color=COR["grade"], alpha=0.6)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", frameon=False, labelcolor=COR["texto"])

    fig.tight_layout()
    return fig


GRAFICOS = {
    "Vitórias x Derrotas": grafico_vitorias_derrotas
}
