from marshmallow import Schema, fields


class ItemCategoriaSchema(Schema):
    id = fields.Int(required=True)


class ItemResiduoSchema(Schema):
    id = fields.Int(required=True)


class PlainCategoriaSchema(Schema):
    id = fields.Int(dump_only=True)
    descricao = fields.Str(required=True)
    icone = fields.Str(required=False)
    url_midia = fields.Str(required=False)
    ativo = fields.Bool(dump_only=True)

    # residuo = fields.List(fields.Nested(ItemResiduoSchema), required=False)
    

class PlainResiduoSchema(Schema):
    id = fields.Int(dump_only=True)
    descricao = fields.Str(required=True)
    icone = fields.Str(required=False)
    url_midia = fields.Str(required=False)
    recolhido_em_ecoponto = fields.Bool(missing=True)
    ativo = fields.Bool(dump_only=True)

    # categorias = fields.List(fields.Nested(ItemCategoriaSchema), required=False)
    

class CategoriaSchema(PlainResiduoSchema):
    residuo = fields.List(fields.Nested(PlainResiduoSchema()), dump_only=True)
   
    
class ResiduoSchema(PlainResiduoSchema):
    categoria = fields.List(fields.Nested(ItemCategoriaSchema), required=True)
    

