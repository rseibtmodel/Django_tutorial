# Template do Resumo Executivo da Entrega

Utilize este modelo para registrar as entregas concluídas em `docs/entregas/{YYMMDDNN}_resumo_executivo_{slug_entrega}.md` (ou `{0001}_resumo_executivo_{slug_entrega}.md`).

```markdown
# Resumo Executivo: [Nome da Funcionalidade / Entrega]

## 1. Escopo & ADRs Atendidas
- **Objetivo da Entrega:** [Resumo claro da funcionalidade implementada]
- **ADRs de Referência:** [Links ou identificadores das ADRs respeitadas, ex: ADR-002: Service/Selector Architecture]
- **Decisões Técnicas:** [Principais escolhas implementadas em conjunto com o time]

## 2. Mapa de Arquivos
- `caminho/para/arquivo.py`: [Criado | Modificado | Removido] — [Descrição sucinta da responsabilidade ou alteração]
- `caminho/para/tests/test_arquivo.py`: [Criado] — [Cobertura de testes implementada]

## 3. Roteiro de Execução Local & Testes
```bash
# 1. Aplicar migrações pendentes
python manage.py makemigrations
python manage.py migrate

# 2. Executar a suíte de testes da entrega
python manage.py test nome_do_app.tests
```

## 4. Pontos de Atenção para Deploy & Produção
- **Variáveis de Ambiente:** [Novas chaves adicionadas ao .env ou 'Nenhuma']
- **Migrações de Banco:** [Impacto no schema, bloqueio de tabelas ou necessidade de retrocompatibilidade]
- **Dependências Externas:** [Novos pacotes instalados com autorização prévia ou 'Nenhum']
- **Riscos Operacionais:** [Avisos sobre caching, background workers ou volumetria]
```
