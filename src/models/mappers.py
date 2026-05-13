"""Mappers entre domínio e documento MongoDB.

Versão 3 — um documento por pedido:
- cliente, pagamento e entrega embutidos como subdocumentos;
- itens como array de subdocumentos com snapshot do produto;
- estrutura alinhada com o pedido_validator() do mongo_schemas.py.
"""

from __future__ import annotations

from src.models.domain import Pedido, Produto


class PedidoMongoMapper:
    @staticmethod
    def to_document(pedido: Pedido) -> dict:
        """Converte um Pedido de domínio em um único documento MongoDB."""

        # ── Cliente ───────────────────────────────────────────────────────────
        cliente_doc = {
            "id_cliente": pedido.cliente.id_cliente,
            "nome":       pedido.cliente.nome,
            "email":      pedido.cliente.email,
            "cpf":        pedido.cliente.cpf,
            "telefone":   pedido.cliente.telefone,
        }

        # ── Itens (snapshot do produto no momento da compra) ──────────────────
        itens_docs = [
            {
                "id_produto":    item.id_produto,
                "nome_produto":  item.nome_produto,
                "categoria":     item.categoria,
                "quantidade":    item.quantidade,
                "valor_unitario": item.preco_unitario_compra,
                "subtotal":      item.subtotal,
            }
            for item in pedido.itens
        ]

        # ── Pagamento ─────────────────────────────────────────────────────────
        pagamento_doc = None
        if pedido.pagamento is not None:
            pagamento_doc = {
                "metodo":          pedido.pagamento.tipo_pagamento,
                "status":          pedido.pagamento.status_pagamento,
                "data_pagamento":  pedido.pagamento.data_pagamento,
            }

        # ── Entrega ───────────────────────────────────────────────────────────
        entrega_doc = None
        if pedido.entrega is not None:
            snap = pedido.entrega.endereco_snapshot
            entrega_doc = {
                "endereco":        snap.logradouro,
                "cidade":          snap.cidade,
                "estado":          snap.estado,
                "cep":             snap.cep,
                "status_entrega":  pedido.entrega.status_entrega,
                "previsao_entrega": None,
            }

        return {
            "_id":          pedido.id_pedido,
            "data_pedido":  pedido.data_pedido,
            "status_pedido": pedido.status_pedido,
            "cliente":      cliente_doc,
            "itens":        itens_docs,
            "valor_total":  pedido.valor_total,
            "pagamento":    pagamento_doc,
            "entrega":      entrega_doc,
        }


class ProdutoMongoMapper:
    @staticmethod
    def to_document(produto: Produto) -> dict:
        return {
            "_id":            produto.id_produto,
            "nome":           produto.nome,
            "descricao":      produto.descricao,
            "preco_atual":    produto.preco_atual,
            "ativo":          produto.ativo,
            "vendedor_nome":  produto.vendedor.nome_loja,
            "categorias":     produto.categorias,
            "estoque_total":  produto.estoque_total,
            "media_avaliacao": produto.resumo_avaliacao.media_notas,
        }
