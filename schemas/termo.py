from marshmallow import Schema, fields

from schemas.retorno import RetornoSchema


# argumentos de pesquisa para termo
class SearchSchema(Schema):
    descricao = fields.Str(required=False)


# Objeto Termo
class PlainTermoSchema(Schema):
    id = fields.Int(dump_only=True)
    titulo = fields.Str(required=True)
    descricao = fields.Str(required=True)
    ativo = fields.Bool(missing=True) 


# Formato de retorno de um objeto termo
class RetornoTermoSchema(RetornoSchema):
    value = fields.Nested(PlainTermoSchema())


# Formato de retorno de uma lista de termos
class RetornoTermoListaSchema(RetornoSchema):
    values = fields.List( fields.Nested(PlainTermoSchema()))


# Post do aceite termo  
class AceiteTermoSchema(Schema):
    id = fields.Int(dump_only=True)
    termo_id = fields.Int(required=True)
    empresa_id = fields.Int(required=True)
    aceite = fields.Bool(missing=False)

