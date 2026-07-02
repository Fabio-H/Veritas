# Veritas — Brief do Projeto

> Este documento é o "prompt-mestre" do projeto: o que estamos construindo,
> por quê, e como decidimos o que entra ou não. Sessões futuras de
> desenvolvimento (humano + IA) devem partir daqui.

## Objetivo

Construir o **Veritas**: um desobfuscador desktop de payloads maliciosos
(Base64, Hex, URL encoding, GZIP/zlib, XOR e camadas empilhadas) com extração
automática de IOCs, voltado para o fluxo de trabalho real de **SOC, Incident
Response e Blue Team**.

O projeto tem duas metas simultâneas:

1. **Ferramenta real** — o analista cola um blob suspeito, o Veritas revela o
   texto por trás e lista os indicadores (IPs, URLs, domínios, hashes,
   comandos PowerShell suspeitos). Análise 100% estática: nada é executado.
2. **Vitrine de portfólio (LinkedIn)** — código, UI e documentação com
   qualidade de produto: visual profissional, testes automatizados, releases
   versionados e README com demonstração visual.

## Princípios de decisão

- **Confiabilidade antes de features.** Todo payload que decodificar errado
  vira caso de teste em `ps-deobfuscator/samples/triage/` e só sai de lá
  quando o motor acertar. A suíte de testes nunca regride.
- **Motor separado da interface.** `ps_deobfuscator/engine.py` não importa
  nada de GUI; a GUI (PySide6) e a CLI são consumidores do motor.
- **Segurança por padrão.** Payloads nunca são executados; limites de tamanho
  e de descompressão protegem contra bombas; exports carregam metadados de
  versão.
- **Escopo atual: desktop Windows.** Sem versão web neste repositório.
  Escalar (novos formatos, integrações, i18n) só depois da casa arrumada.

## Estado atual e prioridades

| # | Prioridade | Status |
|---|-----------|--------|
| 1 | Ambiente reproduzível (Python + deps + testes verdes) | ✅ |
| 2 | Histórico commitado e repositório organizado | ✅ |
| 3 | Biblioteca de payloads de teste (`samples/`) para reproduzir erros de decodificação | ✅ |
| 4 | Redesign da UI: tema escuro profissional, layout responsivo, cara de produto | 🔨 em andamento |
| 5 | Corrigir payloads Base64 que decodificam errado (aguardando amostras em `samples/triage/`) | ⏳ |
| 6 | CI (GitHub Actions) + screenshots/GIF no README + release `.zip` | ⏳ |

## Texto "About" do GitHub (máx. 100 caracteres)

- PT: `Desobfuscador de payloads para Blue Team: decodificação recursiva e extração de IOCs no desktop.`
- EN: `Payload deobfuscator for Blue Team: recursive decoding & IOC extraction, desktop app.`

## Como reproduzir um erro de decodificação

1. Salve o payload problemático em um `.txt` dentro de
   `ps-deobfuscator/samples/triage/` (um payload por arquivo).
2. Rode `python scripts/run_samples.py` — o script imprime a cadeia de
   decodificação completa de cada amostra.
3. Descreva qual era a saída esperada; o caso vira fixture de teste e a
   correção entra no motor.
