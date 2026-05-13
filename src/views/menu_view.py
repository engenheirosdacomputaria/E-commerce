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
        print("0. Sair")
        print("=" * 72)

    def ask_option(self) -> str:
        return input("Escolha uma opção: ").strip()

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
