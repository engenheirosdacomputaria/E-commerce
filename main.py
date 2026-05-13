"""Ponto de entrada da aplicação.

Este arquivo apenas inicia o controller principal.
A ideia é manter a inicialização simples e fácil de localizar.
"""

from src.controllers.app_controller import AppController


if __name__ == "__main__":
    AppController().run()
