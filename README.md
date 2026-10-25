# Batalha-Naval-PJBL
PjBL - Raciocínio Algorítmico

Jogo de Batalha Naval em Python com interface gráfica (tkinter), persistência de dados e visualização de estatísticas.

## Como executar
```
pip install -r requirements.txt
python main.py
```
Requer Python 3.10+ (tkinter já vem com o Python; no Linux: `sudo apt install python3-tk`).

## Estrutura
- `main.py` — ponto de entrada
- `batalha_naval/interface.py` — telas e widgets (tkinter)
- `batalha_naval/modelo.py` — regras do jogo, tabuleiro e IA
- `batalha_naval/persistencia.py` — salvar/carregar partidas (a criar)
- `batalha_naval/estatisticas.py` — gráficos (a criar)
- `registros_individuais/` — PDFs de cada integrante

## Divisão da equipe
1. Interface gráfica
2. Lógica do jogo e IA
3. Persistência e visualização de dados
