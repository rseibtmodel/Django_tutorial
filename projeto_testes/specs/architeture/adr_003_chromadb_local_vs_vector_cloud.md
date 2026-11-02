# 🏛️ ADR 003: ChromaDB Local Persistente vs. Vector Databases em Nuvem

- **Status:** Aprovado & Implementado (com plano de evolução)
- **Decisores:** Arquiteto de Software, Tech Lead
- **Data:** 31/10/2026

---

## 1. Contexto & Problema
A implementação de RAG e memória semântica exige armazenamento e busca por similaridade vetorial (cosseno/HNSW). As opções comerciais em nuvem (Pinecone, Qdrant Cloud, Weaviate Cloud) agregam custos de assinatura, latência de rede extra e complexidade de chaves de API adicionais.

---

## 2. Decisão Arquitetural
- **Para a Fase de MVP / Desenvolvimento Atual:**
  Adotar o **ChromaDB Local com armazenamento persistente em disco (`PersistentClient`)**.
  - Custo zero de infraestrutura.
  - Baixa latência por operar em memória/disco local (`projeto_testes/chroma_data`).
  - Sem necessidade de serviços externos em execução na máquina do desenvolvedor.
- **Plano de Evolução para Produção (Roadmap):**
  Migrar a persistência vetorial para **PostgreSQL com a extensão `pgvector`**, unificando as tabelas relacionais do Django e os vetores na mesma transação ACID.

---

## 3. Consequências & Trade-offs
- **Positivas:**
  - Setup imediato: `pip install chromadb` e persistência local pronta.
  - Independência de serviços em nuvem para desenvolvimento.
- **Negativas / Limitações:**
  - O ChromaDB local com SQLite/DuckDB subjacente não é projetado para concorrência multi-processo de alta escala (ex: Gunicorn com dezenas de workers em processos de SO separados).

