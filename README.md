# Ecommerce: SQLite + MongoDB + Redis

Projeto da disciplina de **Banco de Dados Não Relacionais**.

Backend simplificado de e-commerce com arquitetura MVC, integrando três bancos de dados com papéis distintos: **SQLite** como fonte relacional persistente, **MongoDB** como banco documental e **Redis** como camada de apoio para cache, estado temporário e ranking em tempo real.

---

## Estrutura do Projeto

```
Ecommerce/
├── config/
│   ├── sqlite.ini
│   ├── mongodb.ini
│   └── redis.ini
├── data/
│   └── ecommerce.db
├── src/
│   ├── controllers/
│   │   └── app_controller.py
│   ├── models/
│   │   ├── config_loader.py
│   │   ├── domain.py
│   │   ├── mappers.py
│   │   ├── migration_service.py
│   │   ├── mongo_manager.py
│   │   ├── mongo_schemas.py
│   │   ├── query_service.py
│   │   ├── redis_manager.py
│   │   ├── redis_service.py
│   │   ├── sqlite_manager.py
│   │   └── sqlite_repository.py
│   └── views/
│       └── menu_view.py
├── docker-compose.yml
├── main.py
└── requirements.txt
```

---

## Arquitetura

| Banco | Papel |
|---|---|
| **SQLite** | Fonte persistente e confiável de todos os dados (produtos, pedidos, clientes) |
| **MongoDB** | Modelo documental achatado para consultas analíticas e de leitura |
| **Redis** | Cache de produtos, carrinho temporário e ranking de consultas em tempo real |

---

## Instalação

### Pré-requisitos

- Python 3.11+
- Docker e Docker Compose

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/ecommerce.git
cd ecommerce
```

### 2. Crie e ative o ambiente virtual

```bash
python -m venv .venv
```

Windows PowerShell:
```powershell
.venv\Scripts\Activate.ps1
```

Linux / macOS:
```bash
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Suba os containers

```bash
docker compose up -d
```

Serviços disponíveis após subir:

| Serviço | URL |
|---|---|
| MongoDB | `mongodb://root:example@localhost:27017` |
| Mongo Express | http://localhost:8081 |
| Redis | `localhost:6379` |
| RedisInsight | http://localhost:5540 |

### 5. Execute a aplicação

```bash
python main.py
```

---

## Menu do Sistema

```
1.  Testar configuração do SQLite
2.  Recriar e popular SQLite
3.  Testar configuração do MongoDB
4.  Recriar coleções Mongo com schema
5.  Migrar SQLite -> Mongo
6.  Mostrar amostra de documentos
7.  Executar consultas de exemplo
8.  Mostrar caminhos de configuração
--- Redis ---
9.  Testar configuração do Redis
10. Consultar produto por ID (cache-aside)
11. Adicionar produto ao carrinho
12. Visualizar carrinho
13. Exibir ranking de produtos mais consultados
0.  Sair
```

---

## Demandas Redis Implementadas

### Demanda 1 — Cache-aside de Produtos

Evita consultas repetidas ao SQLite armazenando os dados do produto em Redis com TTL de 60 segundos.

```
Chave: dev:ecommerce:produto:cache:{id_produto}
Tipo:  String com JSON
TTL:   60 segundos
```

Fluxo:
1. Busca no Redis → **CACHE HIT**: retorna imediatamente
2. **CACHE MISS**: busca no SQLite, salva no Redis com TTL e retorna

---

### Demanda 2 — Carrinho Temporário de Compras

Armazena o carrinho do cliente no Redis como Hash, com validação de estoque no SQLite antes de adicionar.

```
Chave: dev:ecommerce:carrinho:cliente:{id_cliente}
Tipo:  Hash  →  produto:{id} : quantidade
TTL:   900 segundos (15 minutos)
```

Validações aplicadas:
- Produto deve existir no SQLite
- Estoque deve ser suficiente para a quantidade solicitada

---

### Demanda 3 — Ranking de Produtos Mais Consultados

Registra automaticamente cada consulta a um produto existente e mantém um ranking ordenado por pontuação.

```
Chave: dev:ecommerce:ranking:produtos:consultas
Tipo:  Sorted Set  →  produto:{id} : score (total de consultas)
TTL:   Sem expiração
```

---

## Padrão de Chaves Redis

Todas as chaves seguem o padrão:

```
ambiente : aplicacao : dominio : finalidade : {identificador}
dev      : ecommerce : produto : cache      : 1
dev      : ecommerce : carrinho: cliente    : 10
dev      : ecommerce : ranking : produtos   : consultas
```

O prefixo `dev:ecommerce` evita colisão com outras aplicações no mesmo servidor Redis e facilita a inspeção no RedisInsight.

---

## Inspecionando com RedisInsight

Acesse http://localhost:5540 e conecte usando:

```
Host: redis
Port: 6379
```

---

## Modo sem Docker

Se o Redis ou o MongoDB não estiverem disponíveis, o sistema cai automaticamente para modo mock em memória:

- **fakeredis** substitui o Redis real
- **mongomock** substitui o MongoDB real

Nesse modo tudo funciona normalmente, mas os dados são perdidos ao encerrar o programa.

---

## 👥 Grupo

BDNRelacional 2 — Edson Ristow, Eduardo Paes, Giovanna Gonçalves e Rodrigo Rodrigues
