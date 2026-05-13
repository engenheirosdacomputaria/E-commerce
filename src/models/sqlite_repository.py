"""Leitura do SQLite e montagem das entidades de domínio."""

from __future__ import annotations

from src.models.domain import (
    Cliente,
    EnderecoSnapshot,
    Entrega,
    ItemPedido,
    Pagamento,
    Pedido,
    Produto,
    ResumoAvaliacao,
    Vendedor,
)
from src.models.sqlite_manager import SQLiteManager


class SQLiteRepository:
    def __init__(self, sqlite_manager: SQLiteManager) -> None:
        self.sqlite = sqlite_manager

    def list_produtos(self) -> list[Produto]:
        rows = self.sqlite.query_all(
            """
            SELECT
                p.id_produto,
                p.nome,
                p.descricao,
                p.preco_atual,
                p.ativo,
                v.id_vendedor,
                v.nome_loja,
                v.ativo AS vendedor_ativo,
                COALESCE(e.quantidade_disponivel, 0) AS estoque_total,
                COALESCE(e.quantidade_reservada, 0) AS estoque_reservado,
                COUNT(pa.id_avaliacao) AS qtd_avaliacoes,
                COALESCE(AVG(pa.nota), 0) AS media_notas
            FROM produto p
            JOIN vendedor v ON v.id_vendedor = p.id_vendedor
            LEFT JOIN estoque e ON e.id_produto = p.id_produto
            LEFT JOIN produto_avaliacao pa ON pa.id_produto = p.id_produto
            GROUP BY p.id_produto, p.nome, p.descricao, p.preco_atual, p.ativo,
                     v.id_vendedor, v.nome_loja, v.ativo,
                     e.quantidade_disponivel, e.quantidade_reservada
            ORDER BY p.id_produto
            """
        )

        produtos: list[Produto] = []
        for row in rows:
            categorias = [
                r["nome"]
                for r in self.sqlite.query_all(
                    """
                    SELECT c.nome
                    FROM produto_categoria pc
                    JOIN categoria c ON c.id_categoria = pc.id_categoria
                    WHERE pc.id_produto = ?
                    ORDER BY c.nome
                    """,
                    (row["id_produto"],),
                )
            ]

            produtos.append(
                Produto(
                    id_produto=int(row["id_produto"]),
                    nome=row["nome"],
                    descricao=row["descricao"],
                    preco_atual=float(row["preco_atual"]),
                    ativo=bool(row["ativo"]),
                    vendedor=Vendedor(
                        id_vendedor=int(row["id_vendedor"]),
                        nome_loja=row["nome_loja"],
                        ativo=bool(row["vendedor_ativo"]),
                    ),
                    categorias=categorias,
                    estoque_total=int(row["estoque_total"]),
                    estoque_reservado=int(row["estoque_reservado"]),
                    resumo_avaliacao=ResumoAvaliacao(
                        qtd_avaliacoes=int(row["qtd_avaliacoes"]),
                        media_notas=round(float(row["media_notas"]), 2),
                    ),
                )
            )
        return produtos

    def list_pedidos(self) -> list[Pedido]:
        pedido_rows = self.sqlite.query_all(
            """
            SELECT p.*,
                   c.nome  AS cliente_nome,
                   c.email AS cliente_email,
                   c.cpf   AS cliente_cpf,
                   c.telefone AS cliente_telefone,
                   cu.codigo        AS cupom_codigo,
                   cu.tipo_desconto AS cupom_tipo,
                   cu.valor_desconto AS cupom_valor
            FROM pedido p
            JOIN cliente c ON c.id_cliente = p.id_cliente
            LEFT JOIN cupom cu ON cu.id_cupom = p.id_cupom
            ORDER BY p.id_pedido
            """
        )

        pedidos: list[Pedido] = []
        for row in pedido_rows:
            pagamento_row = self.sqlite.query_one(
                "SELECT * FROM pagamento WHERE id_pedido = ?",
                (row["id_pedido"],),
            )
            entrega_row = self.sqlite.query_one(
                "SELECT * FROM entrega WHERE id_pedido = ?",
                (row["id_pedido"],),
            )
            item_rows = self.sqlite.query_all(
                "SELECT * FROM item_pedido WHERE id_pedido = ? ORDER BY id_item_pedido",
                (row["id_pedido"],),
            )

            itens = [
                ItemPedido(
                    id_produto=int(item["id_produto"]),
                    produto_ref=int(item["id_produto"]),
                    id_variacao=None if item["id_variacao"] is None else int(item["id_variacao"]),
                    nome_produto=item["nome_produto_snapshot"],
                    sku=item["sku_snapshot"],
                    variacao_snapshot=item["variacao_snapshot"],
                    categoria=item["categoria_snapshot"],
                    quantidade=int(item["quantidade"]),
                    preco_unitario_compra=float(item["preco_unitario_compra"]),
                    subtotal=float(item["subtotal"]),
                    atributos_snapshot=None,
                )
                for item in item_rows
            ]

            pagamento = None
            if pagamento_row is not None:
                pagamento = Pagamento(
                    tipo_pagamento=pagamento_row["tipo_pagamento"],
                    status_pagamento=pagamento_row["status_pagamento"],
                    valor_pago=float(pagamento_row["valor_pago"]),
                    parcelas=int(pagamento_row["parcelas"]),
                    codigo_transacao=None,
                    data_pagamento=None,
                )

            entrega = None
            if entrega_row is not None:
                entrega = Entrega(
                    status_entrega=entrega_row["status_entrega"],
                    transportadora=entrega_row["transportadora"],
                    codigo_rastreio=entrega_row["codigo_rastreio"],
                    endereco_snapshot=EnderecoSnapshot(
                        logradouro=entrega_row["logradouro_snapshot"],
                        numero=entrega_row["numero_snapshot"],
                        bairro=entrega_row["bairro_snapshot"],
                        cidade=entrega_row["cidade_snapshot"],
                        estado=entrega_row["estado_snapshot"],
                        cep=entrega_row["cep_snapshot"],
                        complemento=None,
                    ),
                )

            cupom = None
            if row["id_cupom"] is not None:
                cupom = {
                    "id_cupom": int(row["id_cupom"]),
                    "codigo": row["cupom_codigo"],
                    "tipo_desconto": row["cupom_tipo"],
                    "valor_desconto": float(row["cupom_valor"]),
                }

            pedido = Pedido(
                id_pedido=int(row["id_pedido"]),
                data_pedido=row["data_pedido"],
                status_pedido=row["status_pedido"],
                cliente_ref=int(row["id_cliente"]),
                cliente=Cliente(
                    id_cliente=int(row["id_cliente"]),
                    nome=row["cliente_nome"],
                    email=row["cliente_email"],
                    cpf=row["cliente_cpf"],
                    telefone=row["cliente_telefone"],
                ),
                cupom=cupom,
                pagamento=pagamento,
                entrega=entrega,
                itens=itens,
                valor_produtos=float(row["valor_produtos"]),
                valor_frete=float(row["valor_frete"]),
                valor_desconto=float(row["valor_desconto"]),
                valor_total=float(row["valor_total"]),
            )
            pedidos.append(pedido)
        return pedidos

    def find_produto_by_id(self, produto_id: int) -> dict | None:
        """Busca pontual de produto por ID com JOIN na tabela estoque.

        Retorna um dicionário simples para uso no RedisService,
        ou None se o produto não existir.
        """
        row = self.sqlite.query_one(
            """
            SELECT
                p.id_produto,
                p.nome,
                p.preco_atual,
                COALESCE(e.quantidade_disponivel, 0) AS estoque_total
            FROM produto p
            LEFT JOIN estoque e ON e.id_produto = p.id_produto
            WHERE p.id_produto = ?
            """,
            (produto_id,),
        )

        if row is None:
            return None

        return {
            "id_produto": int(row["id_produto"]),
            "nome": row["nome"],
            "preco_atual": float(row["preco_atual"]),
            "estoque_total": int(row["estoque_total"]),
        }