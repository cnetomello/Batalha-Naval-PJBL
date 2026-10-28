import random

TAMANHO = 10
NAVIOS = [
    ("Porta-aviões", 5),
    ("Encouraçado", 4),
    ("Cruzador", 3),
    ("Submarino", 3),
    ("Destroyer", 2)
    ]

AGUA, NAVIO, ERRO, ACERTO = 0, 1, 2, 3


class Tabuleiro:
    def __init__(self):
        self.limpar()

    def limpar(self):
        self.grade = [
            [AGUA] * TAMANHO
            for i in range(TAMANHO)
        ]
        self.navios = []  # cada navio: {"nome", "celulas", "atingidas"}

    @staticmethod
    def celulas_navio(linha, coluna, tamanho, horizontal):
        if horizontal:
            return [
                (linha, coluna + i)
                for i in range(tamanho)
            ]
        return [
            (linha + i, coluna)
            for i in range(tamanho)
        ]

    def pode_posicionar(self, celulas):
        return all(0 <= l < TAMANHO and 0 <= c < TAMANHO and self.grade[l][c] == AGUA
                   for l, c in celulas)

    def posicionar(self, nome, celulas):
        if not self.pode_posicionar(celulas):
            return False
        for l, c in celulas:
            self.grade[l][c] = NAVIO
        self.navios.append({"nome": nome, "celulas": set(celulas), "atingidas": set()})
        return True

    def posicionar_aleatorio(self):
        self.limpar()
        for nome, tam in NAVIOS:
            while True:
                horiz = random.choice([True, False])
                l, c = random.randrange(TAMANHO), random.randrange(TAMANHO)
                if self.posicionar(nome, self.celulas_navio(l, c, tam, horiz)):
                    break

    def atirar(self, linha, coluna):
        if self.grade[linha][coluna] in (ERRO, ACERTO):
            return "repetido", None
        if self.grade[linha][coluna] == AGUA:
            self.grade[linha][coluna] = ERRO
            return "agua", None
        if self.grade[linha][coluna] == NAVIO:
            self.grade[linha][coluna] = ACERTO
            for n in self.navios:
                if (linha, coluna) in n["celulas"]:
                    n["atingidas"].add((linha, coluna))
                    if n["atingidas"] == n["celulas"]:
                        return "afundou", n["nome"]
                    return "acerto", n["nome"]

    def todos_afundados(self):
        return all(n["atingidas"] == n["celulas"] for n in self.navios)


class IA:

    def __init__(self):
        self.disponiveis = {
            (l, c)
            for l in range(TAMANHO)
            for c in range(TAMANHO)
        }
        self.alvos = []

    def escolher(self):
        while self.alvos:
            alvo = self.alvos.pop()
            if alvo in self.disponiveis:
                break
        else:
            alvo = random.choice(tuple(self.disponiveis))
        self.disponiveis.discard(alvo)
        return alvo

    def registrar(self, linha, coluna, resultado):
        if resultado == "afundou":
            self.alvos.clear()
        elif resultado == "acerto":
            for dl, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                self.alvos.append((linha + dl, coluna + dc))