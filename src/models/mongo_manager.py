from __future__ import annotations
from pymongo import MongoClient
import mongomock

from src.models.mongo_schemas import pedido_validator, produto_validator


class MongoManager:
    def __init__(self, uri: str, database_name: str, use_mongomock_on_failure: bool = True) -> None:
        self.uri = uri
        self.database_name = database_name
        self.use_mongomock_on_failure = use_mongomock_on_failure
        self.client: MongoClient | None = None
        self.db = None
        self.using_mock = False

    def connect(self) -> tuple[bool, str]:
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            self.client.admin.command("ping")
            self.db = self.client[self.database_name]
            self.using_mock = False
            return True, f"Conexão MongoDB real OK. Banco: {self.database_name}"
        except Exception as exc:
            if not self.use_mongomock_on_failure:
                return False, f"Falha no MongoDB: {exc}"

            try:
                self.client = mongomock.MongoClient()
                self.db = self.client[self.database_name]
                self.using_mock = True
                return True, (
                    "MongoDB real indisponível. "
                    "Projeto usando mongomock em memória."
                )
            except Exception as mock_exc:
                return False, f"Falha no MongoDB real e no mongomock: {mock_exc}"

    def ensure_connected(self) -> None:
        if self.db is None:
            ok, message = self.connect()
            if not ok:
                raise RuntimeError(message)

    def test_connection(self) -> tuple[bool, str]:
        return self.connect()

    def recreate_collections_with_schema(self) -> str:
        self.ensure_connected()
        assert self.db is not None

        for name in ["pedidos", "produtos"]:
            try:
                self.db.drop_collection(name)
            except Exception:
                pass

        if self.using_mock:
            self.db.create_collection("pedidos")
            self.db.create_collection("produtos")
            return (
                "Coleções criadas sem validator, pois a aplicação está usando mongomock. "
                "No MongoDB real, os validators com $jsonSchema seriam aplicados."
            )

        self.db.create_collection(
            "pedidos",
            validator=pedido_validator(),
            validationLevel="strict",
            validationAction="error",
        )
        self.db.create_collection(
            "produtos",
            validator=produto_validator(),
            validationLevel="strict",
            validationAction="error",
        )
        return (
            "Coleções V3 criadas com $jsonSchema, "
            "validationLevel='strict' e validationAction='error'. "
            "Pedidos: u documento por pedido, com subdocumentos cliente, "
            "itens (array), pagamento e entrega."
        )

    @property
    def pedidos(self):
        self.ensure_connected()
        return self.db["pedidos"]

    @property
    def produtos(self):
        self.ensure_connected()
        return self.db["produtos"]