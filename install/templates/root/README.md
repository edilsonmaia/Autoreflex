# Autoreflex

Projeto local para criação e consulta de skills Markdown com busca semântica via Qdrant.

## Instalação
1. Abra a raiz do repositório.
2. Rode `python install/install.py` dentro de um venv Python 3.12.
3. O instalador cria o runtime, a pasta `skills/`, o `.env` e o modelo local.
4. O instalador sobe um runtime Qdrant compatível em `{{QDRANT_URL}}`.

## Uso
- O servidor sobe localmente em `{{SERVER_ADDRESS}}`.
- A pesquisa de skills fica em `{{SKILLS_SEARCH_URL}}`.
- A leitura de skill fica em `{{SKILLS_GET_URL}}`.
- O runtime Qdrant também sobe junto e funciona em Windows e Linux.
- O fluxo principal é consultar skills primeiro e reutilizar conhecimento já salvo.
