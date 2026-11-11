from pathlib import Path
import time
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from batalha_naval import estatisticas as est
from batalha_naval import modelo as m
from batalha_naval import persistencia
TAM_CELULA = 36
MARGEM = 28
COR = {
    "fundo": "#0b2540", "texto": "#e8f1f8", "agua": "#1f6fa8", "grade": "#0b2540",
    "navio": "#8a97a3", "acerto": "#d64545", "erro": "#e8f1f8",
    "ok": "#4caf7a", "invalido": "#e08a3c", "botao": "#2d8fd5",
    "painel": "#123a5e", "botao_ativo": "#1b5e8f", "derrota": "#f07a7a",
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


def mostrar_regras():
    messagebox.showinfo(
        "Regras - Batalha Naval",
        "OBJETIVO:\n"
        "Afundar todos os barcos adversários!\n\n"
        "BARCOS:\n"
        "- Porta-aviões: 5 casas\n"
        "- Encouraçado: 4 casas\n"
        "- Cruzador: 3 casas\n"
        "- Submarino: 3 casas\n"
        "- Destroyer: 2 casas\n\n"
        "REGRAS:\n"
        "1. O tabuleiro possui 10x10 casas.\n"
        "2. Posicione os barcos na horizontal ou vertical.\n"
        "3. Clique nas casas do adversário para atirar.\n"
        "4. Acertar um barco conta como acerto.\n"
        "5. Acertar a água conta como erro.\n"
        "6. Não é possível repetir disparos.\n"
        "7. Vence quem afundar todos os barcos inimigos."
    )


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Batalha Naval")
        self.configure(bg=COR["fundo"])
        self.resizable(False, False)
        self.tela = None
        self.jogador = ""  # definido na tela de menu antes de cada partida
        self.mostrar(TelaMenu)

    def mostrar(self, classe, **kwargs):
        if self.tela is not None:
            self.tela.destroy()
        self.tela = classe(self, **kwargs)
        self.tela.pack(padx=24, pady=24)

    def ao_terminar_partida(self, resultado):
        registro = {
            "data_hora": datetime.now().isoformat(timespec="seconds"),
            "jogador": self.jogador or "Jogador",
            **resultado,
        }
        if not persistencia.salvar_partida(registro):
            messagebox.showwarning(
                "Histórico",
                "Não foi possível salvar esta partida no histórico.\n"
                "Verifique se a pasta do jogo permite gravação.")
        return registro


class TelaMenu(tk.Frame):
    MAX_NOME = 16

    def __init__(self, app):
        super().__init__(app, bg=COR["fundo"])
        self.app = app
        rotulo(self, "⚓ BATALHA NAVAL", FONTE_TITULO).pack(pady=(10, 24))
        rotulo(self, "Seu nome:").pack()
        self.nome = tk.StringVar(value=app.jogador)
        entrada = tk.Entry(self, textvariable=self.nome, font=FONTE, width=20,
                           justify="center", relief="flat")
        entrada.pack(pady=(4, 18), ipady=4)
        entrada.bind("<Return>", lambda _e: self.novo_jogo())
        botao(self, "Novo jogo", self.novo_jogo).pack(pady=6)
        botao(self, "Retomar partida", self.retomar_jogo).pack(pady=6)
        botao(self, "Estatísticas", lambda: app.mostrar(TelaEstatisticas)).pack(pady=6)
        botao(self, "Regras", mostrar_regras).pack(pady=6)
        botao(self, "Sair", app.destroy).pack(pady=6)

    def novo_jogo(self):
        nome = " ".join(self.nome.get().split())  # tira espaços extras
        if not nome:
            messagebox.showwarning("Nome obrigatório", "Digite seu nome para começar.")
            return
        if len(nome) > self.MAX_NOME:
            messagebox.showwarning(
                "Nome muito longo", f"Use no máximo {self.MAX_NOME} caracteres.")
            return
        if persistencia.carregar_estado_jogo() is not None:
            confirmar = messagebox.askyesno(
                "Partida salva",
                "Existe uma partida salva. Iniciar um novo jogo irá descartá-la. Deseja continuar?"
            )
            if not confirmar:
                return
            persistencia.excluir_estado_jogo()
        self.app.jogador = nome
        self.app.mostrar(TelaPosicionamento)

    def retomar_jogo(self):
        estado = persistencia.carregar_estado_jogo()
        if estado is None:
            messagebox.showwarning(
                "Erro ao carregar partida",
                "Nenhuma partida salva encontrada."
            )
            return
        self.app.jogador = estado.get("jogador") or self.app.jogador
        self.app.mostrar(
            TelaBatalha,
            estado=estado
        )


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
    def __init__(self, app, tab_jogador=None, estado=None):
        super().__init__(app, bg=COR["fundo"])
        self.app = app
        self.after_ia_id = None
        self.after_msg_id = None

        if estado is not None:
            # Restaurar partida salva
            self.jogador = m.Tabuleiro()
            self.jogador.carregar_dict(estado["tabuleiro_jogador"])
            self.inimigo = m.Tabuleiro()
            self.inimigo.carregar_dict(estado["tabuleiro_inimigo"])
            self.ia = m.IA()
            self.ia.carregar_dict(estado["estado_ia"])
            self.tiros = estado["estatisticas"]["tiros"]
            self.acertos = estado["estatisticas"]["acertos"]
            self.tiros_ia = estado["estatisticas"]["tiros_ia"]
            self.vez_jogador = estado["vez_jogador"]
            duracao = estado["duracao_s"]
            self.inicio = time.monotonic() - duracao
            self.historico_log = estado.get("log", [])
        else:
            # Iniciar nova partida
            self.jogador = tab_jogador
            self.inimigo = m.Tabuleiro()
            self.inimigo.posicionar_aleatorio()
            self.ia = m.IA()
            self.vez_jogador = True
            self.tiros = 0
            self.acertos = 0
            self.tiros_ia = 0
            self.inicio = time.monotonic()
            self.historico_log = []

        # Se a partida restaurada já está no último navio, não repete o aviso
        self.aviso_ultimo_navio = self.inimigo.navios_restantes() <= 1
        self.aviso_ultimo_navio_jogador = self.jogador.navios_restantes() <= 1

        # --- Placar no topo: VOCÊ  4 × 5  INIMIGO ---
        self.placar = tk.Frame(self, bg=COR["fundo"])
        self.placar.grid(row=0, column=0, columnspan=2, pady=(0, 14))
        rotulo(self.placar, "VOCÊ", ("Helvetica", 14, "bold")).grid(row=0, column=0, padx=18)
        self.num_voce = rotulo(self.placar, "", ("Helvetica", 34, "bold"))
        self.num_voce.grid(row=0, column=1)
        rotulo(self.placar, "×", ("Helvetica", 26, "bold")).grid(row=0, column=2, padx=14)
        self.num_inimigo = rotulo(self.placar, "", ("Helvetica", 34, "bold"))
        self.num_inimigo.grid(row=0, column=3)
        rotulo(self.placar, "INIMIGO", ("Helvetica", 14, "bold")).grid(row=0, column=4, padx=18)

        rotulo(self, "Sua frota", ("Helvetica", 13, "bold")).grid(row=1, column=0)
        rotulo(self, "Frota inimiga (clique para atirar)", ("Helvetica", 13, "bold")).grid(row=1, column=1)
        self.canvas_jogador = TabuleiroCanvas(self, self.jogador, True)
        self.canvas_jogador.grid(row=2, column=0, padx=10)
        self.canvas_inimigo = TabuleiroCanvas(self, self.inimigo, False, self.atirar)
        self.canvas_inimigo.grid(row=2, column=1, padx=10)

        self.status = rotulo(self, "Sua vez!", ("Helvetica", 13, "bold"))
        self.status.grid(row=3, column=0, columnspan=2, pady=(12, 4))

        self.mensagem_afundamento = rotulo(self, "", ("Helvetica", 12, "bold"))
        self.mensagem_afundamento.grid(row=4, column=0, columnspan=2, pady=5)

        self.log = tk.Listbox(self, height=5, width=80, font=FONTE, bg="#123a5e",
                              fg=COR["texto"], highlightthickness=0)
        self.log.grid(row=5, column=0, columnspan=2)
        botao(self, "Desistir", lambda: app.mostrar(TelaMenu), 12).grid(row=6, column=0, columnspan=2, pady=8)
        botao(self, "Salvar e sair", self.salvar_e_sair, 12).grid(row=7, column=0, columnspan=2, pady=8)

        # Recuperar histórico da partida salva
        for jogada in self.historico_log:
            self.log.insert("end", jogada)

        self.atualizar_placar()

        if not self.vez_jogador:
            self.status.config(text="Vez do adversário...")
            self.after_ia_id = self.after(700, self.turno_ia)

    def destroy(self):
        # Cancela tudo que estiver agendado para não dar TclError ao trocar de tela
        for attr in ("after_ia_id", "after_msg_id"):
            id_ = getattr(self, attr, None)
            if id_ is not None:
                try:
                    self.after_cancel(id_)
                except tk.TclError:
                    pass
                setattr(self, attr, None)
        super().destroy()

    def salvar_e_sair(self):
        duracao = round(time.monotonic() - self.inicio)
        estado = {
            "jogador": self.app.jogador,
            "tabuleiro_jogador": self.jogador.para_dict(),
            "tabuleiro_inimigo": self.inimigo.para_dict(),
            "estado_ia": self.ia.para_dict(),
            "estatisticas": {
                "tiros": self.tiros,
                "acertos": self.acertos,
                "tiros_ia": self.tiros_ia
            },
            "vez_jogador": self.vez_jogador,
            "duracao_s": duracao,
            "log": list(self.log.get(0, "end"))
        }
        if not persistencia.salvar_estado_jogo(estado):
            messagebox.showerror(
                "Erro ao salvar",
                "Não foi possível salvar a partida."
            )
            return
        messagebox.showinfo(
            "Partida salva",
            "Sua partida foi salva com sucesso!"
        )
        self.app.mostrar(TelaMenu)

    def atualizar_placar(self):
        voce = self.jogador.navios_restantes()
        inimigo = self.inimigo.navios_restantes()
        for rot, qtd in ((self.num_voce, voce), (self.num_inimigo, inimigo)):
            if qtd == 0:
                cor = "#7a8a99"
            elif qtd == 1:
                cor = COR["acerto"]
            else:
                cor = COR["texto"]
            rot.config(text=str(qtd), fg=cor)

    def mostrar_mensagem_afundamento(self, nome):
        self.mensagem_afundamento.config(
            text=f"Você afundou o {nome} inimigo!",
            fg=COR["ok"]
        )
        if self.after_msg_id is not None:
            self.after_cancel(self.after_msg_id)
        self.after_msg_id = self.after(3000, self._limpar_mensagem_afundamento)

    def _limpar_mensagem_afundamento(self):
        self.after_msg_id = None
        self.mensagem_afundamento.config(text="")

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

        if resultado == "afundou":
            self.mostrar_mensagem_afundamento(nome)

        self.canvas_inimigo.desenhar()
        self.atualizar_placar()
        if self.inimigo.todos_afundados():
            return self.fim(True)

        if self.inimigo.navios_restantes() == 1 and not self.aviso_ultimo_navio:
            self.aviso_ultimo_navio = True
            messagebox.showinfo("Último navio!", "Apenas 1 navio inimigo sobrando!")

        self.vez_jogador = False
        self.status.config(text="Vez do adversário...")
        self.after_ia_id = self.after(700, self.turno_ia)

    def turno_ia(self):
        self.after_ia_id = None
        jogada = self.ia.escolher()
        if jogada is None:
            return
        l, c = jogada
        resultado, nome = self.jogador.atirar(l, c)
        self.ia.registrar(l, c, resultado)
        self.tiros_ia += 1
        self._registrar("Inimigo", l, c, resultado, nome)
        self.canvas_jogador.desenhar()
        self.atualizar_placar()
        if self.jogador.todos_afundados():
            return self.fim(False)

        if (self.jogador.navios_restantes() == 1
                and not self.aviso_ultimo_navio_jogador):
            self.aviso_ultimo_navio_jogador = True
            messagebox.showwarning("Cuidado!", "Você só tem 1 navio restante!")

        self.vez_jogador = True
        self.status.config(text="Sua vez!")

    def fim(self, venceu):
        self.vez_jogador = False
        if self.after_ia_id is not None:
            self.after_cancel(self.after_ia_id)
            self.after_ia_id = None
        registro = self.app.ao_terminar_partida({
            "venceu": venceu,
            "tiros": self.tiros,
            "acertos": self.acertos,
            "tiros_inimigo": self.tiros_ia,
            "duracao_s": round(time.monotonic() - self.inicio)
        })
        persistencia.excluir_estado_jogo()
        messagebox.showinfo(
            "Fim de jogo",
            "Você venceu!" if venceu else "Sua frota foi destruída."
        )
        self.app.mostrar(TelaEstatisticas, ultima=registro)


class TelaEstatisticas(tk.Frame):

    COLUNAS = (("data", "Data/hora", 135), ("jogador", "Jogador", 95),
               ("resultado", "Resultado", 85), ("tiros", "Tiros", 55),
               ("acertos", "Acertos", 70), ("precisao", "Precisão", 75),
               ("inimigo", "Tiros inim.", 90), ("duracao", "Duração", 75))

    def __init__(self, app, ultima=None):
        super().__init__(app, bg=COR["fundo"])
        self.app = app
        self.ultima = ultima
        self.historico = persistencia.carregar_historico()
        if ultima is not None and (not self.historico or self.historico[-1] != ultima):
            self.historico.append(ultima)  # salvamento falhou: ainda assim mostra a partida
        self.canvas_grafico = None

        rotulo(self, "📊 Estatísticas", FONTE_TITULO).grid(row=0, column=0, columnspan=2, pady=(0, 10))
        if ultima is not None:
            self._montar_ultima_partida().grid(row=1, column=0, columnspan=2, pady=(0, 10))
        self._montar_resumo().grid(row=2, column=0, columnspan=2, pady=(0, 14))

        esquerda = tk.Frame(self, bg=COR["fundo"])
        esquerda.grid(row=3, column=0, padx=(0, 16), sticky="n")
        self.area_grafico = tk.Frame(esquerda, bg=COR["fundo"])
        self.area_grafico.pack()

        direita = tk.Frame(self, bg=COR["fundo"])
        direita.grid(row=3, column=1, sticky="n")
        rotulo(direita, "Histórico de partidas", ("Helvetica", 13, "bold")).pack(anchor="w", pady=(0, 6))
        self._montar_tabela(direita)

        botao(self, "Voltar ao menu", lambda: app.mostrar(TelaMenu)).grid(
            row=4, column=0, columnspan=2, pady=(16, 0))
        self.mostrar_grafico(next(iter(est.GRAFICOS)))

    # -- resumo -------------------------------------------------------------
    def _cartao(self, master, valor, legenda):
        quadro = tk.Frame(master, bg=COR["painel"], padx=18, pady=8)
        tk.Label(quadro, text=valor, font=("Helvetica", 18, "bold"),
                 bg=COR["painel"], fg=COR["texto"]).pack()
        tk.Label(quadro, text=legenda, font=("Helvetica", 9),
                 bg=COR["painel"], fg=COR["texto"]).pack()
        return quadro

    def _montar_resumo(self):
        r = est.resumo(self.historico)
        melhor = r["melhor_partida"]
        cartoes = [
            (str(r["partidas"]), "partidas"),
            (str(r["vitorias"]), "vitórias"),
            (str(r["derrotas"]), "derrotas"),
            (f"{r['taxa_vitoria']:.0f}%", "taxa de vitória"),
            (f"{r['precisao_media']:.0f}%", "precisão média"),
            (f"{melhor['tiros']} tiros" if melhor else "—", "melhor vitória"),
        ]
        quadro = tk.Frame(self, bg=COR["fundo"])
        for i, (valor, legenda) in enumerate(cartoes):
            self._cartao(quadro, valor, legenda).grid(row=0, column=i, padx=5)
        return quadro

    def _montar_ultima_partida(self):
        u = self.ultima
        precisao = est.precisao(est.normalizar_historico([u])[0])
        texto_precisao = f"{precisao:.0f}%" if precisao is not None else "—"
        resultado = "VITÓRIA" if u["venceu"] else "DERROTA"
        return tk.Label(
            self, bg=COR["fundo"], font=("Helvetica", 12, "bold"),
            fg=COR["ok"] if u["venceu"] else COR["derrota"],
            text=(f"Última partida: {resultado} — {u['tiros']} tiros, {u['acertos']} acertos "
                  f"({texto_precisao}) · inimigo atirou {u['tiros_inimigo']}x · "
                  f"duração {est.formatar_duracao(u['duracao_s'])}"))

    # -- tabela -------------------------------------------------------------
    def _montar_tabela(self, master):
        estilo = ttk.Style(self)
        estilo.theme_use("clam")
        estilo.configure("BN.Treeview", background=COR["painel"], fieldbackground=COR["painel"],
                         foreground=COR["texto"], rowheight=24, borderwidth=0, font=FONTE)
        estilo.configure("BN.Treeview.Heading", background=COR["botao_ativo"], foreground="white",
                         relief="flat", font=("Helvetica", 10, "bold"))
        estilo.map("BN.Treeview", background=[("selected", COR["botao"])],
                   foreground=[("selected", "white")])
        estilo.map("BN.Treeview.Heading", background=[("active", COR["botao"])])

        quadro = tk.Frame(master, bg=COR["fundo"])
        quadro.pack()
        tabela = ttk.Treeview(quadro, columns=[c[0] for c in self.COLUNAS], show="headings",
                              height=11, style="BN.Treeview", selectmode="browse")
        for chave, titulo, largura in self.COLUNAS:
            tabela.heading(chave, text=titulo)
            tabela.column(chave, width=largura, anchor="center", stretch=False)
        tabela.tag_configure("vitoria", foreground=COR["ok"])
        tabela.tag_configure("derrota", foreground=COR["derrota"])
        rolagem = ttk.Scrollbar(quadro, orient="vertical", command=tabela.yview)
        tabela.configure(yscrollcommand=rolagem.set)
        tabela.pack(side="left")
        rolagem.pack(side="left", fill="y")

        registros = est.normalizar_historico(self.historico)
        for reg in reversed(registros):  # mais recente primeiro
            prec = est.precisao(reg)
            tabela.insert("", "end", tags=("vitoria" if reg["venceu"] else "derrota",), values=(
                est.formatar_data(reg["data_hora"]), reg["jogador"],
                "Vitória" if reg["venceu"] else "Derrota", reg["tiros"], reg["acertos"],
                f"{prec:.0f}%" if prec is not None else "—", reg["tiros_inimigo"],
                est.formatar_duracao(reg["duracao_s"])))
        if not registros:
            rotulo(master, "Nenhuma partida registrada ainda.").pack(pady=8)
        elif self.ultima is not None:
            primeiro = tabela.get_children()[0]
            tabela.selection_set(primeiro)  # destaca a partida que acabou de terminar
            tabela.see(primeiro)
        self.tabela = tabela

    # -- gráficos -----------------------------------------------------------
    def mostrar_grafico(self, nome):
        if self.canvas_grafico is not None:
            self.canvas_grafico.get_tk_widget().destroy()
        figura = est.GRAFICOS[nome](self.historico)
        self.canvas_grafico = FigureCanvasTkAgg(figura, master=self.area_grafico)
        self.canvas_grafico.draw()
        self.canvas_grafico.get_tk_widget().configure(highlightthickness=0, bg=COR["fundo"])
        self.canvas_grafico.get_tk_widget().pack()