"""Gerenciamento de conexão com o Redis."""

from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path

import redis


AMBIENTE = "dev"
APLICACAO = "ecommerce"
PREFIXO_CHAVE = f"{AMBIENTE}:{APLICACAO}"


def nome_chave(*partes: object) -> str:
    """Monta uma chave Redis padronizada.

    Exemplo:
        nome_chave("produto", "cache", 1)
        -> "dev:ecommerce:produto:cache:1"
    """
    return ":".join([PREFIXO_CHAVE, *[str(parte) for parte in partes]])


class RedisManager:
    def __init__(self, host: str, port: int, db: int, use_fakeredis_on_failure: bool = True) -> None:
        self.host = host
        self.port = port
        self.db = db
        self.use_fakeredis_on_failure = use_fakeredis_on_failure
        self.client = None
        self.using_mock = False

    def connect(self) -> tuple[bool, str]:
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True,
            )
            self.client.ping()
            self.using_mock = False
            return True, f"Conexão Redis real OK em {self.host}:{self.port}"
        except Exception as exc:
            if not self.use_fakeredis_on_failure:
                return False, f"Falha no Redis: {exc}"

            try:
                import fakeredis
                self.client = fakeredis.FakeRedis(decode_responses=True)
                self.using_mock = True
                return True, (
                    "Redis real indisponível. "
                    "Projeto usando fakeredis em memória."
                )
            except Exception as mock_exc:
                return False, f"Falha no Redis real e no fakeredis: {mock_exc}"

    def ensure_connected(self) -> None:
        if self.client is None:
            ok, message = self.connect()
            if not ok:
                raise RuntimeError(message)

    def test_connection(self) -> tuple[bool, str]:
        return self.connect()