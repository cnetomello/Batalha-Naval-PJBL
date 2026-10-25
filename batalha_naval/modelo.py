import random

TAMANHO = 10
NAVIOS = [("Porta-aviões", 5), ("Encouraçado", 4), ("Cruzador", 3),
          ("Submarino", 3), ("Destroyer", 2)]

AGUA, NAVIO, ERRO, ACERTO = 0, 1, 2, 3


class Tabuleiro:
    def __init__(self):
        self.limpar()

    def limpar(self):
        self.grade = [[AGUA] * TAMANHO for _ in range(TAMANHO)]
        self.navios = []  # cada navio: {"nome", "celulas", "atingidas"}

    @staticmethod
    def celulas_navio(linha, coluna, tamanho, horizontal):
        if horizontal:
            return [(linha, coluna + i) for i in range(tamanho)]
        return [(linha + i, coluna) for i in range(tamanho)]

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

#Seguir logica daqui