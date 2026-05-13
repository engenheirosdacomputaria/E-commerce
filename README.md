# Ecommerce
Projeto da matéria de banco de dados não relacionais

# Especificação de Mudança — Redis
**Banco de Dados Não Relacionais | Projeto base com Redis**

---

## 4.1 Identificação

**Grupo:**
**Integrantes:**

---

## 4.2 Análise das Demandas

### Demanda 1 — Consulta rápida de produtos
**Problema resolvido:** Toda consulta de produto por ID acessa o SQLite diretamente. Quando o mesmo produto é consultado várias vezes seguidas, o banco relacional é acionado de forma desnecessária. O Redis entra como cache intermediário para absorver essas leituras repetidas, reduzindo a carga sobre o SQLite.

### Demanda 2 — Carrinho temporário de compras
**Problema resolvido:** Antes de finalizar um pedido, o cliente monta uma seleção de produtos e quantidades. Esse estado não deve ser persistido no banco principal enquanto o pedido não é confirmado. O Redis oferece uma estrutura leve e temporária para guardar esse carrinho de forma isolada por cliente.

### Demanda 3 — Produtos mais consultados
**Problema resolvido:** O sistema não registra quais produtos são mais acessados. Sem esse dado, o gestor não consegue identificar o interesse dos clientes. O Redis permite acumular e ordenar contagens de consulta em tempo real, sem custo de escrita no banco principal.

---

## 4.3 Técnica Redis Escolhida

### Demanda 1 — Cache com String JSON + TTL
**Técnica:** String com JSON + TTL (`SETEX` / `GET`)

**Justificativa:** O produto é um objeto com poucos campos (nome, preço, estoque). Serializar em JSON e armazenar em uma String é simples e eficiente. O TTL garante que dados desatualizados expirem automaticamente, sem necessidade de invalidação manual em cenários básicos. Essa é a técnica clássica de cache-aside, já demonstrada na PoC do professor.

### Demanda 2 — Carrinho com Hash + TTL
**Técnica:** Hash (`HSET` / `HGETALL`) + TTL (`EXPIRE`)

**Justificativa:** O carrinho é um conjunto de pares `id_produto → quantidade` associados a um cliente. O Hash do Redis representa exatamente essa estrutura: cada campo do Hash é um produto, e o valor é a quantidade. Permite adicionar, consultar e remover itens individualmente sem reescrever o carrinho inteiro. O TTL descarta carrinhos abandonados automaticamente.

### Demanda 3 — Ranking com Sorted Set
**Técnica:** Sorted Set (`ZINCRBY` / `ZREVRANGE`)

**Justificativa:** O Sorted Set mantém elementos ordenados por pontuação de forma nativa. Cada produto é um membro; cada consulta incrementa sua pontuação. A consulta do ranking já vem ordenada do maior para o menor sem necessidade de ordenação na aplicação. É a estrutura ideal para rankings em tempo real.

---

## 4.4 Padrão das Chaves Redis

### Demanda 1

| Chave | `dev:ecommerce:produto:cache:{id_produto}` |
|---|---|
| **Representa** | Cache dos dados de um produto específico |
| **Dado armazenado** | JSON com `id_produto`, `nome`, `preco_atual`, `estoque_total` |
| **TTL** | Sim — 60 segundos |

Exemplo: `dev:ecommerce:produto:cache:3`

---

### Demanda 2

| Chave | `dev:ecommerce:carrinho:cliente:{id_cliente}` |
|---|---|
| **Representa** | Carrinho temporário de um cliente |
| **Dado armazenado** | Hash com campos `produto:{id_produto}` e valor `quantidade` |
| **TTL** | Sim — 900 segundos (15 minutos) |

Exemplo: `dev:ecommerce:carrinho:cliente:5`
Campos do Hash: `produto:2 → 1`, `produto:7 → 3`

---

### Demanda 3

| Chave | `dev:ecommerce:ranking:produtos:consultas` |
|---|---|
| **Representa** | Ranking global de produtos mais consultados |
| **Dado armazenado** | Sorted Set com membros `produto:{id_produto}` e score = total de consultas |
| **TTL** | Não — estrutura permanente enquanto o sistema estiver em uso |

---

## 4.5 Relação entre Redis e SQL

### Demanda 1 — Consulta rápida de produtos

| Aspecto | Detalhe |
|---|---|
| **Dados do SQL** | `nome`, `preco_atual`, `estoque_total`, `id_produto` (tabelas `produto` e `estoque`) |
| **Dados no Redis** | JSON com os mesmos campos, em cache temporário |
| **Papel do Redis** | Cache de leitura (cache-aside) |

O SQLite é sempre a fonte confiável. O Redis é consultado primeiro; se não houver dado (`CACHE MISS`), o SQLite é acessado e o resultado é salvo no Redis.

### Demanda 2 — Carrinho temporário

| Aspecto | Detalhe |
|---|---|
| **Dados do SQL** | Verificação de existência do produto e disponibilidade de estoque (tabelas `produto` e `estoque`) |
| **Dados no Redis** | Apenas `id_produto` e `quantidade` por item do carrinho |
| **Papel do Redis** | Armazenamento temporário de estado |

O Redis não armazena nome nem preço no carrinho. Esses dados são buscados no SQLite apenas na hora de exibir o carrinho ao cliente (nome, preço, subtotal são calculados na hora da leitura).

### Demanda 3 — Produtos mais consultados

| Aspecto | Detalhe |
|---|---|
| **Dados do SQL** | `nome` e `preco_atual` do produto (consultados na hora de exibir o ranking) |
| **Dados no Redis** | Sorted Set com `id_produto` e contagem de consultas como score |
| **Papel do Redis** | Estrutura de apoio para contagem e ordenação em tempo real |

O SQLite não registra contagens de consulta. O Redis assume esse papel exclusivamente. Na exibição do ranking, os IDs dos produtos são recuperados do Sorted Set e os detalhes (nome, preço) são buscados no SQLite.

---

## 4.6 Mudanças no Projeto Base

| Parte do projeto | Alteração prevista |
|---|---|
| `docker-compose.yml` | Adicionar serviço `redis` (imagem `redis:7-alpine`) e serviço `redisinsight` para visualização |
| `requirements.txt` | Adicionar `redis>=5.0,<6.0` e `fakeredis>=2.0,<3.0` |
| Menu/Terminal | Adicionar novas opções: consultar produto por ID, gerenciar carrinho (adicionar item, ver carrinho), exibir ranking de produtos |
| Controller (`app_controller.py`) | Adicionar métodos para despachar as três novas operações Redis, instanciar `RedisManager` e `RedisService` |
| Service | Criar `redis_service.py` com a lógica de negócio das três demandas: cache de produto, operações de carrinho e atualização/leitura do ranking |
| Repository/SQL | Criar método `find_produto_by_id(id)` no `SQLiteRepository` para busca pontual de produto com estoque |
| Configuração Redis | Criar `config/redis.ini` com host, porta, db e modo mock; criar `redis_manager.py` responsável pela conexão (real ou fakeredis) |

---

## 4.7 Plano de Implementação

1. **Configuração do ambiente** — adicionar Redis e RedisInsight ao `docker-compose.yml`; criar `config/redis.ini`; atualizar `requirements.txt`
2. **Criar `RedisManager`** — classe responsável pela conexão com Redis real ou fakeredis, seguindo o mesmo padrão do `MongoManager` já existente
3. **Criar `RedisService`** — implementar as três demandas como métodos separados:
   - `buscar_produto_com_cache(produto_id)` — Demanda 1
   - `adicionar_ao_carrinho(cliente_id, produto_id, quantidade)` e `ver_carrinho(cliente_id)` — Demanda 2
   - `registrar_consulta(produto_id)` e `ver_ranking()` — Demanda 3
4. **Atualizar `SQLiteRepository`** — adicionar `find_produto_by_id(id)` para busca pontual de produto com estoque
5. **Atualizar `AppController`** — instanciar `RedisManager` e `RedisService`; criar métodos `_consultar_produto`, `_gerenciar_carrinho`, `_ver_ranking`
6. **Atualizar `MenuView`** — adicionar as novas opções ao menu e métodos de exibição para carrinho e ranking
7. **Testes pelo terminal** — verificar cada demanda conforme os critérios de aceite e validar chaves no RedisInsight

---

## 4.8 Testes Previstos

### Demanda 1 — Cache de produto

| Teste | Resultado esperado |
|---|---|
| Consultar produto com ID existente (ex: ID 1) | Sistema retorna nome, preço e estoque |
| Consultar o mesmo produto uma segunda vez | Log indica `CACHE HIT`; SQLite não é acessado |
| Consultar produto com ID inexistente | Mensagem "produto não encontrado" |
| Verificar no RedisInsight | Chave `dev:ecommerce:produto:cache:1` aparece com TTL ativo |
| Aguardar 60 segundos e consultar novamente | `CACHE MISS`; SQLite é acessado; chave é recriada |

### Demanda 2 — Carrinho temporário

| Teste | Resultado esperado |
|---|---|
| Adicionar produto existente com estoque suficiente | Item adicionado; Hash criado no Redis |
| Tentar adicionar produto inexistente | Mensagem de erro; Redis não é alterado |
| Tentar adicionar quantidade maior que o estoque | Mensagem de erro; Redis não é alterado |
| Visualizar carrinho | Nome do produto, preço unitário, quantidade e subtotal exibidos corretamente |
| Verificar no RedisInsight | Hash com campos `produto:{id}` e TTL de 900 segundos |

### Demanda 3 — Ranking de consultas

| Teste | Resultado esperado |
|---|---|
| Consultar o mesmo produto várias vezes | Score do produto incrementa a cada consulta |
| Consultar produto inexistente | Score não é incrementado |
| Exibir ranking | Lista ordenada do mais consultado para o menos, com nome, preço e total de consultas |
| Verificar no RedisInsight | Sorted Set `dev:ecommerce:ranking:produtos:consultas` com membros e scores corretos |
