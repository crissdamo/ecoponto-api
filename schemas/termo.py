from marshmallow import Schema, fields, validate


class ItemTermoSchema(Schema):
    id = fields.Int(required=True)
    aceite = fields.Bool(missing=False)


class PlainTermoSchema(Schema):
    id = fields.Int(dump_only=True)
    titulo = fields.Str(required=True)
    descricao = fields.Str(required=True)
    ativo = fields.Bool(missing=True) 


class AceiteTermoSchema(Schema):
    id = fields.Int(dump_only=True)
    id_termo = fields.Int(required=True)
    id_empresa = fields.Int(required=True)
    aceite = fields.Bool(missing=False)
