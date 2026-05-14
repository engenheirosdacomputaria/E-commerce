"""Controller principal.

Responsável por coordenar View e Model.
"""

from __future__ import annotations

from pathlib import Path

from src.models.config_loader import ConfigLoader
from src.models.mongo_manager import MongoManager
from src.models.migration_service import MigrationService
from src.models.query_service import QueryService
from src.models.sqlite_manager import SQLiteManager
from src.models.sqlite_repository import SQLiteRepository
from src.views.menu_view import MenuView
from src.models.redis_manager import RedisManager
from src.models.redis_service import RedisService

class AppController:
    def __init__(self) -> None:
        self.project_root = Path(__file__).resolve().parents[2]

        config_loader = ConfigLoader(self.project_root)
        sqlite_cfg = config_loader.load_sqlite_config()
        mongo_cfg = config_loader.load_mongodb_config()

        self.sqlite_cfg = sqlite_cfg
        self.mongo_cfg = mongo_cfg

        self.sqlite_manager = SQLiteManager(sqlite_cfg["db_path"])
        self.sqlite_repository = SQLiteRepository(self.sqlite_manager)
        self.mongo_manager = MongoManager(
            uri=mongo_cfg["uri"],
            database_name=mongo_cfg["database"],
            use_mongomock_on_failure=mongo_cfg["use_mongomock_on_failure"],
        )
        self.migration_service = MigrationService(self.sqlite_repository, self.mongo_manager)
        self.query_service = QueryService(self.mongo_manager)
        self.view = MenuView()
        self.redis_manager = RedisManager() 
        self.redis_service = RedisService(self.redis_manager, self.sqlite_repository)

    def run(self) -> None:
        while True:
            try:
                self.view.show_menu()
                option = self.view.ask_option()

                if option == "1":
                    self._test_sqlite()
                elif option == "2":
                    self._recreate_sqlite()
                elif option == "3":
                    self._test_mongo()
                elif option == "4":
                    self._recreate_mongo_collections()
                elif option == "5":
                    self._migrate()
                elif option == "6":
                    self._show_samples()
                elif option == "7":
                    self._run_example_queries()
                elif option == "8":
                    self._show_config_paths()
                elif option == "9":
                    self._consultar_produto_redis()
                elif option == "10":
                    self._gerenciar_carrinho()
                elif option == "11":
                    self._visualizar_carrinho()
                elif option == "12":
                    self._ver_ranking()
                elif option == "0":
                    self.view.show_message("Encerrando o sistema.")
                    break
                else:
                    self.view.show_error("Opção inválida.")
            except Exception as exc:
                self.view.show_error(str(exc))

    def _consultar_produto_redis(self):
        prod_id = input("Digite o ID do produto: ")
        produto = self.redis_service.buscar_produto_com_cache(prod_id)
        if produto:
            print(f"Produto Encontrado: {produto['nome']} | Preço: R${produto['preco_atual']} | Estoque: {produto['estoque_total']}")
        else:
            print("Produto não encontrado.")

    def _gerenciar_carrinho(self):
        cliente_id = input("ID do Cliente: ")
        produto_id = input("ID do Produto: ")
        qtd = int(input("Quantidade: "))
        sucesso, msg = self.redis_service.adicionar_ao_carrinho(cliente_id, produto_id, qtd)
        print(msg)

    def _visualizar_carrinho(self):
        cliente_id = input("ID do Cliente: ")
        itens, total = self.redis_service.ver_carrinho(cliente_id)
        print(f"\n--- Carrinho do Cliente {cliente_id} ---")
        if not itens:
            print("Carrinho vazio ou expirado.")
        else:
            for item in itens:
                print(f"- {item['nome']} (Qtd: {item['quantidade']}) -> Subtotal: R${item['subtotal']:.2f}")
            print(f"TOTAL: R${total:.2f}")
        print("-----------------------------------")

    def _ver_ranking(self):
        ranking = self.redis_service.ver_ranking()
        print("\n--- Ranking de Consultas ---")
        if not ranking:
            print("Nenhuma consulta registrada ainda.")
        else:
            for i, p in enumerate(ranking, 1):
                print(f"{i}º | {p['nome']} (R${p['preco']}) - {p['total_consultas']} consultas")

    def _test_sqlite(self) -> None:
        ok, message = self.sqlite_manager.test_connection()
        if ok:
            self.view.show_success(message)
        else:
            self.view.show_error(message)

    def _recreate_sqlite(self) -> None:
        self.view.show_message("Recriando e populando o SQLite...")
        self.sqlite_manager.recreate_database()
        self.view.show_success("SQLite recriado e populado com dados fictícios.")

    def _test_mongo(self) -> None:
        ok, message = self.mongo_manager.test_connection()
        if ok:
            self.view.show_success(message)
            if self.mongo_manager.using_mock:
                self.view.show_message(
                    "Observação: o sistema está usando mongomock em memória; "
                    "validators não serão aplicados."
                )
        else:
            self.view.show_error(message)

    def _recreate_mongo_collections(self) -> None:
        message = self.mongo_manager.recreate_collections_with_schema()
        self.view.show_success(message)

    def _migrate(self) -> None:
        result = self.migration_service.migrate()
        self.view.show_success(
            "Migração concluída. "
            f"Produtos: {result['produtos']} | "
            f"Documentos em pedidos: {result['pedidos']} | "
            f"Pedidos de origem: {result['pedidos_origem']}"
        )

    def _show_samples(self) -> None:
        self.view.show_documents("Produtos (amostra)", self.query_service.sample_produtos())
        self.view.show_documents(
            "Pedidos simplificados (1 documento por item)",
            self.query_service.sample_pedidos(),
        )

    def _run_example_queries(self) -> None:
        self.view.show_documents("[1] Pedidos com status pago", self.query_service.example_filter_paid_orders())
        self.view.show_documents(
            "[2] Pedidos cuja cidade de entrega seja Curitiba",
            self.query_service.example_projection_curitiba(),
        )
        updated = self.query_service.example_update_first_order()
        if updated is None:
            self.view.show_message("[3] Nenhum pedido encontrado para atualizar.")
        else:
            self.view.show_documents("[3] Atualização do primeiro pedido", [updated])
        self.view.show_documents(
            "[4] Produtos mais vendidos",
            self.query_service.example_aggregation_best_sellers(),
        )
        self.view.show_documents(
            "[5] Paginação de pedidos: página 2, tamanho 5",
            self.query_service.example_pagination(),
        )

    def _show_config_paths(self) -> None:
        self.view.show_message("\nArquivos de configuração carregados:")
        self.view.show_message(f"SQLite ini: {self.sqlite_cfg['source_file']}")
        self.view.show_message(f"SQLite db : {self.sqlite_cfg['db_path']}")
        self.view.show_message(f"Mongo ini : {self.mongo_cfg['source_file']}")
        self.view.show_message(f"Mongo uri : {self.mongo_cfg['uri']}")
        self.view.show_message(f"Database  : {self.mongo_cfg['database']}")
