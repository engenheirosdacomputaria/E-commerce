import json
from src.models.sqlite_repository import SQLiteRepository

class RedisService:
    def __init__(self, redis_client, sqlite_repository: SQLiteRepository):
        self.redis = redis_client
        self.sqlite = sqlite_repository

    # Demanda 1: Cache-aside de Produtos
    def consultar_produto(self, produto_id: int):
        chave = f"dev:ecommerce:produto:cache:{produto_id}"
        
        cached_produto = self.redis.get(chave)
        if cached_produto:
            self._incrementar_ranking(produto_id)
            return "HIT", json.loads(cached_produto)

        # Cache MISS - Busca no SQLite
        produtos = self.sqlite.list_produtos()
        produto = next((p for p in produtos if p.id_produto == produto_id), None)
        
        if produto:
            # Simplificação do objeto para JSON
            prod_dict = {
                "id_produto": produto.id_produto,
                "nome": produto.nome,
                "preco": produto.preco_atual,
                "estoque": produto.estoque_total
            }
            # Grava no Redis com TTL de 60 segundos
            self.redis.setex(chave, 60, json.dumps(prod_dict))
            self._incrementar_ranking(produto_id)
            return "MISS", prod_dict
            
        return "MISS", None

    # Demanda 2: Carrinho Temporário de Compras
    def adicionar_ao_carrinho(self, cliente_id: int, produto_id: int, quantidade: int):
        chave = f"dev:ecommerce:carrinho:cliente:{cliente_id}"
        self.redis.hset(chave, str(produto_id), quantidade)
        # Renova o TTL para 900 segundos (15 min) a cada inserção
        self.redis.expire(chave, 900)

    def visualizar_carrinho(self, cliente_id: int):
        chave = f"dev:ecommerce:carrinho:cliente:{cliente_id}"
        return self.redis.hgetall(chave)

    # Demanda 3: Produtos Mais Consultados (Ranking)
    def _incrementar_ranking(self, produto_id: int):
        chave = "dev:ecommerce:ranking:produtos:consultas"
        self.redis.zincrby(chave, 1, str(produto_id))

    def obter_ranking(self):
        chave = "dev:ecommerce:ranking:produtos:consultas"
        # Retorna ordenado do maior pro menor, com os scores (pontuação)
        return self.redis.zrevrange(chave, 0, -1, withscores=True)