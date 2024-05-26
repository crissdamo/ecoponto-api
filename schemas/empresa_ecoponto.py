from marshmallow import Schema, fields, validate
from models.enums.dia_semana import DiasSemanaEnum
from models.enums.situacao_ecoponto import SituacaoEnum
from schemas.categoria_residuo import ItemResiduoSchema, PlainResiduoSchema
from schemas.paginacao import PaginacaoSchema, PaginacaoSearchSchema
from schemas.termo import AceiteTermoSchema


# Empresa (está implicito o usuário e o perfil do usuário)
class PlainEmpresaUpdateSchema(Schema):

    nome_fantasia = fields.Str(required=False)
    razao_social = fields.Str(required=False)
    cnpj = fields.Str(required=False)
    ramo_atuacao = fields.Str(required=False)
    telefone = fields.Str(required=False)
    rede_social = fields.Str(required=False)
    participacao_outros_projetos = fields.Bool(missing=False) 
    descricao_outros_projetos = fields.Str(required=False)
    nome_contato_responsavel = fields.Str(required=False)
    
    email = fields.Str(required=False)
    senha = fields.Str(required=False, load_only=False)

    aceite_termo = fields.List(fields.Nested(AceiteTermoSchema), required=False)


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

    aceite_termo = fields.List(fields.Nested(AceiteTermoSchema), required=False)


# Localizacao
class PlainLocalizacaoSchema(Schema):
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

class PlainLocalizacaoUpdateSchema(Schema):

    rua = fields.Str(required=False)
    numero = fields.Str(required=False)
    bairro = fields.Str(required=False)
    cep = fields.Str(required=False)
    cidade = fields.Str(required=False)
    estado = fields.Str(required=False)
    complemento = fields.Str(required=False)
    latitude = fields.Str(required=False)
    longitude = fields.Str(required=False)
    url_localizacao = fields.Str(required=False, dump_only=True)    


# Dia funcionamento
class PainEcopontoDiaFuncionamento(Schema):
    id = fields.Int(dump_only=True)
    dia_semana = fields.Str(validate=validate.OneOf([s.value for s in DiasSemanaEnum]))
    hora_inicial = fields.Time(format='%H:%M', required=True)
    hora_final = fields.Time(format='%H:%M', required=True)


# Ecoponto + localizacao + dia funcionamento + residuo - empresa_id
class PlainEcopontoSchema(Schema):
    id = fields.Int(dump_only=True)
    situacao = fields.Str(validate=validate.OneOf([s.value for s in SituacaoEnum]), dump_only=True)
    nome = fields.Str(required=True)
    ativo = fields.Boolean(missing=True)
    aberto_publico = fields.Boolean(missing=True)
    data_inicio = fields.Date(format='2024-01-01T00:00:00.019077+00:00', required=False)
    data_final = fields.Date(format='2050-12-31T23:59:59.019077+00:00', required=False)

class PlainEcopontoUpdateSchema(Schema):
    situacao = fields.Str(validate=validate.OneOf([s.value for s in SituacaoEnum]), required=False, dump_only=True)
    nome = fields.Str(required=False)
    ativo = fields.Boolean(missing=True)
    aberto_publico = fields.Boolean(missing=True)
    data_inicio = fields.Date(format='2024-01-01T00:00:00.019077+00:00', required=False)
    data_final = fields.Date(format='2050-12-31T23:59:59.019077+00:00', required=False)


# Ecoponto + localizacao + dia funcionamento + residuo
class EcopontoSchema(PlainEcopontoSchema):
    localizacao = fields.List(fields.Nested(PlainLocalizacaoSchema), required=True)
    dia_funcionamento = fields.List(fields.Nested(PainEcopontoDiaFuncionamento), required=False)
    residuo = fields.List(fields.Nested(ItemResiduoSchema), required=False)


# Ecoponto update + localizacao + dia funcionamento + residuo
class EcopontoGetSchema(PlainEcopontoSchema):
    localizacao = fields.List(fields.Nested(PlainLocalizacaoSchema), required=True)
    dia_funcionamento = fields.List(fields.Nested(PainEcopontoDiaFuncionamento), required=False)
    residuo = fields.List(fields.Nested(PlainResiduoSchema), required=False)
    funcionamento = fields.Str(required=False)

# Empresa + ecoponto
class EmpresaUpdateSchema(PlainEmpresaUpdateSchema):
    ecopontos = fields.List(fields.Nested(EcopontoSchema()))

# Empresa + ecoponto
class EmpresaSchema(PlainEmpresaSchema):
    ecopontos = fields.List(fields.Nested(EcopontoSchema()))

# Empresa + ecoponto
class EmpresaGetSchema(PlainEmpresaSchema):
    ecopontos = fields.List(fields.Nested(EcopontoGetSchema()), required=False )


# retorno: classe com a representação padronizada de saída
class RetornoSchema(Schema):
    code = fields.Str(default='200', dump_only=True)
    status = fields.Str(default='OK', dump_only=True)
    message = fields.Str( dump_only=True)


# empresa: classe com a representação padronizada de saída
class RetornoEmpresaSchema(RetornoSchema):
    value = fields.Nested(EmpresaSchema())


# empresa: classe com a representação padronizada de saída
class RetornoEmpresaGetSchema(RetornoSchema):
    value = fields.Nested(EmpresaGetSchema())


# empresa: classe com a representação padronizada de saída
class RetornoPlainEmpresaSchema(RetornoSchema):
    value = fields.Nested(PlainEmpresaSchema())


# empresa lista: classe com a representação padronizada de saída
class RetornoListaEmpresaSchema(RetornoSchema):
    Values = fields.List(fields.Nested(EmpresaGetSchema()), dump_only=True)


# argumentos de pesquisa
class EcopontoSearchSchema(PaginacaoSearchSchema):
    residuo_id = fields.Int(required=False)
    localizacao = fields.Str(required=False)
    

# Ecoponto + localizacao
class EcopontoLocalizacaoSchema(PlainEcopontoSchema):
    empresa_id = fields.Int(required=True)
    localizacao = fields.List(fields.Nested(PlainLocalizacaoSchema()))
  
class EcopontoLocalizacaoUpdateSchema(PlainEcopontoUpdateSchema):
    empresa_id = fields.Int(required=False)
    localizacao = fields.List(fields.Nested(PlainLocalizacaoUpdateSchema()))
  
  
# Ecoponto + dia funcionamento
class EcopontoFuncionamentoSchema(Schema):
    ecoponto_id = fields.Int(required=True)
    dia_funcionamento = fields.List(fields.Nested(PainEcopontoDiaFuncionamento), required=True)
    
class RetornoEcopontoFuncionamentoSchema(RetornoSchema):
    value = fields.Nested(EcopontoFuncionamentoSchema())
  

# Ecoponto + resíduo
class EcopontoResiduoSchema(Schema):
    ecoponto_id = fields.Int(required=True)
    residuo = fields.List(fields.Nested(ItemResiduoSchema), required=True)

class RetornoEcopontoResiduoSchema(RetornoSchema):
    Values = fields.Nested(EcopontoResiduoSchema())
  

# único ecoponto
class RetornoEcopontoSchema(RetornoSchema):
    value = fields.Nested(EcopontoGetSchema())


# ecoponto lista: classe com a representação padronizada de saída: ecoponto completo
class RetornoListaEcopontoSchema(RetornoSchema):
    Values = fields.List(fields.Nested(EcopontoGetSchema()), dump_only=True)
    pagination = fields.List(fields.Nested(PaginacaoSchema()), dump_only=True)


# ecoponto lista: classe com a representação padronizada de saída: ecoponto + localiação
class RetornoListaEcopontoLocalizacaoSchema(RetornoSchema):
    Values = fields.List(fields.Nested(EcopontoLocalizacaoSchema()), dump_only=True)
    pagination = fields.List(fields.Nested(PaginacaoSchema()), dump_only=True)



# Schema dos dados da situacao ecoponto
class EcopontoSituacaoSchema(Schema):
    situacao = fields.Str(required=False)
    situacao_enum = fields.Str(required=False)

class RetornoEcopontoSituacaoSchema(RetornoSchema):
    value = fields.Nested(EcopontoSituacaoSchema())


# listas de ecoponto por situação
class EcopontoLista(EcopontoSituacaoSchema):
    ecopontos = fields.List(fields.Nested(EcopontoLocalizacaoSchema))
    total = fields.Int()


class EcopontoPorSituacaoSchema(Schema):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adiciona um campo para cada enumeração em SituacaoEnum
        for situacao in SituacaoEnum:
            self.fields[situacao.name] = fields.Nested(EcopontoLista)
   
class EcopontoListaSituacaoSchema(RetornoSchema):
    values = fields.Nested(EcopontoPorSituacaoSchema)
  
    
