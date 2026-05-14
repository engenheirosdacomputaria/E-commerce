import json
import logging

class RedisService:
    def __init__(self, redis_manager, sqlite_repository):
        self.manager = redis_manager
        self.redis = redis_manager.get_client()
        self.sqlite = sqlite_repository

    # ==========================================
    # Demanda 1: Cache-aside de Produtos [cite: 8]
    # ==========================================
    def buscar_produto_com_cache(self, produto_id):
        chave = self.manager.nome_chave("produto", "cache", produto_id) # [cite: 24]
        
        # Tenta buscar no Redis primeiro
        produto_json = self.redis.get(chave)
        
        if produto_json:
            logging.info(f"CACHE HIT para o produto {produto_id}") # [cite: 45]
            self.registrar_consulta(produto_id) # Atualiza o ranking de consultas
            return json.loads(produto_json)
            
        logging.info(f"CACHE MISS para o produto {produto_id}. Buscando no SQLite...") # [cite: 45]
        
        # Busca no SQLite (Fonte de verdade) [cite: 26, 39]
        produto_db = self.sqlite.find_produto_by_id(produto_id)
        
        if produto_db:
            # Salva no Redis (String com JSON + TTL de 60s) [cite: 20, 24]
            self.redis.setex(chave, 60, json.dumps(produto_db))
            self.registrar_consulta(produto_id) # Atualiza o ranking [cite: 49]
            return produto_db
            
        return None

    # ==========================================
    # Demanda 2: Carrinho Temporário [cite: 12]
    # ==========================================
    def adicionar_ao_carrinho(self, cliente_id, produto_id, quantidade):
        # Validação na fonte de verdade (SQLite) 
        produto = self.sqlite.find_produto_by_id(produto_id)
        if not produto:
            return False, "Produto inexistente." # [cite: 47]
            
        if produto['estoque_total'] < quantidade:
            return False, "Quantidade maior que o estoque disponível." # [cite: 47]

        chave_carrinho = self.manager.nome_chave("carrinho", f"cliente:{cliente_id}") # [cite: 24]
        campo_produto = f"produto:{produto_id}"
        
        # Adiciona ao Hash (Hash + TTL de 900s) [cite: 20, 24]
        self.redis.hincrby(chave_carrinho, campo_produto, quantidade)
        self.redis.expire(chave_carrinho, 900)
        
        return True, "Produto adicionado ao carrinho com sucesso!" # [cite: 47]

    def ver_carrinho(self, cliente_id):
        chave_carrinho = self.manager.nome_chave("carrinho", f"cliente:{cliente_id}") # [cite: 24]
        itens_hash = self.redis.hgetall(chave_carrinho)
        
        carrinho_completo = []
        total = 0.0
        
        for campo, qtd_str in itens_hash.items():
            # campo formato: "produto:1"
            prod_id = campo.split(":")[1]
            qtd = int(qtd_str)
            
            # Detalhes buscados no SQL na exibição [cite: 28]
            produto_detalhes = self.sqlite.find_produto_by_id(prod_id)
            if produto_detalhes:
                subtotal = produto_detalhes['preco_atual'] * qtd
                total += subtotal
                carrinho_completo.append({
                    "nome": produto_detalhes['nome'],
                    "preco_unitario": produto_detalhes['preco_atual'],
                    "quantidade": qtd,
                    "subtotal": subtotal
                })
                
        return carrinho_completo, total # [cite: 47]

    # ==========================================
    # Demanda 3: Produtos Mais Consultados [cite: 16]
    # ==========================================
    def registrar_consulta(self, produto_id):
        chave_ranking = self.manager.nome_chave("ranking", "produtos:consultas") # [cite: 24]
        # Sorted Set (ZINCRBY) - Incrementa o score do produto [cite: 20]
        self.redis.zincrby(chave_ranking, 1, f"produto:{produto_id}")

    def ver_ranking(self):
        chave_ranking = self.manager.nome_chave("ranking", "produtos:consultas") # [cite: 24]
        # Sorted Set (ZREVRANGE) - Busca do maior score para o menor [cite: 20]
        ranking = self.redis.zrevrange(chave_ranking, 0, -1, withscores=True)
        
        resultado = []
        for membro, score in ranking:
            prod_id = membro.split(":")[1]
            # Nome e preco consultados ao exibir o ranking [cite: 28]
            produto_detalhes = self.sqlite.find_produto_by_id(prod_id)
            if produto_detalhes:
                resultado.append({
                    "nome": produto_detalhes['nome'],
                    "preco": produto_detalhes['preco_atual'],
                    "total_consultas": int(score)
                })
        return resultado # [cite: 49]