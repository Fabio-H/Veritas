# Veritas

[English](README.md) · **Português (pt-BR)**

### Desobfuscador automático de payloads para SOC, IR e Blue Team

**Veritas** revela o que está escondido em comandos PowerShell ofuscados e
strings codificadas. O analista cola o blob suspeito; a ferramenta identifica
as camadas de codificação, decodifica recursivamente e extrai os Indicadores
de Comprometimento (IOCs) — tudo localmente, sem executar nada e sem enviar
dados para lugar nenhum.

O nome é um trocadilho com a ideia de extrair a **verdade** ("veritas") do que
o atacante tentou esconder.

[![Download latest release](https://img.shields.io/github/v/release/Fabio-H/Veritas?label=download&logo=github)](https://github.com/Fabio-H/Veritas/releases/latest)
[![CI](https://github.com/Fabio-H/Veritas/actions/workflows/ci.yml/badge.svg)](https://github.com/Fabio-H/Veritas/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/GUI-PySide6%20(Qt%206)-41CD52?logo=qt&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-blue)

> **Nota:** o idioma padrão do repositório é o inglês. Este documento é a
> tradução em português; a versão canônica é o [README.md](README.md).

---

## Por que existe

No dia a dia de **SOC (Tier 2)** e **Incident Response** é comum encontrar
PowerShell ofuscado, Base64, Hex, URL encoding e outras camadas empilhadas em
logs de endpoint. Decodificar isso manualmente consome tempo e aumenta o risco
de erro. O Veritas automatiza a triagem: cadeia de decodificação visível
camada por camada, texto final com destaques e tabela de IOCs pronta para
correlação.

## Funcionalidades

- **Decodificação recursiva** (até 8 camadas) com pontuação heurística —
  palavras-chave de PowerShell malicioso + legibilidade decidem a melhor
  transformação em cada passo.
- **Formatos suportados:** URL encoding, Hex, Base64 (UTF-8 e UTF-16LE),
  Base32, Ascii85/Base85, GZIP, zlib/DEFLATE, ROT13, XOR de 1 byte (força
  bruta das 256 chaves), escapes Unicode (`\x..`, `\u....`, `%u....`),
  entidades HTML (`&#65;`, `&#x41;`), JWT (header + payload), arrays de
  char-code (`String.fromCharCode(...)`, `[char[]](...)`),
  `-EncodedCommand`/`-enc` do PowerShell e Base64 embutido em atribuições de
  variável (`$x = "..."`).
- **Pipeline manual:** quando a heurística automática escolhe o ramo errado,
  monte uma receita de decodificação à mão — encadeie operações (Base64, Hex,
  XOR com chave, ROT13, reverse, …) e inspecione o resultado passo a passo.
- **Extração de IOCs:** IPv4/IPv6, URLs, domínios (com heurística para não
  confundir FQDN com namespace .NET), e-mails, hashes MD5/SHA1/SHA256 e
  comandos PowerShell suspeitos.
- **Histórico persistente:** as últimas 20 análises ficam salvas localmente e
  são restauradas ao abrir o app, byte a byte idênticas ao momento da captura.
- **Exportação** dos relatórios em TXT e JSON, com metadados de versão e
  timestamp.
- **CLI** (via [Rich](https://github.com/Textualize/rich)) para uso em
  terminal, além da GUI desktop.

## Segurança por padrão

- **Análise 100% estática** — payloads são decodificados e inspecionados,
  nunca executados.
- Entradas acima de 1.000.000 de caracteres são rejeitadas.
- Descompressão GZIP/zlib é limitada para evitar bombas de descompressão.
- Nenhum dado sai da máquina.

## Instalação e uso

Requisitos: **Python 3.10+** no Windows (Linux/macOS devem funcionar, mas o
foco de teste é Windows). Ou baixe o pacote pronto na
[última release do Windows](https://github.com/Fabio-H/Veritas/releases/latest)
— sem precisar de Python.

```powershell
git clone https://github.com/Fabio-H/Veritas.git
cd Veritas/ps-deobfuscator
pip install -e ".[gui]"
python main_gui.py
```

CLI:

```powershell
pip install -e .
ps-deobfuscator decode --help
```

### Build do executável Windows

```powershell
cd ps-deobfuscator
pip install -e ".[gui,dev,build]"
python scripts\build_exe.py
```

Saídas: `release/ps-deobfuscator-gui/ps-deobfuscator-gui.exe` e
`release/Veritas-vX.Y.Z-windows.zip`. Um push de tag `v*.*.*` faz esse build
automaticamente e anexa o zip a uma GitHub Release.

## Como usar

1. Cole o texto ofuscado (log, comando, string exportada do SIEM) na área de
   entrada — ou arraste um arquivo `.txt`.
2. Clique em **Decode**.
3. Revise as **camadas** da cadeia de decodificação, o **texto final** com
   destaques e a tabela de **IOCs**.
4. Exporte em TXT/JSON ou copie os IOCs conforme necessário.

## Arquitetura

```
ps-deobfuscator/
  ps_deobfuscator/   # Motor de decodificação + CLI (sem dependência de GUI)
    engine.py        #   decodificação recursiva, scoring, extração de IOCs
    history.py       #   persistência do histórico (JSON atômico, versionado)
  gui/               # App desktop PySide6 (temas, janela, widgets)
  samples/           # Biblioteca de payloads de teste (known-good + triage)
  scripts/           # build do .exe, ícones, run_samples, limpeza
  tests/             # suíte unittest (motor, histórico, imports)
```

A separação estrita entre o motor puro e a GUI é uma decisão de design — veja
[docs/architecture-decisions.md](docs/architecture-decisions.md).

## Testes

```powershell
cd ps-deobfuscator
python -m unittest discover -s tests
```

## Processo de desenvolvimento

O Veritas foi construído em "vibe coding" — um humano em par com uma IA. A
arquitetura, o design e os trade-offs de segurança são de minha autoria e
responsabilidade; o raciocínio por trás das decisões está em
[docs/architecture-decisions.md](docs/architecture-decisions.md).

## Aviso de isenção de responsabilidade

Esta ferramenta é fornecida **"como está"**, para fins legítimos de análise
defensiva, pesquisa e educação em cibersegurança. Não substitui processos
formais de resposta a incidentes. **Não execute** comandos ou binários
desconhecidos em sistemas de produção.

## Licença

Licenciado sob a **Licença MIT** — veja [LICENSE](LICENSE).
