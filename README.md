

# Veritas

### Decodificador automático de payloads ofuscados para SOC, IR e Blue Team

> **Veritas** revela o que está escondido em comandos PowerShell e strings codificadas. O foco atual é o app desktop Windows em Python/PySide6; a versão web standalone continua disponível em `web/`.

[HTML5](https://developer.mozilla.org/docs/Web/HTML)
[JavaScript](https://developer.mozilla.org/docs/Web/JavaScript)
[Tailwind CSS](https://tailwindcss.com/)
[License](LICENSE)
[Status](https://github.com)

---

## Visão geral

No dia a dia de **SOC (Tier 2)** e **Incident Response**, é comum encontrar trechos de **PowerShell ofuscado**, **Base64**, **Hex**, **URL encoding** e outras camadas empilhadas em logs de endpoint. Decodificar isso manualmente consome tempo e aumenta o risco de erro.

**Veritas** é um *deobfuscator* pensado para esse fluxo: o analista **cola o bloco de texto suspeito** e a ferramenta tenta **identificar o tipo de codificação**, aplicar **decodificação recursiva** (várias camadas, automaticamente) e **extrair Indicadores de Comprometimento (IoCs)** — por exemplo, IPs, URLs e padrões relevantes que estavam “por trás” da ofuscação.

O nome é um trocadilho com a ideia de extrair a **verdade** do que o atacante tentou esconder.

---

## Principais funcionalidades

- **Decodificação recursiva** — até várias camadas (ex.: Base64 dentro de Hex, ou sequência URL → texto → Base64), com limite configurável no código.
- **Detecção de formatos** — tentativas automáticas para **URL encoding**, **Hex**, **Base64** (incluindo variantes com **UTF-8**, **UTF-16LE** e **GZIP** quando o *magic* `1F 8B` estiver presente).
- **Pontuação heurística** — escolha da “melhor” transformação por camada com base em palavras-chave e legibilidade do texto.
- **Extração de IoCs** — IPv4/IPv6, URLs, domínios (com heurísticas para não confundir FQDN com namespaces .NET), e-mails, hashes (MD5/SHA1/SHA256) e padrões PowerShell marcados para análise.
- **Interface web** — uma única página HTML em [`web/payload-deobfuscator.html`](web/payload-deobfuscator.html) com **Tailwind CSS** via CDN; roda localmente no navegador.
- **Interface desktop (Python / Qt)** — projeto em [`ps-deobfuscator/`](ps-deobfuscator/); após o build, atalho na raiz: **`Veritas GUI.bat`** → `release/ps-deobfuscator-gui/`.

---

## App desktop Windows

O app principal fica em [`ps-deobfuscator/`](ps-deobfuscator/) e pode ser executado a partir do código-fonte ou empacotado como bundle Windows.

```powershell
cd ps-deobfuscator
pip install -e ".[gui,dev,build]"
python -m unittest discover -s tests
python scripts\build_exe.py
```

Saídas principais:

- `release/ps-deobfuscator-gui/ps-deobfuscator-gui.exe` — executável de acesso fácil.
- `release/Veritas-vX.Y.Z-windows.zip` — pacote versionado para distribuição.
- `Veritas GUI.bat` — launcher na raiz do projeto.

## Interface web standalone

Não há **servidor obrigatório** nem **Node.js** para o modo web: basta um navegador moderno.

### Clonar o repositório

```bash
git clone https://github.com/SEU_USUARIO/veritas.git
cd veritas
```

Substitua `SEU_USUARIO` pelo seu usuário ou organização no GitHub.

### Executar localmente

1. Abra o arquivo principal no navegador:
  - **Windows:** clique duas vezes em `web/payload-deobfuscator.html` **ou** arraste o arquivo para uma janela do Chrome/Edge/Firefox.
  - **Linha de comando (opcional):**

```bash
# Exemplo com Python (módulo http embutido)
python -m http.server 8080
# Acesse: http://localhost:8080/web/payload-deobfuscator.html
```

1. **Conectividade:** a página carrega **Tailwind CSS** da CDN; sem internet, o estilo pode não aplicar — o núcleo JavaScript continua no arquivo.

### Dependências web


| Dependência       | Uso                                                      |
| ----------------- | -------------------------------------------------------- |
| Navegador recente | `DecompressionStream` (GZIP), `TextDecoder`, `clipboard` |
| Rede (opcional)   | CDN do Tailwind para estilos                             |


Não há `package.json` nem build obrigatório nesta versão.

---

## Como usar

1. Cole o texto ofuscado (log, comando, string exportada do SIEM, etc.) na área de entrada.
2. Clique em **Decodificar Automaticamente**.
3. Revise as **camadas** expandidas, o **texto final** com destaques e a tabela de **IOCs**.
4. Use **Copiar texto final**, **Copiar todos IOCs** ou **Baixar .txt** conforme necessário.

### Exemplo ilustrativo (cenário educacional)

> Os dados abaixo são **fictícios** e servem apenas para demonstrar o fluxo *antes* / *depois*. Não representam malware real.

**Antes (input — trecho ofuscado em Base64, exemplo genérico):**

```text
cG93ZXJzaGVsbC5leGUgLWVwIGJ5cGFzcyAtYyAiVGVzdC1Db25uZWN0aW9uIC1Db21wdXRlck5hbWUgMTkyLjAuMi4xMCI=
```

**Depois (saída esperada do Veritas — texto decodificado e IoCs):**

O decodificador revela o comando em texto claro e destaca, entre outros:

- **IPv4** extraído (ex.: `192.0.2.10` — endereço [DOCUMENTAÇÃO RFC 5737](https://datatracker.ietf.org/doc/html/rfc5737) reservado para exemplos).
- Possíveis correspondências em **PowerShell** para revisão na tabela de IoCs.

Na prática, o analista usa isso para **priorizar triage**, correlacionar com telemetria e **não** para executar o comando em produção.

---

## Arquitetura / Como funciona

1. **Entrada bruta** — o texto inicial é a “camada 0”.
2. **Por camada**, o motor avalia candidatos:
  - decodificação **URL** (quando há `%XX`);
  - decodificação **Hex** (comprimento par, apenas hex);
  - **Base64** com múltiplas interpretações dos bytes (UTF-8, UTF-16LE, e via **GZIP** se aplicável).
3. Cada candidato recebe uma **pontuação** (palavras-chave de interesse + razão de caracteres imprimíveis).
4. Escolhe-se o melhor passo; se a pontuação não melhora e não há mais codificação aparente, o loop para.
5. No texto final, rodam-se **regex e heurísticas** para IoCs e destaques visuais (URLs, IPs, padrões PowerShell configuráveis).

Tudo roda **no cliente** (JavaScript no navegador). Não enviamos seu payload a servidores do projeto.

---

## Roadmap / To-do


| Prioridade | Ideia                                                                                        |
| ---------- | -------------------------------------------------------------------------------------------- |
| Alta       | Empacotamento opcional (PWA ou extensão de navegador) para uso offline com estilos embutidos |
| Média      | Exportação estruturada (JSON/STIX) para integração com playbooks                             |
| Média      | Testes automatizados (ex.: casos de decodificação em CI)                                     |
| Baixa      | Internacionalização (i18n) da interface                                                      |


Sugestões e *issues* são bem-vindas.

---

## Como contribuir

1. **Fork** o repositório e crie uma branch descritiva (`feat/...`, `fix/...`).
2. Mantenha commits **pequenos e legíveis**; mensagens em português ou inglês, no imperativo (ex.: “Adiciona teste para decodificação Hex”).
3. Para mudanças na UI, preserve **acessibilidade** e **contraste**; para lógica de decodificação, prefira **casos de teste** reproduzíveis.
4. Abra um **Pull Request** explicando o problema e a solução; referencie *issues* quando existirem.
5. Código malicioso, *payloads* reais de ambientes de produção sem anonimização ou conteúdo que viole leis **não** serão aceitos.

---

## Aviso de isenção de responsabilidade

Esta ferramenta é fornecida **“como está”**, para **fins legítimos de análise defensiva**, pesquisa e educação em cibersegurança. **Não** constitui aconselhamento profissional nem substitui processos formais de resposta a incidentes. Os autores **não** se responsabilizam por uso indevido, perdas de dados ou decisões tomadas com base na saída do Veritas. **Não execute** comandos ou binários desconhecidos em sistemas de produção. O projeto está em **desenvolvimento** e **não** foi validado de ponta a ponta contra todos os cenários do mundo real.

---

## Licença

Este projeto está licenciado sob a **Licença MIT** — veja o arquivo [LICENSE](LICENSE).

---

## Créditos

Comunidade de **Blue Team**, analistas de **SOC** e pesquisadores que documentam técnicas de ofuscação de forma responsável. Feito com foco em transparência e utilidade para quem defende redes.