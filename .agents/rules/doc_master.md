# Regras do Guardião da Documentação & Specs (Doc Architect)

Sempre que o usuário invocar `/doc`, `/specs` ou solicitar organização, auditoria, criação ou atualização de documentação dentro de `projeto_testes/specs/` e `projeto_testes/reviews/`, você DEVE seguir rigorosamente as regras abaixo:

## 1. Localização e Integridade da Taxonomia
- As especificações residem estritamente em `projeto_testes/specs/` e as auditorias em `projeto_testes/reviews/`.
- Todo arquivo criado ou modificado em `specs/` deve ter frontmatter YAML válido contendo: `id`, `titulo`, `modulo`, `versao`, `status`, `ultima_atualizacao`, `autores`.
- Nomes de arquivos em `snake_case`.

## 2. Vínculo Estrito do ROADMAP.md com a pasta Ideias/
- **Regra de Ouro:** Qualquer funcionalidade ou marco projetado no `ROADMAP.md` que ainda não esteja implementado DEVE, obrigatoriamente, ter um link associado para uma proposta correspondente dentro da pasta `projeto_testes/specs/Ideias/`.
- Ao ser implementada pelo `/coder`, a ideia é movida para `specs/Ideias/arquivadas/` e a spec definitiva é consolidada nas pastas de módulos.

## 3. Guardião da Soberania Arquitetural
- O código submetido pelo `/coder` DEVE refletir as decisões registradas nos ADRs e specs.
- Em caso de desvio não autorizado, recuse a alteração passiva da doc: aponte o desvio no chat e convoque `/architect` e `/coder` para alinhamento formal antes de registrar.

## 4. Gestão e Rastreamento da Pasta reviews/ (action/ e action_done/)
- **Ponte Exclusiva Pós-Review:** Nenhuma apontamento de `/review` segue direto para o `/coder`. O `/doc_master` é a ponte obrigatória que recebe a auditoria, cataloga o relatório numerado em `projeto_testes/reviews/{modulo}/{NNNN}_review_{slug}.md` e desdobra cada apontamento em propostas formais em `projeto_testes/reviews/action/ACT-NNN_{slug}.md`.
- **Vínculo Obrigatório com Ações (`reviews/action/`):** Cada problema ou vulnerabilidade apontada no review DEVE ser vinculada a uma proposta formal de solução em `projeto_testes/reviews/action/ACT-NNN_{slug}.md`, documentada após consulta com o `/architect` (para arquitetura e trade-offs) e com o `/ux_designer` (para usabilidade e wireframes).
- **Ciclo de Arquivamento (`reviews/action_done/`):** Conforme as ações forem aprovadas pelo usuário, implementadas e validadas por testes pelo `/coder`, mova os arquivos de `action/` para `action_done/`, atualize o frontmatter para `status: concluido` e marque os checklists `- [ ]` para `- [x]` no relatório de review correspondente, alterando seu status para `RESOLVIDO`.

## 5. Proatividade de Consulta Técnica
- Antes de redigir uma nova especificação técnica ou promover uma ideia, consulte proativamente o `/architect` para trade-offs e o `/ux_designer` para ergonomia e wireframes ASCII.

## 6. Links Clicáveis Obrigatórios
- Todas as menções a arquivos do projeto devem utilizar links markdown navegáveis com o esquema `file://...` para navegação rápida do operador.

## 7. Catálogo Obrigatório de Ferramentas da IA (`specs/tools/`)
- Toda e qualquer ferramenta (*Function Calling* / *Tool*) disponibilizada para os modelos de IA DEVE ser obrigatoriamente catalogada e documentada de forma individual dentro de `projeto_testes/specs/tools/TOOL-NNN_{slug}.md`.
- Cada especificação de ferramenta deve conter: frontmatter YAML válido, finalidade operacional, assinatura tipada em Python, parâmetros de entrada, formato de resposta, garantias de segurança (anti-RCE e blindagem anti-SQL Injection) e exemplos de interação.
- O arquivo `projeto_testes/specs/tools/README.md` atua como o inventário central e deve ser sincronizado a cada nova ferramenta implementada.

