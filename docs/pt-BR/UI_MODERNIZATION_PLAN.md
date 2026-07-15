# Plano de Modernização da UI — Veritas

> Aprovado para execução em sessões futuras. Objetivo: sensação de produto
> real (fluidez, feedback, responsividade) mantendo a stack PySide6 — nada de
> reescrever em web. Cada fase termina com testes verdes +
> `scripts/check_gui_layout.py` passando.

## Fase 1 — Movimento (animações)

1. **Sidebar animada** *(pedido do Fabio)*: trocar o `setFixedWidth()` seco
   por `QPropertyAnimation` na largura (≈200 ms, easing `OutCubic`), com fade
   nos rótulos via `QGraphicsOpacityEffect` para o texto não "pular" ao
   recolher/expandir.
2. **Accordion de camadas suave**: animar a altura do corpo ao expandir uma
   camada da cadeia de decodificação, em vez de mostrar/esconder de uma vez.
3. **Transição entre páginas**: crossfade curto ao alternar
   Quick Decode ↔ History no `QStackedWidget`.

## Fase 2 — Feedback e microinterações

4. **Toast "Copied!"**: notificação flutuante discreta (~1,5 s com fade) ao
   copiar IOC ou texto final, em vez de nenhum feedback.
5. **Botão Decode com progresso embutido**: estado de "decodificando" dentro
   do próprio botão (texto + indicador), substituindo a barra de progresso
   separada.
6. **Profundidade**: sombra suave nos cards (`QGraphicsDropShadowEffect`) e
   realce de foco mais visível nos campos.

## Fase 3 — Responsividade real

7. **Quebra automática**: stat pills e linha de ações reorganizam em duas
   linhas (FlowLayout) em janelas estreitas, em vez de espremer.
8. **Escala por DPI**: revisar tamanhos fixos em pt/px para monitores de alta
   densidade e o modo de escala do Windows.
9. **Tabela IOC**: colunas com redimensionamento mais inteligente em larguras
   pequenas (prioridade para a coluna Value).

## Fase 4 — Sensação de app de verdade

10. **Memória de janela**: lembrar tamanho, posição e estado da sidebar entre
    sessões (`QSettings`).
11. **Instância única**: abrir o atalho com o app já aberto traz a janela para
    frente em vez de abrir uma segunda cópia.
12. **Distribuição**: build PyInstaller windowed atualizado + futuramente um
    instalador (Inno Setup) com atalho no Menu Iniciar.

## Status (v0.5.0 — 2026-07-02)

| Item | Status |
|------|--------|
| 1. Sidebar animada | ✅ v0.5.0 |
| 2. Accordion suave | ✅ v0.5.0 |
| 3. Transição entre páginas | ✅ v0.5.0 (crossfade) |
| 4. Toast "Copied!" | ✅ v0.5.0 (+ exportações) |
| 5. Botão Decode com progresso embutido | mantido como está (texto "Decoding..." + barra) |
| 6. Sombras nos cards | ❌ descartado de propósito: Qt permite 1 efeito gráfico por widget (conflita com o crossfade) e rasteriza o card inteiro a cada repaint, prejudicando o scroll |
| 7. Quebra automática (pills) | ✅ v0.5.0 (FlowLayout) |
| 8. Escala por DPI | parcial (PassThrough já ativo); revisar em monitor high-DPI real |
| 9. Tabela IOC responsiva | ✅ v0.5.0 (Confidence auto-size) |
| 10. Memória de janela | ✅ v0.5.0 (QSettings) |
| 11. Instância única | ✅ v0.5.0 (QLocalServer) |
| 12. Build windowed + instalador | ⏳ próximo (PyInstaller já configurado; falta Inno Setup) |

Extras da pesquisa de UX (fora do plano original), também em v0.5.0:
barra de título nativa escura no Windows (checklist da Microsoft: janela
nativa deve combinar com o tema) e botão **Copy all IOCs** (diretriz de
SOC: do alerta à ação em segundos, sem copiar linha a linha).

Itens entregues antes deste plano: abrir sem janela de console
(v0.4.0, `[project.gui-scripts]` + atalho `Veritas.lnk`).
