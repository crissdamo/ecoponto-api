from marshmallow import Schema, fields, validate
from models.enums.situacao_ecoponto import SituacaoEnum
from schemas.paginacao import PaginacaoSchema, PaginacaoSearchSchema
from schemas.retorno import RetornoSchema


# argumentos de pesquisa de publicação
class PublicacaoSearchSchema(PaginacaoSearchSchema):
    residuo_id = fields.Int(required=False)
    categoria_id = fields.Int(required=False)
    ecoponto_id = fields.Int(required=False)
    palavra_chave = fields.Str(required=False)


# Apenas os campos da Publicação
class PlainPublicacaoSchema(Schema):
    id = fields.Int(dump_only=True)
    titulo = fields.Str(required=True)
    descricao = fields.Str(required=True)
    url_media = fields.Str(required=False)
    ativo = fields.Boolean(missing=True)
    data_inicio = fields.Date(format='2024-01-01T00:00:00.019077+00:00', required=False)
    data_final = fields.Date(format='2050-12-31T23:59:59.019077+00:00', required=False)
    categoria_id = fields.Int(required=False)
    residuo_id = fields.Int(required=False)


# Apenas os campos da Seção Publicação
class PlainSecaoPublicacaoSchema(Schema):
    id = fields.Int(dump_only=True)
    titulo = fields.Str(required=True)
    descricao = fields.Str(required=True)
    url_media = fields.Str(required=False)
    ativo = fields.Boolean(missing=True)
    data_inicio = fields.Date(format='2024-01-01T00:00:00.019077+00:00', required=False)
    data_final = fields.Date(format='2050-12-31T23:59:59.019077+00:00', required=False)


# Post Publicação
class PublicacaoPostSchema(PlainPublicacaoSchema):
    secao_publicacao = fields.List(fields.Nested(PlainSecaoPublicacaoSchema()), required=False)


# Publicacao + seções
class PublicacaoSchema(PlainPublicacaoSchema):
    secao_publicacao = fields.List(fields.Nested(PlainSecaoPublicacaoSchema()))


# Devolve uma publicações no padrão de retorno estabelecido
class PublicacaoGetSchema (RetornoSchema):
    value = fields.Nested(PublicacaoSchema)


# Devolve uma lista publicações no padrão de retorno estabelecido
class PublicacaoGetListSchema (RetornoSchema):
    values = fields.List(fields.Nested(PublicacaoSchema()))
    pagination = fields.List(fields.Nested(PaginacaoSchema()), dump_only=True)


# Devolve uma seção da publicações no padrão de retorno estabelecido
class SecaoPublicacaoGetSchema (RetornoSchema):
    value = fields.Nested(PlainSecaoPublicacaoSchema)
