
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from matplotlib.lines import Line2D


# Cores dos gráficos
COR = {
    "fundo": "#0b2540",
    "painel": "#123a5e",
    "texto": "#e8f1f8",
    "grade": "#31516d",
    "vitoria": "#4caf7a",
    "derrota": "#d64545",
    "destaque": "#2d8fd5",
}

MAX_JOGADORES_RANKING = 10


def _nova_figura():
    fig = plt.figure(figsize=(7, 4.5), facecolor=COR["fundo"])
    return fig


def _estilizar_eixo(ax, titulo):
    ax.set_facecolor(COR["painel"])
    ax.set_title(
        titulo,
        color=COR["texto"],
        fontsize=13,
        fontweight="bold",
        pad=12
    )
    ax.tick_params(colors=COR["texto"])

    for lado in ax.spines.values():
        lado.set_color(COR["grade"])


def normalizar_historico(historico):
    """Garante que o histórico seja uma lista de resultados válidos."""
    if not isinstance(historico, list):
        return []

    return [
        partida for partida in historico
        if isinstance(partida, dict)
    ]


def vitorias_derrotas(historico):
    partidas = normalizar_historico(historico)

    vitorias = sum(1 for p in partidas if p.get("venceu") is True)
    derrotas = sum(1 for p in partidas if p.get("venceu") is False)

    return vitorias, derrotas


def taxa_vitoria(historico):
    vitorias, derrotas = vitorias_derrotas(historico)
    total = vitorias + derrotas

    if total == 0:
        return 0

    return (vitorias / total) * 100


def precisao(partida):
    tiros = partida.get("tiros", 0)
    acertos = partida.get("acertos", 0)

    if tiros <= 0:
        return None

    return (acertos / tiros) * 100


def ranking_por_jogador(historico):
    """
    Agrupa partidas pelo nome do jogador.
    Enquanto o jogo não registrar nomes, utiliza 'Jogador'.
    """
    partidas = normalizar_historico(historico)
    jogadores = {}

    for partida in partidas:
        nome = partida.get("jogador", "Jogador")

        if nome not in jogadores:
            jogadores[nome] = {
                "jogador": nome,
                "vitorias": 0,
                "derrotas": 0,
                "partidas": 0
            }

        jogador = jogadores[nome]
        jogador["partidas"] += 1

        if partida.get("venceu") is True:
            jogador["vitorias"] += 1
        elif partida.get("venceu") is False:
            jogador["derrotas"] += 1

    ranking = []

    for jogador in jogadores.values():
        total = jogador["vitorias"] + jogador["derrotas"]

        jogador["taxa_vitoria"] = (
            jogador["vitorias"] / total * 100
            if total > 0 else 0
        )

        ranking.append(jogador)

    return sorted(
        ranking,
        key=lambda j: (j["vitorias"], j["taxa_vitoria"]),
        reverse=True
    )


def _figura_vazia(titulo, mensagem="Nenhuma partida registrada ainda.\nJogue uma partida para ver o gráfico."):
    fig = _nova_figura()
    ax = fig.add_subplot(111)

    _estilizar_eixo(ax, titulo)
    ax.set_xticks([])
    ax.set_yticks([])

    ax.text(
        0.5, 0.5, mensagem,
        ha="center",
        va="center",
        color=COR["texto"],
        fontsize=12,
        transform=ax.transAxes
    )

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
    ax.set_title(
        titulo,
        color=COR["texto"],
        fontsize=13,
        fontweight="bold",
        pad=12
    )

    valores = []
    cores = []
    nomes = []

    if vitorias > 0:
        valores.append(vitorias)
        cores.append(COR["vitoria"])
        nomes.append("Vitórias")

    if derrotas > 0:
        valores.append(derrotas)
        cores.append(COR["derrota"])
        nomes.append("Derrotas")

    ax.pie(
        valores,
        colors=cores,
        startangle=90,
        counterclock=False,
        wedgeprops={
            "width": 0.38,
            "edgecolor": COR["fundo"],
            "linewidth": 2
        },
        autopct=lambda p: f"{round(p * sum(valores) / 100)}",
        pctdistance=0.81,
        textprops={
            "color": "white",
            "fontsize": 12,
            "fontweight": "bold"
        }
    )

    ax.text(
        0, 0.06,
        f"{taxa_vitoria(historico):.0f}%",
        ha="center",
        va="center",
        color=COR["texto"],
        fontsize=24,
        fontweight="bold"
    )

    ax.text(
        0, -0.2,
        "de vitórias",
        ha="center",
        va="center",
        color=COR["texto"],
        fontsize=10
    )

    ax.legend(
        nomes,
        loc="lower center",
        ncol=2,
        frameon=False,
        labelcolor=COR["texto"],
        bbox_to_anchor=(0.5, -0.08)
    )

    ax.set_aspect("equal")
    fig.tight_layout()

    return fig


def grafico_precisao_por_partida(historico):
    titulo = "Precisão por partida"

    pontos = [
        (partida, precisao(partida))
        for partida in normalizar_historico(historico)
    ]

    pontos = [
        (partida, valor)
        for partida, valor in pontos
        if valor is not None
    ]

    if not pontos:
        return _figura_vazia(titulo)

    numeros = list(range(1, len(pontos) + 1))
    valores = [valor for _, valor in pontos]

    cores = [
        COR["vitoria"] if partida.get("venceu") else COR["derrota"]
        for partida, _ in pontos
    ]

    media = sum(valores) / len(valores)

    fig = _nova_figura()
    ax = fig.add_subplot(111)

    _estilizar_eixo(ax, titulo)

    ax.plot(
        numeros, valores,
        color=COR["destaque"],
        linewidth=2,
        zorder=2
    )

    ax.scatter(
        numeros, valores,
        c=cores,
        s=70,
        zorder=3,
        edgecolors=COR["fundo"],
        linewidths=1.5
    )

    ax.axhline(
        media,
        color=COR["texto"],
        linestyle="--",
        linewidth=1,
        alpha=0.7,
        zorder=1
    )

    ax.text(
        0.99, media,
        f" média {media:.0f}%",
        transform=ax.get_yaxis_transform(),
        ha="right",
        va="bottom",
        color=COR["texto"],
        fontsize=9
    )

    ax.set_ylim(0, 105)
    ax.set_xlim(0.5, len(pontos) + 0.5)

    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    ax.set_xlabel("Partida", color=COR["texto"])
    ax.set_ylabel("Acertos / tiros (%)", color=COR["texto"])

    ax.grid(color=COR["grade"], alpha=0.6)
    ax.set_axisbelow(True)

    ax.legend(
        handles=[
            Line2D(
                [], [],
                marker="o",
                linestyle="",
                color=COR["vitoria"],
                label="Vitória"
            ),
            Line2D(
                [], [],
                marker="o",
                linestyle="",
                color=COR["derrota"],
                label="Derrota"
            )
        ],
        loc="lower left",
        frameon=False,
        labelcolor=COR["texto"]
    )

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

    ax.barh(
        nomes,
        vitorias,
        color=COR["vitoria"],
        label="Vitórias",
        height=0.6
    )

    ax.barh(
        nomes,
        derrotas,
        left=vitorias,
        color=COR["derrota"],
        label="Derrotas",
        height=0.6
    )

    for i, jogador in enumerate(ranking):
        ax.text(
            jogador["partidas"] + 0.1,
            i,
            f'{jogador["taxa_vitoria"]:.0f}%',
            va="center",
            color=COR["texto"],
            fontsize=10,
            fontweight="bold"
        )

    maximo = max(j["partidas"] for j in ranking)

    ax.set_xlim(0, maximo * 1.2 + 0.5)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    ax.set_xlabel(
        "Partidas (percentual = taxa de vitória)",
        color=COR["texto"]
    )

    ax.grid(axis="x", color=COR["grade"], alpha=0.6)
    ax.set_axisbelow(True)

    ax.legend(
        loc="lower right",
        frameon=False,
        labelcolor=COR["texto"]
    )

    fig.tight_layout()
    return fig


# Nome do botão na tela -> função que gera o gráfico
GRAFICOS = {
    "Vitórias x Derrotas": grafico_vitorias_derrotas,
    "Precisão por partida": grafico_precisao_por_partida,
    "Ranking de jogadores": grafico_ranking_jogadores,
}
