
from marshmallow import Schema, fields


class PlainUsuarioSchema(Schema):
    id = fields.Int(dump_only=True)
    email = fields.Str(required=True)
    senha = fields.Str(required=True, load_only=True)
    ativo = fields.Bool(dump_only=True)
