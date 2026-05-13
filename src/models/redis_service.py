"""Serviço Redis.

Implementa as três demandas da atividade:
    Demanda 1 — Cache-aside de produtos
    Demanda 2 — Carrinho temporário de compras
    Demanda 3 — Ranking de produtos mais consultados
"""

from __future__ import annotations

import json

from src.models.redis_manager import RedisManager, nome_chave
from src.models.sqlite_repository import SQLiteRepository

TTL_CACHE_PRODUTO = 60
TTL_CARRINHO = 900


class RedisService:
    def __init__(self, redis_manager: RedisManager, sqlite_repository: SQLiteRepository) -> None:
        self.redis = redis_manager
        self.repository = sqlite_repository

    def _r(self):
        self.redis.ensure_connected()
        return self.redis.client

    # -------------------------------------------------------------------------
    # Demanda 1 — Cache-aside de produtos
    # -------------------------------------------------------------------------

    def buscar_produto_com_cache(self, produto_id: int) -> dict | None:
        """Busca produto pelo ID usando cache-aside.

        Fluxo:
            1. Tenta buscar no Redis.
            2. CACHE HIT: retorna dado do Redis.
            3. CACHE MISS: busca no SQLite, salva no Redis com TTL e retorna.
        """
        r = self._r()
        chave = nome_chave("produto", "cache", produto_id)

        valor = r.get(chave)
        if valor is not None:
            print(f"[CACHE HIT] Produto {produto_id} veio do Redis.")
            produto = json.loads(valor)
            self._registrar_consulta(produto_id)
            return produto

        print(f"[CACHE MISS] Produto {produto_id} não estava no Redis.")
        produto = self.repository.find_produto_by_id(produto_id)

        if produto is None:
            print(f"[SQL] Produto {produto_id} não encontrado.")
            return None

        r.setex(chave, TTL_CACHE_PRODUTO, json.dumps(produto, ensure_ascii=False))
        print(f"[REDIS] Produto salvo em {chave} com TTL de {TTL_CACHE_PRODUTO}s.")
        self._registrar_consulta(produto_id)
        return produto

    # -------------------------------------------------------------------------
    # Demanda 2 — Carrinho temporário de compras
    # -------------------------------------------------------------------------

    def adicionar_ao_carrinho(self, cliente_id: int, produto_id: int, quantidade: int) -> tuple[bool, str]:
        """Adiciona produto ao carrinho do cliente.

        Validações:
            - Produto deve existir no SQLite.
            - Estoque deve ser suficiente.
        """
        produto = self.repository.find_produto_by_id(produto_id)
        if produto is None:
            return False, f"Produto {produto_id} não encontrado."

        if produto["estoque_total"] < quantidade:
            return False, (
                f"Estoque insuficiente. "
                f"Disponível: {produto['estoque_total']} | Solicitado: {quantidade}"
            )

        r = self._r()
        chave = nome_chave("carrinho", "cliente", cliente_id)
        campo = f"produto:{produto_id}"

        r.hset(chave, campo, quantidade)
        r.expire(chave, TTL_CARRINHO)

        return True, f"Produto '{produto['nome']}' adicionado ao carrinho (quantidade: {quantidade})."

    def ver_carrinho(self, cliente_id: int) -> list[dict]:
        """Retorna os itens do carrinho com nome, preço, quantidade e subtotal."""
        r = self._r()
        chave = nome_chave("carrinho", "cliente", cliente_id)
        itens_hash = r.hgetall(chave)

        if not itens_hash:
            return []

        itens = []
        for campo, quantidade_str in itens_hash.items():
            produto_id = int(campo.split(":")[1])
            produto = self.repository.find_produto_by_id(produto_id)
            if produto is None:
                continue
            quantidade = int(quantidade_str)
            subtotal = round(produto["preco_atual"] * quantidade, 2)
            itens.append({
                "produto_id": produto_id,
                "nome": produto["nome"],
                "preco_unitario": produto["preco_atual"],
                "quantidade": quantidade,
                "subtotal": subtotal,
            })

        return itens

    # -------------------------------------------------------------------------
    # Demanda 3 — Ranking de produtos mais consultados
    # -------------------------------------------------------------------------

    def _registrar_consulta(self, produto_id: int) -> None:
        """Incrementa o score do produto no Sorted Set de ranking.

        Chamado internamente por buscar_produto_com_cache(),
        garantindo que só produtos existentes sejam contabilizados.
        """
        r = self._r()
        chave = nome_chave("ranking", "produtos", "consultas")
        r.zincrby(chave, 1, f"produto:{produto_id}")

    def ver_ranking(self, limite: int = 10) -> list[dict]:
        """Retorna os produtos mais consultados em ordem decrescente."""
        r = self._r()
        chave = nome_chave("ranking", "produtos", "consultas")
        ranking_raw = r.zrevrange(chave, 0, limite - 1, withscores=True)

        if not ranking_raw:
            return []

        resultado = []
        for membro, score in ranking_raw:
            produto_id = int(membro.split(":")[1])
            produto = self.repository.find_produto_by_id(produto_id)
            if produto is None:
                continue
            resultado.append({
                "produto_id": produto_id,
                "nome": produto["nome"],
                "preco_atual": produto["preco_atual"],
                "total_consultas": int(score),
            })

        return resultado