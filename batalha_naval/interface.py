import tkinter as tk
from tkinter import messagebox

from batalha_naval import modelo as m

TAM_CELULA = 36
MARGEM = 28
COR = {
    "fundo": "#0b2540", "texto": "#e8f1f8", "agua": "#1f6fa8", "grade": "#0b2540",
    "navio": "#8a97a3", "acerto": "#d64545", "erro": "#e8f1f8",
    "ok": "#4caf7a", "invalido": "#e08a3c", "botao": "#2d8fd5",
}
FONTE = ("Helvetica", 11)
FONTE_TITULO = ("Helvetica", 22, "bold")


def botao(master, texto, comando, largura=18):
    return tk.Button(master, text=texto, command=comando, width=largura,
                     font=FONTE, bg=COR["botao"], fg="white", relief="flat", pady=6)


def rotulo(master, texto, fonte=FONTE, **kw):
    return tk.Label(master, text=texto, font=fonte, bg=COR["fundo"], fg=COR["texto"], **kw)


class TabuleiroCanvas(tk.Canvas):

    def __init__(self, master, tabuleiro, mostrar_navios=True, ao_clicar=None, ao_passar=None):
        lado = MARGEM + m.TAMANHO * TAM_CELULA + 2
        super().__init__(master, width=lado, height=lado, bg=COR["fundo"], highlightthickness=0)
        self.tabuleiro = tabuleiro
        self.mostrar_navios = mostrar_navios
        self.ao_clicar, self.ao_passar = ao_clicar, ao_passar
        self.preview, self.preview_ok = [], True
        self.bind("<Button-1>", self._clique)
        self.bind("<Motion>", self._movimento)
        self.bind("<Leave>", lambda e: self._avisar_passagem(None))
        self.desenhar()

    def _celula(self, evento):
        l = (evento.y - MARGEM) // TAM_CELULA
        c = (evento.x - MARGEM) // TAM_CELULA
        if 0 <= l < m.TAMANHO and 0 <= c < m.TAMANHO:
            return l, c
        return None

    def _clique(self, evento):
        cel = self._celula(evento)
        if cel and self.ao_clicar:
            self.ao_clicar(cel)

    def _movimento(self, evento):
        self._avisar_passagem(self._celula(evento))

    def _avisar_passagem(self, cel):
        if self.ao_passar:
            self.ao_passar(cel)

    def definir_preview(self, celulas, ok):
        self.preview, self.preview_ok = celulas, ok
        self.desenhar()

    def desenhar(self):
        self.delete("all")
        for i in range(m.TAMANHO):
            centro = MARGEM + i * TAM_CELULA + TAM_CELULA // 2
            self.create_text(centro, MARGEM // 2, text=chr(65 + i), fill=COR["texto"], font=FONTE)
            self.create_text(MARGEM // 2, centro, text=str(i + 1), fill=COR["texto"], font=FONTE)
        for l in range(m.TAMANHO):
            for c in range(m.TAMANHO):
                x0, y0 = MARGEM + c * TAM_CELULA, MARGEM + l * TAM_CELULA
                x1, y1 = x0 + TAM_CELULA, y0 + TAM_CELULA
                estado = self.tabuleiro.grade[l][c]
                cor = COR["agua"]
                if estado == m.NAVIO and self.mostrar_navios:
                    cor = COR["navio"]
                elif estado == m.ACERTO:
                    cor = COR["acerto"]
                if (l, c) in self.preview:
                    cor = COR["ok"] if self.preview_ok else COR["invalido"]
                self.create_rectangle(x0, y0, x1, y1, fill=cor, outline=COR["grade"], width=2)
                if estado == m.ERRO:
                    self.create_oval(x0 + 13, y0 + 13, x1 - 13, y1 - 13, fill=COR["erro"], outline="")
                elif estado == m.ACERTO:
                    self.create_line(x0 + 9, y0 + 9, x1 - 9, y1 - 9, fill="white", width=3)
                    self.create_line(x0 + 9, y1 - 9, x1 - 9, y0 + 9, fill="white", width=3)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Batalha Naval")
        self.configure(bg=COR["fundo"])
        self.resizable(False, False)
        self.tela = None
        self.mostrar(TelaMenu)

    def mostrar(self, classe, **kwargs):
        if self.tela is not None:
            self.tela.destroy()
        self.tela = classe(self, **kwargs)
        self.tela.pack(padx=24, pady=24)

    def ao_terminar_partida(self, resultado):
        """Chamado ao fim de cada partida com um dict:
        {"venceu": bool, "tiros": int, "acertos": int, "tiros_inimigo": int}
        TODO (Participante 3): salvar com a camada de persistência."""
        print("Partida finalizada:", resultado)


class TelaMenu(tk.Frame):
    def __init__(self, app):
        super().__init__(app, bg=COR["fundo"])
        self.app = app
        rotulo(self, "⚓ BATALHA NAVAL", FONTE_TITULO).pack(pady=(10, 30))
        botao(self, "Novo jogo", lambda: app.mostrar(TelaPosicionamento)).pack(pady=6)
        #botao(self, "Estatísticas", lambda: app.mostrar(TelaEstatisticas)).pack(pady=6)
        botao(self, "Sair", app.destroy).pack(pady=6)


class TelaPosicionamento(tk.Frame):
    def __init__(self, app):
        super().__init__(app, bg=COR["fundo"])
        self.app = app
        self.tab = m.Tabuleiro()
        self.indice, self.horizontal, self.ultima = 0, True, None

        rotulo(self, "Posicione seus navios", ("Helvetica", 16, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 12))
        self.canvas = TabuleiroCanvas(self, self.tab, True, self.colocar, self.passar)
        self.canvas.grid(row=1, column=0)
        self.canvas.bind("<Button-3>", self.girar)  # botão direito (Windows/Linux)
        self.canvas.bind("<Button-2>", self.girar)  # botão direito (macOS)

        painel = tk.Frame(self, bg=COR["fundo"])
        painel.grid(row=1, column=1, padx=24, sticky="n")
        self.info = rotulo(painel, "", justify="left")
        self.info.pack(pady=(0, 16))
        botao(painel, "Girar (botão direito)", self.girar).pack(pady=4)
        botao(painel, "Posicionar aleatório", self.aleatorio).pack(pady=4)
        botao(painel, "Limpar", self.limpar).pack(pady=4)
        self.btn_iniciar = botao(painel, "Iniciar batalha ▶", self.iniciar)
        self.btn_iniciar.pack(pady=(20, 4))
        botao(painel, "Voltar ao menu", lambda: app.mostrar(TelaMenu)).pack(pady=4)
        self.atualizar_info()

    def passar(self, cel):
        self.ultima = cel
        if cel is None or self.indice >= len(m.NAVIOS):
            self.canvas.definir_preview([], True)
            return
        tam = m.NAVIOS[self.indice][1]
        celulas = self.tab.celulas_navio(*cel, tam, self.horizontal)
        self.canvas.definir_preview(celulas, self.tab.pode_posicionar(celulas))

    def colocar(self, cel):
        if self.indice >= len(m.NAVIOS):
            return
        nome, tam = m.NAVIOS[self.indice]
        if self.tab.posicionar(nome, self.tab.celulas_navio(*cel, tam, self.horizontal)):
            self.indice += 1
            self.passar(cel)
            self.atualizar_info()

    def girar(self, _evento=None):
        self.horizontal = not self.horizontal
        self.passar(self.ultima)
        self.atualizar_info()

    def aleatorio(self):
        self.tab.posicionar_aleatorio()
        self.indice = len(m.NAVIOS)
        self.canvas.definir_preview([], True)
        self.atualizar_info()

    def limpar(self):
        self.tab.limpar()
        self.indice = 0
        self.canvas.definir_preview([], True)
        self.atualizar_info()

    def atualizar_info(self):
        if self.indice < len(m.NAVIOS):
            nome, tam = m.NAVIOS[self.indice]
            orient = "horizontal" if self.horizontal else "vertical"
            self.info.config(text=f"Posicionando:\n{nome} ({tam} células)\nOrientação: {orient}")
            self.btn_iniciar.config(state="disabled")
        else:
            self.info.config(text="Frota pronta!\nClique em Iniciar batalha.")
            self.btn_iniciar.config(state="normal")

    def iniciar(self):
        self.app.mostrar(TelaBatalha, tab_jogador=self.tab)


class TelaBatalha(tk.Frame):
    def __init__(self, app, tab_jogador):
        super().__init__(app, bg=COR["fundo"])
        self.app = app
        self.jogador = tab_jogador
        self.inimigo = m.Tabuleiro()
        self.inimigo.posicionar_aleatorio()
        self.ia = m.IA()
        self.vez_jogador = True
        self.tiros = self.acertos = self.tiros_ia = 0

        rotulo(self, "Sua frota", ("Helvetica", 13, "bold")).grid(row=0, column=0)
        rotulo(self, "Frota inimiga (clique para atirar)", ("Helvetica", 13, "bold")).grid(row=0, column=1)
        self.canvas_jogador = TabuleiroCanvas(self, self.jogador, True)
        self.canvas_jogador.grid(row=1, column=0, padx=10)
        self.canvas_inimigo = TabuleiroCanvas(self, self.inimigo, False, self.atirar)
        self.canvas_inimigo.grid(row=1, column=1, padx=10)

        self.status = rotulo(self, "Sua vez!", ("Helvetica", 13, "bold"))
        self.status.grid(row=2, column=0, columnspan=2, pady=(12, 4))
        self.log = tk.Listbox(self, height=5, width=80, font=FONTE, bg="#123a5e",
                              fg=COR["texto"], highlightthickness=0)
        self.log.grid(row=3, column=0, columnspan=2)
        botao(self, "Desistir", lambda: app.mostrar(TelaMenu), 12).grid(row=4, column=0, columnspan=2, pady=10)

    def _registrar(self, quem, linha, coluna, resultado, nome):
        coord = f"{chr(65 + coluna)}{linha + 1}"
        textos = {"agua": "água", "acerto": f"acertou o {nome}!", "afundou": f"afundou o {nome}!"}
        self.log.insert(0, f"{quem} → {coord}: {textos[resultado]}")

    def atirar(self, cel):
        if not self.vez_jogador:
            return
        resultado, nome = self.inimigo.atirar(*cel)
        if resultado == "repetido":
            return
        self.tiros += 1
        self.acertos += resultado != "agua"
        self._registrar("Você", *cel, resultado, nome)
        self.canvas_inimigo.desenhar()
        if self.inimigo.todos_afundados():
            return self.fim(True)
        self.vez_jogador = False
        self.status.config(text="Vez do adversário...")
        self.after(700, self.turno_ia)

    def turno_ia(self):
        l, c = self.ia.escolher()
        resultado, nome = self.jogador.atirar(l, c)
        self.ia.registrar(l, c, resultado)
        self.tiros_ia += 1
        self._registrar("Inimigo", l, c, resultado, nome)
        self.canvas_jogador.desenhar()
        if self.jogador.todos_afundados():
            return self.fim(False)
        self.vez_jogador = True
        self.status.config(text="Sua vez!")

    def fim(self, venceu):
        self.vez_jogador = False
        self.app.ao_terminar_partida({"venceu": venceu, "tiros": self.tiros,
                                      "acertos": self.acertos, "tiros_inimigo": self.tiros_ia})
        messagebox.showinfo("Fim de jogo", "Você venceu!" if venceu else "Sua frota foi destruída.")
        self.app.mostrar(TelaMenu)