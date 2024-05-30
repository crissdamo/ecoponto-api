from marshmallow import Schema, fields

# retorno: classe com a representação padronizada de saída
class RetornoSchema(Schema):
    code = fields.Str(default='200', dump_only=True)
    status = fields.Str(default='OK', dump_only=True)
    message = fields.Str( dump_only=True)

