import redis
import fakeredis
import logging

class RedisManager:
    def __init__(self, host='localhost', port=6379, db=0, use_fake_on_failure=True, prefix="dev:ecommerce"):
        self.host = host
        self.port = port
        self.db = db
        self.use_fake_on_failure = use_fake_on_failure
        self.prefix = prefix # Prefixo fixo: dev:ecommerce [cite: 23, 34]
        self.client = None
        self.connect()

    def connect(self):
        try:
            self.client = redis.Redis(host=self.host, port=self.port, db=self.db, decode_responses=True)
            self.client.ping()
            logging.info("Conectado ao Redis com sucesso.")
        except redis.ConnectionError:
            logging.warning("Falha ao conectar ao Redis real.")
            if self.use_fake_on_failure:
                logging.info("Iniciando FakeRedis (modo mock).")
                self.client = fakeredis.FakeRedis(decode_responses=True)
            else:
                raise Exception("Redis não está disponível e o fallback (FakeRedis) está desativado.")

    def get_client(self):
        if not self.client:
            self.connect()
        return self.client

    def nome_chave(self, dominio, finalidade, identificador=None):
        """Monta a chave no padrão: ambiente:aplicacao:dominio:finalidade:{id}"""
        # Ex: dev:ecommerce:produto:cache:1 [cite: 22, 24]
        base = f"{self.prefix}:{dominio}:{finalidade}"
        return f"{base}:{identificador}" if identificador else base