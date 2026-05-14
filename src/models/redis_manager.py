import fakeredis

class RedisManager:
    # Mantemos os parâmetros host e port na assinatura para não quebrar o controller,
    # mas o FakeRedis vai ignorá-los e rodar tudo apenas na memória.
    def __init__(self, host='localhost', port=6379, db=0):
        # AQUI É A MUDANÇA PRINCIPAL:
        self.client = fakeredis.FakeRedis(decode_responses=True)

    def test_connection(self) -> tuple[bool, str]:
        try:
            if self.client.ping():
                return True, "Conexão com FakeRedis (Sem Docker) estabelecida com sucesso."
        except Exception as e:
            return False, f"Falha ao conectar no FakeRedis: {e}"