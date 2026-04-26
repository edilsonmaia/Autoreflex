# Autoreflex

> Servidor local de skills com busca semântica para agentes de IA — projetado para reduzir o consumo de tokens e tornar o conhecimento do agente reutilizável entre sessões.

[![License](https://img.shields.io/badge/license-AutoReflex%20Community-blue)](LICENSE.txt)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey)]()
[![Status](https://img.shields.io/badge/status-active-success)]()

---

## Sumário

- [Sobre](#sobre)
- [Por que Autoreflex](#por-que-autoreflex)
- [Casos de uso](#casos-de-uso)
- [Arquitetura](#arquitetura)
- [Requisitos](#requisitos)
- [Instalação rápida](#instalação-rápida)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Configuração](#configuração)
- [Endpoints da API](#endpoints-da-api)
- [Sistema de skills](#sistema-de-skills)
- [Fluxo operacional do agente](#fluxo-operacional-do-agente)
- [Logs](#logs)
- [Reparo e reinstalação](#reparo-e-reinstalação)
- [Compatibilidade](#compatibilidade)
- [Solução de problemas](#solução-de-problemas)
- [Licença](#licença)
- [Autor e mantenedora](#autor-e-mantenedora)

---

## Sobre

**Autoreflex** é um servidor local que cria, indexa e consulta *skills* — pequenas unidades de conhecimento em Markdown — usando busca semântica vetorial. Ele serve como **memória persistente externa** para agentes de IA: em vez de reprocessar todo o histórico de uma tarefa a cada nova sessão, o agente consulta apenas a skill relevante e continua de onde parou, com contexto limpo.

O sistema sobe localmente com FastAPI, usa o Qdrant como base vetorial e o modelo `google/embeddinggemma-300m` (configurável) para gerar embeddings.

---

## Por que Autoreflex

Em sessões longas com agentes de IA, o contexto satura, o custo cresce e a performance degrada. O Autoreflex resolve isso transformando o conhecimento já produzido em skills indexadas que ficam disponíveis para qualquer nova sessão.

- **Redução de 85,47% no consumo de tokens** em inícios de sessão, ao trocar histórico extenso por consulta dirigida a skills.
- **Reuso entre sessões**: o que foi resolvido uma vez vira skill consultável.
- **Busca semântica**: o agente encontra a skill certa mesmo sem saber o nome do arquivo.
- **100% local**: nenhuma dependência de SaaS, modelo e índice rodam na sua máquina.
- **Multiplataforma**: Windows e Linux, sem Docker.

---

## Casos de uso

O Autoreflex não serve apenas para sessões interativas de chat. Ele se torna especialmente poderoso quando agentes são **acionados programaticamente por eventos externos** — um webhook, um cron, um alerta de monitoramento, um ticket novo. O agente acorda, consulta a skill certa para aquele contexto, age, e ao terminar grava novas skills sobre o que aprendeu. Com o tempo, cada agente se torna mais capaz sem precisar de treinamento adicional.

Abaixo estão cenários reais (marcados como "em uso real") e possibilidades validadas pela arquitetura do sistema:

### 🔒 Segurança e resposta a incidentes

Um monitor de infraestrutura detecta um volume anormal de requisições em portas inesperadas e aciona o agente. O agente consulta uma skill de endurecimento de segurança, que contém os passos para: analisar logs do firewall, identificar padrões de ataque, bloquear IPs suspeitos e reforçar regras de rede. Ao terminar, ele cria uma nova skill com o incidente documentado — tipo de ataque, IPs envolvidos, medidas aplicadas — para que a próxima vez a resposta seja ainda mais rápida. Cada ataque mitigado torna o agente mais preparado.

### 🎫 Automação de tickets de suporte (em uso real)

Um novo ticket de cliente chega ao sistema. O agente é disparado automaticamente: lê a descrição do chamado, analisa prints e evidências anexadas, localiza o bug no código, corrige, roda os testes e responde ao cliente com a resolução — fechando o ticket sem intervenção humana. As correções e padrões de bug encontrados viram skills indexadas, acelerando a resolução de chamados futuros semelhantes.

### 📊 Monitoramento e relatórios automatizados

Um cron job aciona o agente no fim de cada dia. Ele consulta skills que descrevem a estrutura dos dashboards e as métricas esperadas, coleta dados de APIs internas, monta o relatório e envia para a equipe. Se uma métrica sair do esperado, ele consulta skills de diagnóstico e já inclui a análise de causa raiz no relatório.

### 🚀 CI/CD e qualidade de código

O pipeline de CI dispara o agente quando um merge request é aberto. O agente busca skills de padrões de código do projeto, review guidelines e regras de arquitetura. Ele analisa o diff, aponta inconsistências, sugere correções e comenta diretamente no merge request. Se encontrar um padrão novo recorrente, cria uma skill para que revisões futuras já cubram aquele caso.

### 🏗️ Onboarding de desenvolvedores

Um novo membro entra no time. Em vez de ler dezenas de documentos dispersos, o agente já tem indexadas as skills de setup do ambiente, padrões do projeto, fluxos de deploy, credenciais necessárias e decisões arquiteturais passadas. O novo desenvolvedor pergunta ao agente e recebe respostas contextualizadas — sem precisar interromper colegas.

### 📦 Gestão de infraestrutura e runbooks

O agente carrega skills com os runbooks operacionais: como escalar serviços, procedimentos de rollback, configuração de novos nós e verificações de saúde. Quando um alerta do Prometheus ou Grafana dispara, o agente consulta o runbook correto e executa o procedimento ou orienta o operador passo a passo. Se o procedimento precisar de ajustes, a skill é atualizada automaticamente.

### 🌐 Provisioning de servidores web (em uso real)

O agente recebe o pedido de configurar um novo servidor. Ele consulta skills com os passos completos de instalação — Apache ou Nginx, configuração de vhosts, hardening de SSL/TLS, ajuste de permissões, instalação e configuração de cPanel/WHM, criação de contas, configuração de DNS interno e backup. Cada etapa já documentada em skill é executada sem retrabalho. Quando um servidor apresenta particularidade nova (versão diferente de OS, painel alternativo, regra de firewall específica), o agente documenta como nova skill e a próxima instalação já contempla aquele cenário. O resultado é que provisionar um servidor completo, que antes levava horas de trabalho manual, passa a ser uma sequência automatizada e auditável.

### 🧪 Testes e validação contínua

O agente é acionado após cada deploy. Ele consulta skills com cenários de teste e validações esperadas, executa testes de smoke, verifica endpoints críticos e compara respostas com baselines documentados. Se algo divergir, grava uma skill com o desvio encontrado e notifica a equipe.

### 💬 Atendimento inteligente multicanal

Mensagens chegam por chat, e-mail ou WhatsApp. O agente é acionado por cada mensagem nova, consulta skills de atendimento (políticas de troca, prazos, FAQ, processos internos), responde ao cliente e escala para humano apenas o que realmente precisa de decisão manual. Cada resolução nova alimenta a base de skills para os próximos atendimentos.

### 🔄 Automação de processos de negócio

Eventos de negócio disparam o agente: uma nota fiscal emitida, um pedido aprovado, um contrato assinado. O agente consulta skills com os fluxos de cada processo, executa as ações subsequentes (atualizar planilhas, disparar e-mails, gerar documentos) e documenta exceções como novas skills quando o fluxo esperado não funciona.

### 🗄️ Migração e manutenção de bancos de dados

O agente é acionado para migrar dados entre ambientes ou versões de banco. Ele consulta skills com os schemas esperados, scripts de migração já validados, verificações de integridade e rollback procedures. Durante a execução, compara contagens, valida constraints e registra divergências. Se o schema do destino tiver mudanças inesperadas, documenta como nova skill para migrações futuras.

### 📋 Auditoria e conformidade

Periodicamente, o agente percorre a infraestrutura verificando conformidade com políticas internas: permissões de acesso, certificados próximos do vencimento, versões de dependências com CVEs conhecidos, configurações de backup. Ele consulta skills com os critérios de cada auditoria e gera um relatório de conformidade. Itens fora do padrão viram skills de correção para a próxima rodada.

### 📚 Documentação viva do projeto

A cada pull request mergeado, o agente é acionado, analisa as mudanças e atualiza as skills de documentação afetadas — arquitetura, fluxos, APIs, decisões técnicas. A documentação nunca defasa porque acompanha o código. Desenvolvedores novos encontram documentação sempre atualizada sem que alguém precise lembrar de atualizá-la manualmente.

### 🧠 Construção progressiva de conhecimento

A característica que diferencia o Autoreflex de outras soluções é que **cada execução pode gerar novas skills**. O agente não apenas consome conhecimento — ele produz. Com o tempo, a base de skills cresce organicamente e reflete a realidade operacional do projeto, criando uma espécie de memória institucional que não depende de nenhum indivíduo específico.

> **A ideia central é simples:** qualquer evento que acione um agente pode ser enriquecido com conhecimento prévio (skills de leitura) e gerar conhecimento novo (skills de escrita). O Autoreflex é a infraestrutura que viabiliza esse ciclo.

---

## Arquitetura

```
┌──────────────────────────────────────────────────────────────┐
│                         Agente de IA                         │
└─────────────────────────────┬────────────────────────────────┘
                              │ HTTP (127.0.0.1:8090)
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                FastAPI · /agent/skills/*                     │
│   search · get · index · health                              │
└─────────┬──────────────────────────────────────┬─────────────┘
          │                                      │
          ▼                                      ▼
┌────────────────────────┐        ┌──────────────────────────────┐
│  Embedding Model       │        │   Qdrant runtime local       │
│  EmbeddingGemma-300m   │        │   127.0.0.1:6333             │
│  (Torch / HF)          │        │   Coleção: skills_*          │
└────────────────────────┘        └──────────────────────────────┘
                                          │
                                          ▼
                                  ┌────────────────┐
                                  │   skills/*.md  │
                                  │  *.meta.json   │
                                  └────────────────┘
```

- **API principal** (`app/main.py`) — FastAPI rodando em `http://127.0.0.1:8090`.
- **Runtime Qdrant local** (`app/qdrant_runtime.py`) — vetorial em `http://127.0.0.1:6333`.
- **Instalador** (`install/install.py`) — bootstrap de venv, dependências, modelo e diretórios.
- **Skills** — arquivos Markdown em `skills/` com metadata JSON ao lado.

---

## Requisitos

| Item                     | Versão / Observação                              |
| ------------------------ | ------------------------------------------------ |
| Python                   | 3.12 ou superior                                 |
| Arquitetura              | `x86_64` ou `arm64`                              |
| Sistema operacional      | Windows 10+ ou Linux                             |
| Conta Hugging Face       | Necessária se o modelo ainda não estiver baixado |
| GPU (opcional)           | CUDA detectado automaticamente pelo instalador   |
| Docker                   | **Não** é necessário                             |

---

## Instalação rápida

### Windows

```powershell
# 1. Clone o repositório
git clone https://github.com/<seu-usuario>/autoreflex.git
cd autoreflex

# 2. (Opcional) Crie e ative uma venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Rode o instalador
python install\install.py
```

### Linux

```bash
# 1. Clone o repositório
git clone https://github.com/<seu-usuario>/autoreflex.git
cd autoreflex

# 2. (Opcional) Crie e ative uma venv
python3.12 -m venv .venv
source .venv/bin/activate

# 3. Rode o instalador
python install/install.py
```

### Menu do instalador

Ao executar `install.py`, três opções aparecem:

1. **Instalar do zero** — cria toda a estrutura, baixa o modelo e sobe o servidor.
2. **Rodar sistema já instalado** — inicia a API quando tudo já está montado.
3. **Reparar instalação** — repete os passos para corrigir uma instalação inconsistente.

> Na primeira execução, se o modelo de embeddings ainda não estiver baixado, o instalador **vai pedir o token do Hugging Face**. Cole o token; ele será salvo em `.env` automaticamente.

Ao final, a API fica acessível em `http://127.0.0.1:8090`.

---

## Estrutura do projeto

```
autoreflex/
├── app/                    # Runtime do servidor
│   ├── main.py             # Entrada da API FastAPI
│   ├── qdrant_runtime.py   # Runtime local compatível com Qdrant
│   └── config.py           # Carregamento de configuração
├── install/
│   ├── install.py          # Instalador interativo
│   ├── config.py           # Configuração central e templates
│   ├── logging_utils.py    # Logging rotativo
│   └── requirements.txt    # Dependências
├── skills/                 # Skills em Markdown + metadata JSON
├── models/                 # Modelo local de embeddings
├── logs/                   # Logs persistentes
├── .env                    # Configuração local (gerado)
├── agents.md               # Memória operacional do agente
├── LICENSE.txt
└── README.md
```

---

## Configuração

Toda a configuração mora em `.env`, gerado pelo instalador. Os principais valores:

### Servidor

| Variável         | Padrão              | Descrição                          |
| ---------------- | ------------------- | ---------------------------------- |
| `AGENT_HOST`     | `127.0.0.1`         | Host da API                        |
| `AGENT_PORT`     | `8090`              | Porta da API                       |
| `UVICORN_RELOAD` | `0`                 | Reload automático do uvicorn       |

### Qdrant

| Variável                    | Padrão                       | Descrição                  |
| --------------------------- | ---------------------------- | -------------------------- |
| `QDRANT_URL`                | `http://127.0.0.1:6333`      | URL do Qdrant              |
| `QDRANT_PATH`               | `./.qdrant`                  | Storage local              |
| `QDRANT_COLLECTION_PREFIX`  | `org`                        | Prefixo das coleções       |
| `EMBEDDING_DIMENSION`       | `768`                        | Dimensão dos vetores       |
| `VECTOR_DISTANCE`           | `Cosine`                     | Métrica de distância       |

### Modelo de embeddings

| Variável                   | Padrão                          | Descrição                         |
| -------------------------- | ------------------------------- | --------------------------------- |
| `EMBEDDING_MODEL_ID`       | `google/embeddinggemma-300m`    | Repositório no Hugging Face       |
| `EMBEDDING_MODEL_REVISION` | `main`                          | Revisão do modelo                 |
| `EMBEDDING_MODEL_PATH`     | `./models/gemma`                | Pasta local do modelo             |
| `EMBEDDING_DEVICE`         | `auto`                          | `auto`, `cpu` ou `cuda`           |
| `EMBEDDING_BACKEND`        | `torch`                         | Backend de inferência             |
| `HF_TOKEN`                 | —                               | Token do Hugging Face             |

### Skills

| Variável                    | Padrão           | Descrição                          |
| --------------------------- | ---------------- | ---------------------------------- |
| `SKILLS_DIR`                | `./skills`       | Diretório das skills               |
| `SKILLS_COLLECTION_PREFIX`  | `skills`         | Prefixo da coleção                 |
| `SKILLS_COLLECTION_KEY`     | `global_default` | Chave lógica da coleção            |
| `SKILLS_MIN_SCORE`          | `0.65500000`     | Score mínimo de relevância         |
| `SKILLS_CHUNK_SIZE`         | `150`            | Tamanho dos chunks                 |
| `SKILLS_CHUNK_OVERLAP`      | `20`             | Sobreposição entre chunks          |

### Rate limit e logs

| Variável                       | Padrão | Descrição                         |
| ------------------------------ | ------ | --------------------------------- |
| `RATE_LIMIT_REQUESTS`          | `30`   | Requisições por intervalo         |
| `RATE_LIMIT_INTERVAL_SECONDS`  | `60`   | Janela do rate limit              |
| `SKILLS_GET_LIMIT`             | `3`    | Limite de leituras de skill       |
| `ENABLE_METRICS`               | `1`    | Métricas habilitadas              |
| `ENABLE_REQUEST_LOGS`          | `0`    | Log de requisições (opt-in)       |
| `LOG_LEVEL`                    | `INFO` | Nível de log                      |

---

## Endpoints da API

### `GET /health`

Status do serviço.

```bash
curl http://127.0.0.1:8090/health
```

### `POST /agent/skills/search`

Busca semântica nas skills indexadas.

```bash
curl -X POST http://127.0.0.1:8090/agent/skills/search \
  -H "Content-Type: application/json" \
  -d '{"query": "criar novas skills"}'
```

Apenas resultados com score acima de `SKILLS_MIN_SCORE` (padrão `0.65500000`) são retornados.

### `POST /agent/skills/get`

Lê o conteúdo completo de uma skill pelo caminho.

```bash
curl -X POST http://127.0.0.1:8090/agent/skills/get \
  -H "Content-Type: application/json" \
  -d '{"skill_path": "criar_novas_skills.md"}'
```

### `POST /agent/skills/index`

Reindexa uma skill específica ou todas as skills do diretório.

```bash
# Indexar uma skill específica
curl -X POST http://127.0.0.1:8090/agent/skills/index \
  -H "Content-Type: application/json" \
  -d '{"skill_path": "skills/minha_skill.md"}'

# Reindexar tudo
curl -X POST http://127.0.0.1:8090/agent/skills/index \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## Sistema de skills

Toda skill é composta por **dois arquivos** em `skills/`:

### 1. Conteúdo: `skills/<nome>.md`

```markdown
# Título no idioma do usuário

## Resumo curto
Explique o problema e a solução em poucas linhas.

## Quando usar
Descreva em que situação essa skill deve ser consultada.

## Instruções
1. Passo um.
2. Passo dois.
3. Passo três.

## Arquivos relevantes
- `app/main.py`
- `install/install.py`

## Observações
Detalhes importantes, limites e cuidados.
```

### 2. Metadata: `skills/<nome>.meta.json`

```json
{
  "name": "nome-da-skill",
  "title": "Título no idioma do usuário",
  "summary": "Resumo curto da skill",
  "tags": ["tag1", "tag2", "tag3"],
  "language": "pt-BR",
  "source_skill_path": "skills/nome-da-skill.md",
  "created_at": "2026-04-26T10:00:00-03:00",
  "updated_at": "2026-04-26T10:00:00-03:00",
  "version": 1
}
```

**Regras do metadata:**

- `summary` curto e direto.
- `tags` com 3 a 8 termos úteis.
- `version` começa em `1` e incrementa a cada alteração.
- `updated_at` atualizado a cada edição.
- O metadata serve como atalho de classificação **antes** de o agente ler a skill completa.

---

## Fluxo operacional do agente

A ordem de decisão recomendada (e replicada em `agents.md`):

1. **Usar o contexto da conversa atual.**
2. Se não bastar, consultar `POST /agent/skills/search`.
3. Se houver match útil, ler a skill completa via `POST /agent/skills/get`.
4. Se a skill apontar arquivo, função ou linha, **seguir a referência** antes de abrir arquivos grandes.
5. Só depois, navegar pelo código do projeto.
6. Ao resolver algo novo e reutilizável, criar uma nova skill em `skills/<nome>.md` + `<nome>.meta.json` e chamar `POST /agent/skills/index`.

> **Idioma**: respostas e consultas devem sempre estar na língua do usuário.

---

## Logs

A pasta `logs/` é parte da operação, não decorativa. Todos os logs são rotacionados (5 MB × 5 backups).

| Arquivo                    | Conteúdo                          |
| -------------------------- | --------------------------------- |
| `logs/runtime.log`         | Fluxo da API principal            |
| `logs/runtime.error.log`   | Erros do runtime principal        |
| `logs/qdrant.log`          | Runtime local do Qdrant           |
| `logs/qdrant.error.log`    | Erros do Qdrant local             |
| `logs/installer.log`       | Fluxo do instalador               |
| `logs/installer.error.log` | Erros do instalador               |

Os logs também aparecem no console em tempo real.

---

## Reparo e reinstalação

Quando a instalação ficar inconsistente:

```bash
python install/install.py
# escolha: 3) Reparar instalação
```

A opção repete os passos de estrutura, dependências, `.env`, modelo e validação sem apagar suas skills.

---

## Compatibilidade

- O instalador detecta o sistema operacional automaticamente.
- Em Windows usa `Scripts/`, em Linux usa `bin/` para a venv.
- A camada de busca foi ajustada para funcionar com clientes Qdrant que expõem `query_points` **e** com versões antigas que ainda usam `search`.
- O runtime do Qdrant local sobe e funciona nos dois sistemas sem Docker.

---

## Solução de problemas

| Sintoma                                                | Causa provável                              | Ação                                                                          |
| ------------------------------------------------------ | ------------------------------------------- | ----------------------------------------------------------------------------- |
| Instalador pede token do HF                            | Modelo local ausente                        | Cole um token válido — fica salvo no `.env`                                   |
| `uvicorn` não encontrado                               | Dependências não instaladas                 | Rode opção 3 (Reparar instalação)                                             |
| `curl 127.0.0.1:8090` falha                            | Servidor não subiu ou porta bloqueada       | Verifique `logs/runtime.error.log` e permissões de rede                       |
| Score sempre abaixo do limite                          | `SKILLS_MIN_SCORE` muito alto               | Ajuste o valor no `.env` (padrão `0.65500000`)                                |
| Erro de API do `qdrant-client` na busca                | Versão incompatível                         | A camada já trata fallback `query_points → search`; atualize o `qdrant-client`|

---

## Licença

Distribuído sob a **Licença AutoReflex – Uso e Distribuição Comunitária**. Consulte [`LICENSE.txt`](LICENSE.txt) para os termos completos.

Em resumo:

- Uso pessoal e comercial é permitido.
- Atribuição obrigatória: criador, e-mail, projeto, mantenedora e site devem permanecer visíveis.
- **Copyleft parcial**: melhorias no núcleo do Autoreflex devem ser compartilhadas publicamente sob esta mesma licença.
- É permitido vender produtos comerciais que usem o Autoreflex como componente, desde que a parte derivada do Autoreflex permaneça livre e acessível.
- Software fornecido "como está", sem garantias.

---

## Autor e mantenedora

**Edilson Maia Favero**
- E-mail: [edilson.tec@hotmail.com](mailto:edilson.tec@hotmail.com)
- Projeto: **AutoReflex**
- Mantenedora: **Costafavero — Tecnologia, Comércio e Serviços LTDA**
- Site: [costafavero.com.br](https://costafavero.com.br)

---

## Tecnologias relacionadas (Costafavero)

Para cenários de **missão crítica** que exigem fidelidade determinística e zero alucinação, a Costafavero mantém tecnologias complementares ao Autoreflex:

- **QVR Engram** — motor de processamento determinístico (0,00% de interferência) para problemas de alta complexidade em hardware padrão. [projetoqvr.com.br](https://projetoqvr.com.br)
- **Esensor** — camada de sensoriamento semântico e triagem neuroestimulada para defesa, análise de logs em tempo real e endurecimento de segurança.

Para integração em infraestruturas de defesa, automação industrial ou sistemas de alta disponibilidade, contate o e-mail acima.

---

> Se este projeto te ajudou, considere dar uma ⭐ no repositório e compartilhar com quem trabalha com agentes de IA.
