from __future__ import annotations


def pedido_validator() -> dict:
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": [
                "_id",
                "data_pedido",
                "status_pedido",
                "cliente",
                "itens",
                "valor_total",
                "pagamento",
                "entrega",
            ],
            "additionalProperties": False,
            "properties": {
                "_id": {
                    "bsonType": ["int", "long"],
                    "description": "Identificador único do pedido.",
                },
                "data_pedido": {
                    "bsonType": "string",
                    "description": "Data/hora da criação do pedido (ISO-8601).",
                },
                "status_pedido": {
                    "enum": ["pendente", "pago", "cancelado", "entregue"],
                    "description": "Estado geral do pedido.",
                },

                "cliente": {
                    "bsonType": "object",
                    "required": ["id_cliente", "nome", "email"],
                    "additionalProperties": False,
                    "properties": {
                        "id_cliente": {"bsonType": ["int", "long"]},
                        "nome":       {"bsonType": "string"},
                        "email":      {"bsonType": "string"},
                        "cpf":        {"bsonType": ["string", "null"]},
                        "telefone":   {"bsonType": ["string", "null"]},
                    },
                },

                "itens": {
                    "bsonType": "array",
                    "minItems": 1,
                    "description": "Pelo menos um item por pedido.",
                    "items": {
                        "bsonType": "object",
                        "required": [
                            "id_produto",
                            "nome_produto",
                            "quantidade",
                            "valor_unitario",
                            "subtotal",
                        ],
                        "additionalProperties": False,
                        "properties": {
                            # snapshot do produto — preservado mesmo que o
                            # cadastro do produto seja alterado no futuro
                            "id_produto":    {"bsonType": ["int", "long"]},
                            "nome_produto":  {"bsonType": "string"},
                            "categoria":     {"bsonType": ["string", "null"]},
                            "quantidade": {
                                "bsonType": ["int", "long"],
                                "minimum": 1,
                            },
                            "valor_unitario": {
                                "bsonType": ["double", "int", "long", "decimal"],
                                "minimum": 0,
                            },
                            "subtotal": {
                                "bsonType": ["double", "int", "long", "decimal"],
                                "minimum": 0,
                            },
                        },
                    },
                },

                "valor_total": {
                    "bsonType": ["double", "int", "long", "decimal"],
                    "minimum": 0,
                    "description": "Soma dos subtotais de todos os itens.",
                },

                "pagamento": {
                    "bsonType": "object",
                    "required": ["metodo", "status"],
                    "additionalProperties": False,
                    "properties": {
                        "metodo": {
                            "enum": [
                                "cartao_credito",
                                "cartao_debito",
                                "pix",
                                "boleto",
                                "dinheiro",
                            ]
                        },
                        "status": {
                            "enum": ["pendente", "aprovado", "recusado", "estornado"]
                        },
                        "data_pagamento": {"bsonType": ["string", "null"]},
                    },
                },

                "entrega": {
                    "bsonType": "object",
                    "required": ["cidade", "estado", "status_entrega"],
                    "additionalProperties": False,
                    "properties": {
                        "endereco":        {"bsonType": ["string", "null"]},
                        "cidade":          {"bsonType": "string"},
                        "estado":          {"bsonType": "string"},
                        "cep":             {"bsonType": ["string", "null"]},
                        "status_entrega": {
                            "enum": [
                                "aguardando",
                                "em_separacao",
                                "em_transito",
                                "entregue",
                                "devolvido",
                            ]
                        },
                        "previsao_entrega": {"bsonType": ["string", "null"]},
                    },
                },
            },
        }
    }


def produto_validator() -> dict:
    """Schema da coleção produtos — sem alterações em relação à Versão 2.

    Os dados do produto são copiados (snapshot) para cada item do pedido
    no momento da compra, portanto o cadastro de produto pode evoluir
    independentemente sem afetar pedidos históricos.
    """
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_id", "nome", "preco_atual", "ativo"],
            "properties": {
                "_id": {"bsonType": ["int", "long"]},
                "nome": {"bsonType": "string"},
                "descricao": {"bsonType": "string"},
                "preco_atual": {
                    "bsonType": ["double", "int", "long", "decimal"],
                    "minimum": 0,
                },
                "ativo": {"bsonType": "bool"},
                "vendedor_nome": {"bsonType": "string"},
                "categorias": {
                    "bsonType": "array",
                    "items": {"bsonType": "string"},
                },
                "estoque_total": {"bsonType": ["int", "long"], "minimum": 0},
                "media_avaliacao": {
                    "bsonType": ["double", "int", "long", "decimal"],
                    "minimum": 0,
                },
            },
        }
    }