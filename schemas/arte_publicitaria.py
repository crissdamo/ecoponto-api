from marshmallow import Schema, fields

from schemas.paginacao import PaginacaoSchema, PaginacaoSearchSchema
from schemas.retorno import RetornoSchema


# argumentos de pesquisa
class ArtePublicitariaSearchSchema(PaginacaoSearchSchema):
    residuo_id = fields.Int(required=False)
    ecoponto_id = fields.Int(required=False)


class PlainArtePublicitariaSchema(Schema):
    id = fields.Int(dump_only=True)
    descricao = fields.Str(required=True)
    url_midia = fields.Str(required=False)
    disponibilizar_ecoponto = fields.Boolean(missing=True)
    ativo = fields.Boolean(missing=True)
    data_inicio = fields.Date(format='2024-01-01T00:00:00.019077+00:00', required=False)
    data_final = fields.Date(format='2050-12-31T23:59:59.019077+00:00', required=False)
    residuo_id = fields.Int(required=False)


# Devolve uma publicações no padrão de retorno estabelecido
class PlainArtePublicitariaGetSchema (RetornoSchema):
    value = fields.Nested(PlainArtePublicitariaSchema)


# Devolve uma lista publicações no padrão de retorno estabelecido
class PlainArtePublicitariaGetListSchema (RetornoSchema):
    values = fields.List(fields.Nested(PlainArtePublicitariaSchema()))
    pagination = fields.List(fields.Nested(PaginacaoSchema()), dump_only=True)

