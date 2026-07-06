# Veritas — Master Plan para a v1.0 ("aplicativo completo")

> Este é o prompt-mestre detalhado que orienta a evolução do Veritas de um
> protótipo bem-feito (v0.6.0) para um produto de portfólio completo (v1.0).
> Cada fase é independente, versionada, com testes verdes + layout check +
> screenshot antes de commitar. Nada de reescrever o que já funciona — o
> motor, os testes e a GUI são a fundação; nós construímos por cima.

## Contexto para a IA executora

Veritas é um desobfuscador desktop (Python 3.10+ / PySide6) para análise
defensiva de payloads (SOC / IR / Blue Team). Motor 100% desacoplado da
interface (`ps_deobfuscator/engine.py` não importa nada de GUI). Objetivo
duplo: ferramenta real **e** vitrine de portfólio para LinkedIn. Princípios
inegociáveis: análise estática (nunca executar payload), confiabilidade antes
de features (todo decode errado vira teste de regressão), motor separado da
interface, tudo em inglês na UI.

## Diagnóstico (base da pesquisa 2026 + auditoria do código)

Forças: separação motor/GUI/CLI real; `pyproject.toml` moderno; 32 testes;
empacotamento PyInstaller windowed funcional. Lacunas encontradas:

1. Trabalho não publicado no GitHub (8 commits à frente do origin).
2. Sem CI, sem linter, sem type-checker.
3. Código morto (`gui/main.py`).
4. Como "desobfuscador", faltam formatos comuns em malware real e o modo
   **manual/guiado** (hoje só há heurística automática).
5. Sem screenshots/demo no README.

## Fases

### Fase 1 — Qualidade e publicação (fundação de credibilidade) — v0.7.0
- [x] Remover código morto (`gui/main.py`).
- [x] `ruff` (lint + import sort) configurado e limpo.
- [x] `mypy` no pacote `ps_deobfuscator` (lógica pura) sem erros.
- [x] GitHub Actions: matriz de Python, roda ruff + mypy + os testes a cada push.
- [ ] Push do repositório (ação do dono — publica identidade pública).
- [ ] Screenshots renderizados no README + narrativa "por quê" (workflow Blue Team).

### Fase 2 — Cobertura de formatos (identidade de "desobfuscador") — v0.7.0
Adicionar decodificadores comuns em malware real, cada um com detecção
conservadora (baixo falso-positivo) e testes:
- [x] **Ascii85 / Base85** (Adobe `<~…~>` e raw).
- [x] **Entidades HTML** (`&#65;`, `&#x41;`) — ofuscação web/HTA.
- [x] **JWT** — decodifica header+payload como JSON (alto valor visual, baixo falso-positivo).
- [x] **Arrays de char-code** — `String.fromCharCode(...)` (JS) e `[char[]](...)` (PowerShell).
- [ ] Decimal/octal puro e VBScript `Chr()+concat` (fase futura; risco de falso-positivo maior).

### Fase 3 — Decodificação manual/guiada (o maior diferencial) — v0.8.0
Resolve de raiz a classe de bug "a heurística escolheu errado":
- Nova API no motor: `apply_operation(text, op)` (aplica UMA transformação
  incondicionalmente) e `decode_with_ops(text, [ops])` (pipeline manual),
  sem depender de score. Reusa os decodificadores existentes.
- GUI: ao lado da cadeia automática, um modo "Manual" onde o analista
  encadeia operações (dropdown de operações: URL, Hex, Base64, Base32,
  Ascii85, GZIP, XOR key, ROT-N, HTML entity, …) e vê o resultado camada a
  camada — inspirado no "recipe" do CyberChef, mas enxuto.
- Toda operação manual é reversível/re-editável; exportável como "receita".

### Fase 4 — Integração Blue Team / entregáveis — v0.9.0
- Exportação **STIX 2.1** e **MISP** dos IOCs (padrão de fato para sharing).
- Modo **batch** visível na GUI (já existe na CLI): soltar vários arquivos,
  decodificar todos, exportar relatório consolidado.
- "Defanging"/"refanging" de IOCs (`hxxp://`, `1.2.3[.]4`) — convenção de IR.

### Fase 5 — Produto e distribuição — v1.0.0
- Empacotar fonte **Inter** (OFL) para travar o visual Apple em qualquer máquina.
- Instalador Windows (Inno Setup) com atalho no Menu Iniciar.
- Memória de janela já feita (v0.5.0); revisar escala high-DPI.
- README final com GIF de demonstração, badges de CI, seção de arquitetura.

## Regras de execução (para qualquer sessão)
1. Uma fase por vez; nunca quebrar testes existentes.
2. Todo decode incorreto reportado → fixture de regressão antes da correção.
3. Detecção de formato sempre conservadora; o scoring + o guard de
   "legível→ilegível só se melhora" (v0.3.1) protegem contra falso-positivo.
4. Verificar sempre: `unittest` + `scripts/check_gui_layout.py` + screenshot.
5. Versionar (`app_info.py` + `pyproject.toml`), atualizar `CHANGELOG.md`,
   commit descritivo.
