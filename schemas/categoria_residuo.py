from marshmallow import Schema, fields

from schemas.retorno import RetornoSchema



# argumentos de pesquisa de publicação
class SearchSchema(Schema):
    descricao = fields.Str(required=False)


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
    

class CategoriaSchema(PlainCategoriaSchema):
    residuo = fields.List(fields.Nested(PlainResiduoSchema()), dump_only=True)
   

class RetornoCategoriaSchema(RetornoSchema):
    values= fields.Nested(CategoriaSchema())
  

class ResiduoSchema(PlainResiduoSchema):
    categoria = fields.List(fields.Nested(PlainCategoriaSchema), required=True)
    
    
class ResiduoPostSchema(PlainResiduoSchema):
    categoria = fields.List(fields.Nested(ItemCategoriaSchema), required=True)
    

class RetornoResiduoSchema(RetornoSchema):
    value = fields.Nested(ResiduoSchema())
  


# argumentos d epesquisa
class ResiduoSearchSchema(Schema):
    categoria_id = fields.Int(required=False)
    recolhe_ecoponto = fields.Bool(required=False)
    descricao = fields.Str(required=False)
