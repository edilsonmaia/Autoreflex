# Memória operacional do projeto Autoreflex

Este arquivo é criado pelo instalador e serve como instrução base do agente no repositório.

## Servidor local para consultar habilidades para o agente
- Endereço base: `{{SERVER_ADDRESS}}`
- URL de pesquisa de skills: `{{SKILLS_SEARCH_URL}}`
- Endpoint de skills: `{{SKILLS_SEARCH_URL}}`
- Endpoint de leitura da skill completa: `{{SKILLS_GET_URL}}`
- Use `POST /agent/skills/search` com `{"query":"criar novas skills"}`.
- Use `POST /agent/skills/get` com `{"skill_path":"criar_novas_skills.md"}`.

## Ordem de decisão
1. Usar a memória já presente na conversa.
2. Se não houver resposta suficiente, consultar skills relevantes via endpoint.
3. Se a skill apontar arquivo, função ou linha, seguir isso antes de abrir arquivos grandes.
4. Só depois pesquisar o código do projeto.
5. Se qualquer `curl` para `127.0.0.1:8090` falhar, interrompa a execução imediatamente.
6. A falha no endpoint de skills é uma condição de bloqueio.
7. Sem confirmação do usuário, o agente não pode executar nenhuma ação subsequente relacionada à tarefa.
8. Não tente procurar skills no diretório local, usar caminhos alternativos, inferir indisponibilidade ou continuar a tarefa por outra rota.
9. Antes de qualquer outra ação, informe o erro exato ao usuário e pergunte se ele lhe deu permissões de rede.
10. Se o usuário não permitiu rede antes, o agente não tem acesso à rede.

## Regra principal
- Responder e consultar endpoints sempre na língua do usuário.
- O agente deve consultar skills primeiro para economizar tokens.
- A primeira skill a ler ao criar novas skills é a skill base de criação.
- Termo inicial de busca: `criar novas skills`.
- Sequência operacional: buscar -> ler skill completa -> criar nova skill -> indexar.
- Depois da busca, se houver correspondência útil, ler a skill completa pelo endpoint de leitura.
- Quando uma nova skill for salva, o agente deve chamar `POST /agent/skills/index`.
- O cache local de skills usa o score da busca vetorial como filtro de relevância.
- Não listar nem usar resultados com score abaixo de `0.65500000`, que é o padrão.
- O score é um float de similaridade; o `.env` o preserva com 8 casas decimais para manter consistência visual e operacional.
- Toda skill nova deve ser criada com `skills/<nome>.md` e `skills/<nome>.meta.json`.
- O metadata deve conter `name`, `title`, `summary`, `tags`, `language`, `source_skill_path`, `created_at`, `updated_at` e `version`.
- Quando o metadata existir, use-o como atalho de classificação antes de ler a skill completa.
