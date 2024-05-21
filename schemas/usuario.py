
from marshmallow import Schema, fields


class PlainUsuarioSchema(Schema):
    id = fields.Int(dump_only=True)
    email = fields.Str(required=True)
    senha = fields.Str(required=True, load_only=True)
    nome = fields.Str(required=True)
    telefone = fields.Str(required=False)
    ativo = fields.Bool(dump_only=True)
