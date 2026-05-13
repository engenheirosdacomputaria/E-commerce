"""Camada de View.

Nesta aplicação de console, a View é responsável por:
- exibir o menu;
- pedir opções ao usuário;
- mostrar mensagens e resultados.
"""

from __future__ import annotations

from pprint import pprint
from typing import Iterable, Any


class MenuView:
    def show_menu(self) -> None:
        print("\n" + "=" * 72)
        print(" Laboratório de migração — SQLite + MongoDB + MVC + domínio")
        print("=" * 72)
        print("1. Testar configuração do SQLite")
        print("2. Recriar e popular SQLite")
        print("3. Testar configuração do MongoDB")
        print("4. Recriar coleções Mongo com schema")
        print("5. Migrar SQLite -> Mongo (modelo simplificado e achatado)")
        print("6. Mostrar amostra de documentos")
        print("7. Executar consultas de exemplo")
        print("8. Mostrar caminhos de configuração carregados")
        print("--- Redis ---")
        print("9.  Testar configuração do Redis")
        print("10. Consultar produto por ID (cache-aside)")
        print("11. Adicionar produto ao carrinho")
        print("12. Visualizar carrinho")
        print("13. Exibir ranking de produtos mais consultados")
        print("0. Sair")
        print("=" * 72)

    def ask_option(self) -> str:
        return input("Escolha uma opção: ").strip()

    def ask_int(self, prompt: str) -> int:
        while True:
            try:
                return int(input(prompt).strip())
            except ValueError:
                print("[ERRO] Digite um número inteiro válido.")

    def show_message(self, message: str) -> None:
        print(message)

    def show_error(self, message: str) -> None:
        print(f"[ERRO] {message}")

    def show_success(self, message: str) -> None:
        print(f"[OK] {message}")

    def show_documents(self, title: str, documents: Iterable[Any]) -> None:
        print(f"\n=== {title} ===")
        found = False
        for doc in documents:
            pprint(doc)
            found = True
        if not found:
            print("Nenhum documento encontrado.")

    def show_produto(self, produto: dict) -> None:
        print("\n=== Produto ===")
        print(f"  ID      : {produto['id_produto']}")
        print(f"  Nome    : {produto['nome']}")
        print(f"  Preço   : R$ {produto['preco_atual']:.2f}")
        print(f"  Estoque : {produto['estoque_total']}")

    def show_carrinho(self, itens: list[dict]) -> None:
        print("\n=== Carrinho ===")
        if not itens:
            print("  Carrinho vazio.")
            return
        total = 0.0
        for item in itens:
            print(
                f"  {item['nome']} | "
                f"R$ {item['preco_unitario']:.2f} x {item['quantidade']} = "
                f"R$ {item['subtotal']:.2f}"
            )
            total += item["subtotal"]
        print(f"  Total: R$ {total:.2f}")

    def show_ranking(self, ranking: list[dict]) -> None:
        print("\n=== Ranking de Produtos Mais Consultados ===")
        if not ranking:
            print("  Nenhuma consulta registrada ainda.")
            return
        for i, item in enumerate(ranking, start=1):
            print(
                f"  {i}. {item['nome']} | "
                f"R$ {item['preco_atual']:.2f} | "
                f"Consultas: {item['total_consultas']}"
            )