# Criar novas skills

## Objetivo
Criar skills novas quando o problema for reutilizável e valha a pena ser consultado de novo.

## Ordem de trabalho
1. Use sua memória de contexto primeiro.
2. Se não houver resposta suficiente, consulte `POST /agent/skills/search`.
3. Se uma skill existente resolver, reutilize-a.
4. Se não houver skill adequada, leia os arquivos necessários do projeto.
5. Depois de resolver, crie a nova skill em `skills/<nome-da-skill>.md` e o metadata em `skills/<nome-da-skill>.meta.json`.
6. Salve os dois arquivos.
7. Execute `POST /agent/skills/index` com o caminho da skill recém-criada.
8. Só então siga para a próxima tarefa.

## Formato exato da nova skill
Use o idioma do usuário no nome do arquivo e no título Markdown. O formato deve ser este:

```md
# Título no idioma do usuário

## Resumo curto
Explique o problema e a solução em poucas linhas.

## Quando usar
Descreva em que situação essa skill deve ser consultada.

## Instruções
Liste os passos objetivos para resolver o problema novamente.

## Metadados
Crie um arquivo `skills/<nome-da-skill>.meta.json` com metadados curtos e estáveis para facilitar busca, cache e reutilização.
{
  "name": "nome-da-skill",
  "title": "Título no idioma do usuário",
  "summary": "Resumo curto da skill",
  "tags": ["tag1", "tag2"],
  "language": "pt-BR",
  "source_skill_path": "skills/nome-da-skill.md",
  "created_at": "YYYY-MM-DDTHH:MM:SS-03:00",
  "updated_at": "YYYY-MM-DDTHH:MM:SS-03:00",
  "version": 1
}

Regras:
- mantenha `summary` curto;
- use `tags` com 3 a 8 termos úteis;
- inicie `version` em `1` e atualize quando a skill mudar;
- atualize `updated_at` sempre que editar a skill;
- use o metadata para classificar a skill antes de depender só do conteúdo completo.

## Arquivos relevantes
- `app/main.py`
- `install/install.py`

## Observações
Inclua detalhes importantes, limites e cuidados.
```

## Indexação obrigatória
Depois de salvar a skill, indexe imediatamente com o caminho relativo dentro de `skills/`:

```json
{
  "skill_path": "skills/nome-da-skill.md"
}
```

Se quiser reindexar tudo:

```json
{}
```
