"""Consultas de exemplo sobre o modelo documental simplificado."""

from __future__ import annotations

from src.models.mongo_manager import MongoManager


class QueryService:
    def __init__(self, mongo_manager: MongoManager) -> None:
        self.mongo = mongo_manager

    def sample_produtos(self, limit: int = 3) -> list[dict]:
        return list(self.mongo.produtos.find().limit(limit))

    def sample_pedidos(self, limit: int = 5) -> list[dict]:
        return list(self.mongo.pedidos.find().limit(limit))

    def example_filter_paid_orders(self) -> list[dict]:
        return list(
            self.mongo.pedidos.find(
                {"status_pedido": "pago"},
                {"_id": 1, "cliente.nome": 1, "valor_total": 1},
            ).limit(5)
        )

    def example_projection_curitiba(self) -> list[dict]:
        return list(
            self.mongo.pedidos.find(
                {"entrega.cidade": "Curitiba"},
                {
                    "_id": 1,
                    "cliente.nome": 1,
                    "entrega.cidade": 1,
                    "valor_total": 1,
                },
            ).limit(5)
        )

    def example_update_first_order(self) -> dict | None:
        pedido = self.mongo.pedidos.find_one({})
        if not pedido:
            return None

        resultado = self.mongo.pedidos.update_one(
            {"_id": pedido["_id"]},
            {"$set": {"status_pedido": "entregue", "entrega.status_entrega": "entregue"}},
        )

        atualizado = self.mongo.pedidos.find_one(
            {"_id": pedido["_id"]},
            {"_id": 1, "status_pedido": 1, "entrega.status_entrega": 1},
        )
        if atualizado is None:
            return None

        atualizado["documentos_modificados"] = resultado.modified_count
        return atualizado

    def example_aggregation_best_sellers(self) -> list[dict]:
        pipeline = [
            {"$unwind": "$itens"},
            {
                "$group": {
                    "_id": "$itens.nome_produto",
                    "quantidade_total": {"$sum": "$itens.quantidade"},
                    "faturamento_total": {"$sum": "$itens.subtotal"},
                }
            },
            {"$sort": {"quantidade_total": -1, "_id": 1}},
            {"$limit": 5},
        ]
        return list(self.mongo.pedidos.aggregate(pipeline))

    def example_pagination(self, page: int = 2, size: int = 5) -> list[dict]:
        return list(
            self.mongo.pedidos.find(
                {},
                {"_id": 1, "data_pedido": 1, "cliente.nome": 1, "valor_total": 1},
            )
            .sort("data_pedido", -1)
            .skip((page - 1) * size)
            .limit(size)
        )