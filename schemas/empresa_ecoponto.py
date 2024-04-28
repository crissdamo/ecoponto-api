from marshmallow import Schema, fields, validate
from models.enums.dia_semana import DiasSemanaEnum
from models.enums.situacao_ecoponto import SituacaoEnum
from schemas.categoria_residuo import ItemResiduoSchema, PlainResiduoSchema
from schemas.termo import ItemTermoSchema


class PlainEcopontoLocalizacaoSchema(Schema):
    id = fields.Int(dump_only=True)
    rua = fields.Str(required=True)
    numero = fields.Str(required=True)
    bairro = fields.Str(required=True)
    cep = fields.Str(required=True)
    cidade = fields.Str(required=True)
    estado = fields.Str(required=True)
    complemento = fields.Str(required=False)
    latitude = fields.Str(required=True)
    longitude = fields.Str(required=True)
    url_localizacao = fields.Str(required=False, dump_only=True)    


class PainEcopontoDiaFuncionamento(Schema):
    id = fields.Int(dump_only=True)
    dia_semana = fields.Str(validate=validate.OneOf([s.value for s in DiasSemanaEnum]))
    hora_inicial = fields.Time(format='%H:%M', required=True)
    hora_final = fields.Time(format='%H:%M', required=True)


class PlainEmpresaSchema(Schema):
    id = fields.Int(dump_only=True)
    nome_fantasia = fields.Str(required=True)
    razao_social = fields.Str(required=False)
    cnpj = fields.Str(required=True)
    ramo_atuacao = fields.Str(required=False)
    telefone = fields.Str(required=True)
    rede_social = fields.Str(required=False)
    participacao_outros_projetos = fields.Bool(missing=False) 
    descricao_outros_projetos = fields.Str(required=False)
    nome_contato_responsavel = fields.Str(required=True)
    
    email = fields.Str(required=True)
    senha = fields.Str(required=True, load_only=True)

    aceite_termos = fields.List(fields.Nested(ItemTermoSchema), required=False)


class PlainEcopontoSchema(Schema):
    id = fields.Int(dump_only=True)
    empresa_id = fields.Int(required=True)
    situacao = fields.Str(validate=validate.OneOf([s.value for s in SituacaoEnum]), dump_only=True)
    nome = fields.Str(required=True)
    ativo = fields.Boolean(missing=True)
    aberto_publico = fields.Boolean(missing=True)
    data_inicio = fields.Date(format='2024-01-01T00:00:00.019077+00:00', required=False)
    data_final = fields.Date(format='2050-12-31T23:59:59.019077+00:00', required=False)
    localizacao = fields.List(fields.Nested(PlainEcopontoLocalizacaoSchema), required=True)

    dia_funcionamento = fields.List(fields.Nested(PainEcopontoDiaFuncionamento), required=False)
    residuo = fields.List(fields.Nested(ItemResiduoSchema), required=False)


class EcopontoFuncionamentoSchema(Schema):
    ecoponto_id = fields.Int(required=True)
    dia_funcionamento = fields.List(fields.Nested(PainEcopontoDiaFuncionamento), required=True)
    ecoponto = fields.Nested(PlainEcopontoSchema(), dump_only=True)
    

class EcopontoResiduoSchema(Schema):
    ecoponto_id = fields.Int(required=True)
    # descricao_outros_projetos = fields.Str(required=True)
    residuo = fields.List(fields.Nested(PlainResiduoSchema), required=True)
    ecoponto = fields.Nested(PlainEcopontoSchema(), dump_only=True)
    

class EcopontoSchema(PlainEcopontoSchema):
    residuo = fields.List(fields.Nested(PlainResiduoSchema()), dump_only=True)
    localizacao = fields.List(fields.Nested(PlainEcopontoLocalizacaoSchema()), dump_only=True)
    dia_funcionamento = fields.List(fields.Nested(PainEcopontoDiaFuncionamento), dump_only=True)
    

class EcopontoEmpresaSchema(PlainEcopontoSchema):
    empresa = fields.Nested(PlainEmpresaSchema(), dump_only=True)
    residuo = fields.List(fields.Nested(PlainResiduoSchema()), dump_only=True)
    localizacao = fields.List(fields.Nested(PlainEcopontoLocalizacaoSchema()), dump_only=True)
    dia_funcionamento = fields.List(fields.Nested(PainEcopontoDiaFuncionamento), dump_only=True)


class EmpresaSchema(PlainEmpresaSchema):
    ecopontos = fields.List(fields.Nested(EcopontoSchema()), dump_only=True)


# class EmpresaUpdateSchema(Schema):
#     nome_fantasia  = fields.Str()
#     razao_social = fields.Str()
#     cnpj = fields.Str()
#     ramo_atuacao = fields.Str()
#     telefone = fields.Str()
#     rede_social = fields.Str()
#     participacao_outros_projetos = fields.Boolean() 
#     descricao_outros_projetos = fields.Str()
#     nome_contato_responsavel = fields.Str()
#     email = fields.Str()



# class EcopontoUpdateSchema(Schema):
#     nome = fields.Str()
#     situacao = fields.Str()
#     ativo = fields.Boolean()
#     aberto_publico = fields.Boolean()
#     data_inicio: fields.DateTime() # type: ignore
#     data_final: fields.Date() # type: ignore



