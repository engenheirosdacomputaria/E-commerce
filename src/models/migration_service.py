"""Serviço de migração.

Fluxo:
1. lê o SQLite por meio do repository;
2. monta entidades de domínio;
3. converte essas entidades para documentos Mongo (v3 — um doc por pedido).
"""

from __future__ import annotations

from src.models.mappers import PedidoMongoMapper, ProdutoMongoMapper
from src.models.mongo_manager import MongoManager
from src.models.sqlite_repository import SQLiteRepository


class MigrationService:
    def __init__(self, repository: SQLiteRepository, mongo_manager: MongoManager) -> None:
        self.repository = repository
        self.mongo = mongo_manager

    def migrate(self) -> dict[str, int]:
        self.mongo.ensure_connected()

        produtos = [
            ProdutoMongoMapper.to_document(produto)
            for produto in self.repository.list_produtos()
        ]

        pedidos: list[dict] = []
        total_pedidos_origem = 0
        for pedido in self.repository.list_pedidos():
            total_pedidos_origem += 1
            pedidos.append(PedidoMongoMapper.to_document(pedido))

        self.mongo.produtos.delete_many({})
        self.mongo.pedidos.delete_many({})

        if produtos:
            self.mongo.produtos.insert_many(produtos)
        if pedidos:
            self.mongo.pedidos.insert_many(pedidos)

        return {
            "produtos": len(produtos),
            "pedidos": len(pedidos),
            "pedidos_origem": total_pedidos_origem,
        }