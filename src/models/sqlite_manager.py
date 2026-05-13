"""Criação e população do banco SQLite.

Aqui concentramos tudo que pertence ao lado relacional.
A ideia é reduzir a arquitetura: uma classe para o banco relacional e pronto.
"""

from __future__ import annotations

import random
import sqlite3
from pathlib import Path
from typing import Iterable

from faker import Faker


class SQLiteManager:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.fake = Faker("pt_BR")
        random.seed(42)
        Faker.seed(42)

    def connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON;")
        return connection

    def test_connection(self) -> tuple[bool, str]:
        try:
            conn = self.connect()
            conn.execute("SELECT 1")
            conn.close()
            return True, f"Conexão SQLite OK em: {self.db_path}"
        except Exception as exc:
            return False, f"Falha no SQLite: {exc}"

    def recreate_database(self) -> None:
        if self.db_path.exists():
            self.db_path.unlink()

        conn = self.connect()
        self._create_schema(conn)
        self._populate(conn)
        conn.commit()
        conn.close()

    def _create_schema(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE cliente (
                id_cliente INTEGER PRIMARY KEY,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                telefone TEXT,
                cpf TEXT,
                data_cadastro TEXT NOT NULL,
                ativo INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE endereco_cliente (
                id_endereco INTEGER PRIMARY KEY,
                id_cliente INTEGER NOT NULL,
                logradouro TEXT NOT NULL,
                numero TEXT NOT NULL,
                bairro TEXT NOT NULL,
                cidade TEXT NOT NULL,
                estado TEXT NOT NULL,
                cep TEXT NOT NULL,
                principal INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (id_cliente) REFERENCES cliente(id_cliente)
            );

            CREATE TABLE metodo_pagamento_cliente (
                id_metodo_pagamento INTEGER PRIMARY KEY,
                id_cliente INTEGER NOT NULL,
                tipo_pagamento TEXT NOT NULL,
                detalhes TEXT,
                principal INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (id_cliente) REFERENCES cliente(id_cliente)
            );

            CREATE TABLE vendedor (
                id_vendedor INTEGER PRIMARY KEY,
                nome_loja TEXT NOT NULL,
                email_contato TEXT NOT NULL,
                ativo INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE categoria (
                id_categoria INTEGER PRIMARY KEY,
                nome TEXT NOT NULL UNIQUE
            );

            CREATE TABLE produto (
                id_produto INTEGER PRIMARY KEY,
                id_vendedor INTEGER NOT NULL,
                nome TEXT NOT NULL,
                descricao TEXT NOT NULL,
                preco_atual REAL NOT NULL,
                ativo INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (id_vendedor) REFERENCES vendedor(id_vendedor)
            );

            CREATE TABLE produto_categoria (
                id_produto INTEGER NOT NULL,
                id_categoria INTEGER NOT NULL,
                PRIMARY KEY (id_produto, id_categoria),
                FOREIGN KEY (id_produto) REFERENCES produto(id_produto),
                FOREIGN KEY (id_categoria) REFERENCES categoria(id_categoria)
            );

            CREATE TABLE produto_variacao (
                id_variacao INTEGER PRIMARY KEY,
                id_produto INTEGER NOT NULL,
                sku TEXT NOT NULL UNIQUE,
                nome_variacao TEXT NOT NULL,
                preco_adicional REAL NOT NULL DEFAULT 0,
                FOREIGN KEY (id_produto) REFERENCES produto(id_produto)
            );

            CREATE TABLE produto_atributo_valor (
                id_atributo_valor INTEGER PRIMARY KEY,
                id_produto INTEGER NOT NULL,
                nome_atributo TEXT NOT NULL,
                valor_atributo TEXT NOT NULL,
                FOREIGN KEY (id_produto) REFERENCES produto(id_produto)
            );

            CREATE TABLE produto_imagem (
                id_imagem INTEGER PRIMARY KEY,
                id_produto INTEGER NOT NULL,
                url_imagem TEXT NOT NULL,
                principal INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (id_produto) REFERENCES produto(id_produto)
            );

            CREATE TABLE estoque (
                id_estoque INTEGER PRIMARY KEY,
                id_produto INTEGER NOT NULL UNIQUE,
                quantidade_disponivel INTEGER NOT NULL,
                quantidade_reservada INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (id_produto) REFERENCES produto(id_produto)
            );

            CREATE TABLE produto_avaliacao (
                id_avaliacao INTEGER PRIMARY KEY,
                id_produto INTEGER NOT NULL,
                nome_cliente TEXT NOT NULL,
                nota INTEGER NOT NULL,
                comentario TEXT,
                data_avaliacao TEXT NOT NULL,
                FOREIGN KEY (id_produto) REFERENCES produto(id_produto)
            );

            CREATE TABLE cupom (
                id_cupom INTEGER PRIMARY KEY,
                codigo TEXT NOT NULL UNIQUE,
                tipo_desconto TEXT NOT NULL,
                valor_desconto REAL NOT NULL,
                ativo INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE pedido (
                id_pedido INTEGER PRIMARY KEY,
                id_cliente INTEGER NOT NULL,
                id_cupom INTEGER,
                data_pedido TEXT NOT NULL,
                status_pedido TEXT NOT NULL,
                valor_produtos REAL NOT NULL,
                valor_frete REAL NOT NULL,
                valor_desconto REAL NOT NULL,
                valor_total REAL NOT NULL,
                FOREIGN KEY (id_cliente) REFERENCES cliente(id_cliente),
                FOREIGN KEY (id_cupom) REFERENCES cupom(id_cupom)
            );

            CREATE TABLE pagamento (
                id_pagamento INTEGER PRIMARY KEY,
                id_pedido INTEGER NOT NULL UNIQUE,
                tipo_pagamento TEXT NOT NULL,
                status_pagamento TEXT NOT NULL,
                valor_pago REAL NOT NULL,
                parcelas INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (id_pedido) REFERENCES pedido(id_pedido)
            );

            CREATE TABLE entrega (
                id_entrega INTEGER PRIMARY KEY,
                id_pedido INTEGER NOT NULL UNIQUE,
                status_entrega TEXT NOT NULL,
                transportadora TEXT NOT NULL,
                codigo_rastreio TEXT NOT NULL,
                logradouro_snapshot TEXT NOT NULL,
                numero_snapshot TEXT NOT NULL,
                bairro_snapshot TEXT NOT NULL,
                cidade_snapshot TEXT NOT NULL,
                estado_snapshot TEXT NOT NULL,
                cep_snapshot TEXT NOT NULL,
                FOREIGN KEY (id_pedido) REFERENCES pedido(id_pedido)
            );

            CREATE TABLE item_pedido (
                id_item_pedido INTEGER PRIMARY KEY,
                id_pedido INTEGER NOT NULL,
                id_produto INTEGER NOT NULL,
                id_variacao INTEGER,
                nome_produto_snapshot TEXT NOT NULL,
                sku_snapshot TEXT,
                variacao_snapshot TEXT,
                categoria_snapshot TEXT NOT NULL,
                quantidade INTEGER NOT NULL,
                preco_unitario_compra REAL NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (id_pedido) REFERENCES pedido(id_pedido),
                FOREIGN KEY (id_produto) REFERENCES produto(id_produto),
                FOREIGN KEY (id_variacao) REFERENCES produto_variacao(id_variacao)
            );
            """
        )

    def _populate(self, conn: sqlite3.Connection) -> None:
        self._insert_clientes(conn, 12)
        self._insert_enderecos(conn, 18)
        self._insert_metodos_pagamento(conn, 12)
        self._insert_vendedores(conn, 10)
        self._insert_categorias(conn)
        self._insert_produtos(conn, 15)
        self._insert_produto_categoria(conn)
        self._insert_variacoes(conn, 12)
        self._insert_atributos(conn, 20)
        self._insert_imagens(conn, 15)
        self._insert_estoque(conn)
        self._insert_avaliacoes(conn, 18)
        self._insert_cupons(conn, 10)
        self._insert_pedidos_pagamentos_entregas_itens(conn, 12)

    def _insert_clientes(self, conn: sqlite3.Connection, total: int) -> None:
        rows = []
        for i in range(1, total + 1):
            rows.append((
                i,
                self.fake.name(),
                f"cliente{i}@email.com",
                self.fake.phone_number(),
                self.fake.cpf(),
                self.fake.date_between(start_date="-1y", end_date="today").isoformat(),
                1,
            ))
        conn.executemany(
            "INSERT INTO cliente VALUES (?, ?, ?, ?, ?, ?, ?)", rows
        )

    def _insert_enderecos(self, conn: sqlite3.Connection, total: int) -> None:
        """Insere endereços garantindo ao menos 1 por cliente.

        Isso evita erro na geração de entregas, pois cada pedido precisa
        encontrar um endereço do cliente para montar o snapshot.
        """
        cidades = ["Curitiba", "São José dos Pinhais", "Pinhais", "Colombo", "Araucária"]
        rows = []
        next_id = 1
        total_clientes = 12

        # 1 endereço principal obrigatório para cada cliente
        for id_cliente in range(1, total_clientes + 1):
            rows.append((
                next_id,
                id_cliente,
                self.fake.street_name(),
                str(random.randint(1, 999)),
                self.fake.bairro(),
                random.choice(cidades),
                "PR",
                self.fake.postcode(),
                1,
            ))
            next_id += 1

        # Endereços extras, se solicitado
        extras = max(total - total_clientes, 0)
        for _ in range(extras):
            rows.append((
                next_id,
                random.randint(1, total_clientes),
                self.fake.street_name(),
                str(random.randint(1, 999)),
                self.fake.bairro(),
                random.choice(cidades),
                "PR",
                self.fake.postcode(),
                0,
            ))
            next_id += 1

        conn.executemany(
            "INSERT INTO endereco_cliente VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", rows
        )

    def _insert_metodos_pagamento(self, conn: sqlite3.Connection, total: int) -> None:
        tipos = ["cartao", "pix", "boleto"]
        rows = []
        for i in range(1, total + 1):
            rows.append((
                i,
                i,
                random.choice(tipos),
                self.fake.credit_card_number(),
                1,
            ))
        conn.executemany(
            "INSERT INTO metodo_pagamento_cliente VALUES (?, ?, ?, ?, ?)", rows
        )

    def _insert_vendedores(self, conn: sqlite3.Connection, total: int) -> None:
        rows = []
        for i in range(1, total + 1):
            rows.append((i, f"Loja {i}", f"loja{i}@email.com", 1))
        conn.executemany("INSERT INTO vendedor VALUES (?, ?, ?, ?)", rows)

    def _insert_categorias(self, conn: sqlite3.Connection) -> None:
        categorias = [
            (1, "Eletrônicos"),
            (2, "Informática"),
            (3, "Periféricos"),
            (4, "Áudio"),
            (5, "Casa Inteligente"),
            (6, "Acessórios"),
            (7, "Games"),
            (8, "Escritório"),
            (9, "Rede"),
            (10, "Monitores"),
        ]
        conn.executemany("INSERT INTO categoria VALUES (?, ?)", categorias)

    def _insert_produtos(self, conn: sqlite3.Connection, total: int) -> None:
        nomes = [
            "Notebook X", "Mouse Gamer", "Teclado Mecânico", "Headset Pro", "Monitor 24",
            "Roteador AX", "Webcam HD", "SSD 1TB", "Hub USB", "Caixa de Som",
            "Smart Plug", "Cadeira Office", "Microfone USB", "Teclado Slim", "Mouse Sem Fio"
        ]
        rows = []
        for i in range(1, total + 1):
            rows.append((
                i,
                random.randint(1, 10),
                nomes[i - 1],
                self.fake.sentence(nb_words=12),
                round(random.uniform(49.9, 4999.9), 2),
                1 if i % 7 != 0 else 0,
            ))
        conn.executemany("INSERT INTO produto VALUES (?, ?, ?, ?, ?, ?)", rows)

    def _insert_produto_categoria(self, conn: sqlite3.Connection) -> None:
        rows = []
        for id_produto in range(1, 16):
            categorias = random.sample(range(1, 11), k=random.randint(1, 2))
            for id_categoria in categorias:
                rows.append((id_produto, id_categoria))
        conn.executemany("INSERT OR IGNORE INTO produto_categoria VALUES (?, ?)", rows)

    def _insert_variacoes(self, conn: sqlite3.Connection, total: int) -> None:
        nomes = ["Preto", "Branco", "Azul", "64GB", "128GB", "Prata", "RGB", "Compacto"]
        rows = []
        for i in range(1, total + 1):
            rows.append((
                i,
                random.randint(1, 15),
                f"SKU-{1000 + i}",
                random.choice(nomes),
                round(random.uniform(0, 300), 2),
            ))
        conn.executemany("INSERT INTO produto_variacao VALUES (?, ?, ?, ?, ?)", rows)

    def _insert_atributos(self, conn: sqlite3.Connection, total: int) -> None:
        atributos = [
            ("cor", "preto"),
            ("ram", "16GB"),
            ("armazenamento", "1TB"),
            ("conexao", "bluetooth"),
        ]
        rows = []
        for i in range(1, total + 1):
            nome, valor = random.choice(atributos)
            rows.append((i, random.randint(1, 15), nome, valor))
        conn.executemany("INSERT INTO produto_atributo_valor VALUES (?, ?, ?, ?)", rows)

    def _insert_imagens(self, conn: sqlite3.Connection, total: int) -> None:
        rows = []
        for i in range(1, total + 1):
            rows.append((
                i,
                random.randint(1, 15),
                f"https://img.exemplo/produto_{i}.jpg",
                1 if i <= 5 else 0,
            ))
        conn.executemany("INSERT INTO produto_imagem VALUES (?, ?, ?, ?)", rows)

    def _insert_estoque(self, conn: sqlite3.Connection) -> None:
        rows = []
        for i in range(1, 16):
            disponivel = random.randint(0, 80)
            reservado = random.randint(0, min(disponivel, 10))
            rows.append((i, i, disponivel, reservado))
        conn.executemany("INSERT INTO estoque VALUES (?, ?, ?, ?)", rows)

    def _insert_avaliacoes(self, conn: sqlite3.Connection, total: int) -> None:
        rows = []
        for i in range(1, total + 1):
            rows.append((
                i,
                random.randint(1, 15),
                self.fake.name(),
                random.randint(2, 5),
                self.fake.sentence(nb_words=8),
                self.fake.date_between(start_date="-8M", end_date="today").isoformat(),
            ))
        conn.executemany("INSERT INTO produto_avaliacao VALUES (?, ?, ?, ?, ?, ?)", rows)

    def _insert_cupons(self, conn: sqlite3.Connection, total: int) -> None:
        rows = []
        for i in range(1, total + 1):
            tipo = random.choice(["fixo", "percentual"])
            valor = round(random.uniform(5, 50), 2)
            rows.append((i, f"DESC{i:02d}", tipo, valor, 1))
        conn.executemany("INSERT INTO cupom VALUES (?, ?, ?, ?, ?)", rows)

    def _insert_pedidos_pagamentos_entregas_itens(self, conn: sqlite3.Connection, total: int) -> None:
        status_pedido = ["pendente", "pago", "cancelado", "entregue"]
        status_pagamento = ["pendente", "aprovado", "recusado"]
        status_entrega = ["pendente", "em_transporte", "entregue"]
        tipo_pagamento = ["cartao", "pix", "boleto"]
        transportadoras = ["LogExpress", "EntregaJá", "RápidoSul"]

        pedido_rows = []
        pagamento_rows = []
        entrega_rows = []
        item_rows = []

        item_id = 1
        for id_pedido in range(1, total + 1):
            id_cliente = random.randint(1, 12)
            id_cupom = random.choice([None, None, random.randint(1, 10)])
            data_pedido = self.fake.date_between(start_date="-6M", end_date="today").isoformat()
            status = random.choice(status_pedido)
            qtd_itens = random.randint(1, 3)
            produtos_escolhidos = random.sample(range(1, 16), k=qtd_itens)
            valor_produtos = 0.0
            item_temp = []

            for id_produto in produtos_escolhidos:
                produto = conn.execute(
                    "SELECT nome, preco_atual FROM produto WHERE id_produto = ?",
                    (id_produto,),
                ).fetchone()

                categoria = conn.execute(
                    """
                    SELECT c.nome
                    FROM produto_categoria pc
                    JOIN categoria c ON c.id_categoria = pc.id_categoria
                    WHERE pc.id_produto = ?
                    LIMIT 1
                    """,
                    (id_produto,),
                ).fetchone()

                variacao = conn.execute(
                    "SELECT id_variacao, sku, nome_variacao FROM produto_variacao WHERE id_produto = ? LIMIT 1",
                    (id_produto,),
                ).fetchone()

                quantidade = random.randint(1, 3)
                preco = float(produto["preco_atual"])
                subtotal = round(preco * quantidade, 2)
                valor_produtos += subtotal

                item_temp.append((
                    item_id,
                    id_pedido,
                    id_produto,
                    variacao["id_variacao"] if variacao else None,
                    produto["nome"],
                    variacao["sku"] if variacao else None,
                    variacao["nome_variacao"] if variacao else None,
                    categoria["nome"] if categoria else "Sem categoria",
                    quantidade,
                    preco,
                    subtotal,
                ))
                item_id += 1

            valor_frete = round(random.uniform(10, 40), 2)
            desconto = 0.0
            if id_cupom is not None:
                cupom = conn.execute(
                    "SELECT tipo_desconto, valor_desconto FROM cupom WHERE id_cupom = ?",
                    (id_cupom,),
                ).fetchone()
                if cupom["tipo_desconto"] == "fixo":
                    desconto = float(cupom["valor_desconto"])
                else:
                    desconto = round(valor_produtos * (float(cupom["valor_desconto"]) / 100.0), 2)

            valor_total = round(max(valor_produtos + valor_frete - desconto, 0), 2)

            pedido_rows.append((
                id_pedido,
                id_cliente,
                id_cupom,
                data_pedido,
                status,
                round(valor_produtos, 2),
                valor_frete,
                desconto,
                valor_total,
            ))

            pagamento_rows.append((
                id_pedido,
                id_pedido,
                random.choice(tipo_pagamento),
                random.choice(status_pagamento),
                valor_total,
                random.randint(1, 6),
            ))

            endereco = conn.execute(
                """
                SELECT *
                FROM endereco_cliente
                WHERE id_cliente = ?
                ORDER BY principal DESC, id_endereco
                LIMIT 1
                """,
                (id_cliente,),
            ).fetchone()

            if endereco is None:
                raise ValueError(f"Cliente {id_cliente} está sem endereço cadastrado.")

            entrega_rows.append((
                id_pedido,
                id_pedido,
                random.choice(status_entrega),
                random.choice(transportadoras),
                f"BR{id_pedido:05d}",
                endereco["logradouro"],
                endereco["numero"],
                endereco["bairro"],
                endereco["cidade"],
                endereco["estado"],
                endereco["cep"],
            ))

            item_rows.extend(item_temp)

        conn.executemany("INSERT INTO pedido VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", pedido_rows)
        conn.executemany("INSERT INTO pagamento VALUES (?, ?, ?, ?, ?, ?)", pagamento_rows)
        conn.executemany("INSERT INTO entrega VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", entrega_rows)
        conn.executemany("INSERT INTO item_pedido VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", item_rows)

    def query_all(self, sql: str, params: Iterable | tuple = ()) -> list[sqlite3.Row]:
        conn = self.connect()
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return rows

    def query_one(self, sql: str, params: Iterable | tuple = ()) -> sqlite3.Row | None:
        conn = self.connect()
        row = conn.execute(sql, params).fetchone()
        conn.close()
        return row
