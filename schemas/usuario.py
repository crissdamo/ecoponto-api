
from marshmallow import Schema, fields

from schemas.categoria_residuo import RetornoSchema


class EmpresaUsuarioSchema(Schema):
    id = fields.Int(dump_only=True)
    nome_fantasia = fields.Str(required=True)

class PlainTokenSchema(Schema):
    access_token = fields.Str()
    refresh_token = fields.Str()

class PlainUsuarioLoginSchema(Schema):
    id = fields.Int(dump_only=True)
    email = fields.Str(required=True)
    senha = fields.Str(required=True, load_only=True)

class UsuarioSchema(PlainUsuarioLoginSchema):
    nome = fields.Str(required=True)
    telefone = fields.Str(required=False)
    ativo = fields.Bool(dump_only=True)

class UsuarioTiposSchema(UsuarioSchema):
    admin = fields.Bool(dump_only=True)
    equipe = fields.Bool(dump_only=True)
    sistema = fields.Bool(dump_only=True)
    
class UsuarioTokenSchema(UsuarioTiposSchema):
    id = fields.Int()
    email = fields.Str()
    nome = fields.Str()
    empresa = fields.Nested(EmpresaUsuarioSchema)
    token = fields.Nested(PlainTokenSchema)

class UsuarioReturnSchema(RetornoSchema):
    value = fields.Nested(UsuarioTiposSchema)

class UsuarioReturnTokenSchema(RetornoSchema):
    value = fields.Nested(UsuarioTokenSchema)