"""Classes de domínio.

Estas classes representam o negócio e não dependem diretamente
nem do SQLite nem do MongoDB.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(slots=True)
class Cliente:
    id_cliente: int
    nome: str
    email: str
    cpf: Optional[str] = None
    telefone: Optional[str] = None


@dataclass(slots=True)
class EnderecoSnapshot:
    logradouro: str
    numero: str
    bairro: str
    cidade: str
    estado: str
    cep: str
    complemento: Optional[str] = None


@dataclass(slots=True)
class Pagamento:
    tipo_pagamento: str
    status_pagamento: str
    valor_pago: float
    parcelas: int
    codigo_transacao: Optional[str] = None
    data_pagamento: Optional[str] = None


@dataclass(slots=True)
class Entrega:
    status_entrega: str
    transportadora: str
    codigo_rastreio: str
    endereco_snapshot: EnderecoSnapshot


@dataclass(slots=True)
class ItemPedido:
    id_produto: int
    produto_ref: int
    id_variacao: Optional[int]
    nome_produto: str
    sku: Optional[str]
    variacao_snapshot: Optional[str]
    categoria: str
    quantidade: int
    preco_unitario_compra: float
    subtotal: float
    atributos_snapshot: Optional[dict] = None


@dataclass(slots=True)
class Pedido:
    id_pedido: int
    data_pedido: str
    status_pedido: str
    cliente_ref: int
    cliente: Cliente
    cupom: Optional[dict]
    pagamento: Optional[Pagamento]
    entrega: Optional[Entrega]
    itens: list[ItemPedido] = field(default_factory=list)
    valor_produtos: float = 0.0
    valor_frete: float = 0.0
    valor_desconto: float = 0.0
    valor_total: float = 0.0


@dataclass(slots=True)
class Vendedor:
    id_vendedor: int
    nome_loja: str
    ativo: bool


@dataclass(slots=True)
class ResumoAvaliacao:
    qtd_avaliacoes: int
    media_notas: float


@dataclass(slots=True)
class Produto:
    id_produto: int
    nome: str
    descricao: str
    preco_atual: float
    ativo: bool
    vendedor: Vendedor
    categorias: list[str] = field(default_factory=list)
    estoque_total: int = 0
    estoque_reservado: int = 0
    resumo_avaliacao: ResumoAvaliacao = field(default_factory=lambda: ResumoAvaliacao(0, 0.0))