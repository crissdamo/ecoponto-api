
from marshmallow import Schema, fields

# argumentos de pesquisa páginação
class PaginacaoSearchSchema(Schema):
    page = fields.Int(required=False)
    page_size = fields.Int(required=False)

class PaginacaoSchema(PaginacaoSearchSchema):
    total = fields.Int()
    previous = fields.Bool()
    next = fields.Bool()


