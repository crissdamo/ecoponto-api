import logging.handlers
from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from collections import defaultdict
import itertools

from extensions.database import db
from models.dia_funcionamento import DiaFuncionamentoModel
from models.ecoponto import EcopontoModel
from models.ecoponto_residuo import EcopontoResiduoModel
from models.empresa import EmpresaModel
from models.enums.situacao_ecoponto import SituacaoEnum
from models.localizacao import LocalizacaoModel
from models.residuo import ResiduoModel
from schemas.empresa_ecoponto import (
    EcopontoFuncionamentoSchema,
    EcopontoGetSchema,
    EcopontoLocalizacaoSchema,
    EcopontoLocalizacaoUpdateSchema, 
    EcopontoResiduoSchema,
    EcopontoSearchSchema, 
    RetornoEcopontoFuncionamentoSchema,
    RetornoEcopontoLocalizacaoSchema,
    RetornoEcopontoResiduoSchema,  
    RetornoListaEcopontoSchema)

blp = Blueprint("Ecopontos", "ecopontos", description="Operations on ecopontos")

def retira_valor_enum(valor):
    valor = str(valor).split('.')
    return valor[-1]

def transforma_dia_funcionamento(dias_funcionamento):

    for horario in dias_funcionamento:
        dia = retira_valor_enum(horario['dia_semana'])
        horario['dia_semana'] = dia
    return dias_funcionamento

    
def agrupar_horarios(dia_funcionamento):

    # Passo 1: Organizar horários por dia da semana
    horarios_por_dia = defaultdict(list)
    for horario in dia_funcionamento:
        dia = horario['dia_semana']
        intervalo = f"{horario['hora_inicial']} às {horario['hora_final']}"
        horarios_por_dia[dia].append(intervalo)

    # Passo 2: Identificar horários iguais em dias consecutivos
    dias_semana = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]
    grupos = []
    for key, group in itertools.groupby(enumerate(dias_semana), lambda x: horarios_por_dia.get(x[1])):
        dias_grupo = list(group)
        if key:  # Apenas adiciona se key não for None
            grupos.append((key, [dias[1] for dias in dias_grupo]))

    # Passo 3: Criar a string resumida
    partes = []

    for horarios, dias in grupos:
        dias_str = dias[0] if len(dias) == 1 else f"{dias[0]} a {dias[-1]}"
        horarios_str = " - ".join(horarios_por_dia[dias[0]])
        partes.append(f"{dias_str} das {horarios_str}")


    funcionamento_string = ""
    len_partes = len(partes) - 1
    for index, parte in enumerate(partes):
        
        # ultimo ou só tem um
        if index == len_partes or len_partes == 0:
            funcionamento_string += f"{parte} "
        
        # penúltimo
        elif (len_partes - index) == 1:
            funcionamento_string += f"{parte} e "

        else:
            funcionamento_string += f"{parte}, "
        
    return funcionamento_string


@blp.route("/ecoponto/<int:ecoponto_id>")
class Ecoponto(MethodView):

    @blp.response(200, RetornoEcopontoLocalizacaoSchema)
    def get(self, ecoponto_id):
        ecoponto = EcopontoModel().query.get_or_404(ecoponto_id)
        ecoponto_schema = EcopontoGetSchema()
        result = ecoponto_schema.dump(ecoponto)
        dias_funcionamento = result.get('dia_funcionamento')

        # estrai valor do enum
        if dias_funcionamento:
            dia_funcionamento = transforma_dia_funcionamento(dias_funcionamento)
            result["dia_funcionamento"] = dia_funcionamento

            # agrupa horário de funcionamento em uma única string
            result["funcionamento"] = agrupar_horarios(dias_funcionamento)

        # estrai valor do enum
        situacao = result.get("situacao")

        if situacao:
            result["situacao"] = retira_valor_enum(situacao)

        context = {
            "code": 200,
            "status": "OK",
            "message": "",
            "values": result
        }
        
        return jsonify(context)

    def delete(self, ecoponto_id):
        try:
            ecoponto = EcopontoModel().query.get_or_404(ecoponto_id)
            localizacoes = ecoponto.localizacao
            funcionamentos = ecoponto.dia_funcionamento


            for localizacao in localizacoes:
                db.session.delete(localizacao)

            for funcionamento in funcionamentos:
                db.session.delete(funcionamento)

            db.session.delete(ecoponto)

            db.session.commit()

            message = f"Ecoponto excluída com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error delete ecoponto: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao deletar ecoponto."
            )
        except SQLAlchemyError as error:
            message = f"Error delete ecoponto: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        context = {
            "code": 200,
            "status": "OK",
            "message": message,
            "errors": {}
        }

        return jsonify(context)


    @blp.arguments(EcopontoLocalizacaoUpdateSchema)
    @blp.response(200, RetornoEcopontoLocalizacaoSchema)
    def put(self, ecoponto_data, ecoponto_id):
        ecoponto = EcopontoModel().query.get_or_404(ecoponto_id)

        ecoponto.empresa_id = ecoponto_data['empresa_id']
        ecoponto.nome = ecoponto_data['nome']
        ecoponto.ativo = ecoponto_data.get('ativo')
        ecoponto.aberto_publico = ecoponto_data.get('aberto_publico')
        ecoponto.data_inicio = ecoponto_data.get('data_inicio')
        ecoponto.data_final = ecoponto_data.get('data_final')
        localizacao = ecoponto_data.get('localizacao')

        localizacao_obj = None
        if localizacao:
            localizacao = localizacao[0]
            latitude=localizacao['latitude']
            longitude=localizacao['longitude']
            url_localizacao = f"https://maps.google.com/?q={latitude},{longitude}"

            localizacao_obj = LocalizacaoModel.query.filter(LocalizacaoModel.ecoponto == ecoponto).first()
            localizacao_obj.rua=localizacao['rua'],
            localizacao_obj.numero=localizacao['numero'],
            localizacao_obj.bairro=localizacao['bairro'],
            localizacao_obj.cep=localizacao['cep'],
            localizacao_obj.cidade=localizacao['cidade'],
            localizacao_obj.estado=localizacao['estado'],
            localizacao_obj.complemento=localizacao.get('complemento'),
            localizacao_obj.latitude=latitude,
            localizacao_obj.longitude=longitude,
            localizacao_obj.url_localizacao=url_localizacao,
                     
        # Salva em BD
        try:
            db.session.add(ecoponto)
            if localizacao_obj:
                db.session.add(localizacao_obj)

            db.session.commit()


            message = f"Ecoponto editado com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error create ecoponto: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao criar ecoponto.",
            )
        except SQLAlchemyError as error:
            message = f"Error create ecoponto: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        ecoponto_schema = EcopontoLocalizacaoSchema()
        result = ecoponto_schema.dump(ecoponto)

        dias_funcionamento = result.get('dia_funcionamento')

        # estrai valor do enum
        if dias_funcionamento:
            dia_funcionamento = transforma_dia_funcionamento(dias_funcionamento)
            result["dia_funcionamento"] = dia_funcionamento

            # agrupa horário de funcionamento em uma única string
            result["funcionamento"] = agrupar_horarios(dias_funcionamento)

        # estrai valor do enum
        situacao = result.get("situacao")

        if situacao:
            result["situacao"] = retira_valor_enum(situacao)

        context = {
            "code": 200,
            "status": "OK",
            "message": "",
            "value": result
        }

        return jsonify(context)


@blp.route("/ecoponto")
class Ecopontos(MethodView):
    
    @blp.arguments(EcopontoSearchSchema, location="query")
    @blp.response(200, RetornoListaEcopontoSchema(many=True))
    def get(self, query_args):

        result_lista = []
        residuo_id = query_args.get("residuo_id")
        localizacao = query_args.get("localizacao")

        query = EcopontoModel().query.all()
        set_ids_lista = {ecoponto for ecoponto in query}
        intersecao_ids = set_ids_lista
        
        if localizacao:

            # Realiza a consulta para encontrar os ecopontos com base na localizacao
            query1 = db.session.query(EcopontoModel).join(LocalizacaoModel).filter(
                or_(
                    LocalizacaoModel.rua.ilike(f'%{localizacao}%'),
                    LocalizacaoModel.numero.ilike(f'%{localizacao}%'),
                    LocalizacaoModel.bairro.ilike(f'%{localizacao}%'),
                    LocalizacaoModel.cep.ilike(f'%{localizacao}%'),
                    LocalizacaoModel.cidade.ilike(f'%{localizacao}%'),
                    LocalizacaoModel.estado.ilike(f'%{localizacao}%'),
                    LocalizacaoModel.complemento.ilike(f'%{localizacao}%'),
                )
            ).all()

            set_ids_lista1 = {ecoponto for ecoponto in query1}
            intersecao_ids = set_ids_lista.intersection(set_ids_lista1)
            set_ids_lista = set_ids_lista1

        if residuo_id:

            # Pega todos ecopontos do resíduo pesquisado
            residuo = ResiduoModel().query.get_or_404(residuo_id)
            query2 = residuo.ecoponto

            # Pega todos ecopontos do resíduo pesquisado, coloca em um grupo para não ter ecoponto duplo
            set_ids_lista1 = {ecoponto for ecoponto in query2}

            # Pega apenas os ecopontos que combinam com as duas pesquisas
            intersecao_ids = set_ids_lista.intersection(set_ids_lista1)

        for ecoponto in intersecao_ids:
            ecoponto_schema = EcopontoGetSchema()
            result = ecoponto_schema.dump(ecoponto)
            dias_funcionamento = result.get('dia_funcionamento')

            # estrai valor do enum
            if dias_funcionamento:
                dia_funcionamento = transforma_dia_funcionamento(dias_funcionamento)
                result["dia_funcionamento"] = dia_funcionamento

                # agrupa horário de funcionamento em uma única string
                result["funcionamento"] = agrupar_horarios(dias_funcionamento)

            # estrai valor do enum
            situacao = result.get("situacao")

            if situacao:
                result["situacao"] = retira_valor_enum(situacao)
            
            result_lista.append(result)

        context = {
            "code": 200,
            "status": "OK",
            "message": "",
            "values": result_lista
        }
        
        return jsonify(context)


    @blp.arguments(EcopontoLocalizacaoSchema)
    @blp.response(201, RetornoEcopontoLocalizacaoSchema)
    def post(self, ecoponto_data):


        # Dados recebidos:

        empresa_id = ecoponto_data['empresa_id']
        nome = ecoponto_data['nome']
        ativo = ecoponto_data.get('ativo')
        aberto_publico = ecoponto_data.get('aberto_publico')
        data_inicio = ecoponto_data.get('data_inicio')
        data_final = ecoponto_data.get('data_final')
        localizacao = ecoponto_data.get('localizacao')
        dias_funcionamento = ecoponto_data.get('dia_funcionamento')

        residuos = ecoponto_data.get('residuo')
        
        dias_funcionamento_list = []

        # Cria objetos:
        emprsa = EmpresaModel().query.get_or_404(empresa_id)

        ecoponto = EcopontoModel(
            nome=nome,
            ativo=ativo,
            aberto_publico=aberto_publico,
            data_inicio=data_inicio,
            data_final=data_final,
            situacao=SituacaoEnum.em_analise,
            empresa=emprsa
        )

        if dias_funcionamento:
            for funcionamento in dias_funcionamento:
                
                dia_semana = funcionamento.get('dia_semana')
                hora_inicial = funcionamento.get('hora_inicial')
                hora_final = funcionamento.get('hora_final')

                dia_funcionamento_obj = DiaFuncionamentoModel(
                    dia_semana=dia_semana,
                    hora_inicial=hora_inicial,
                    hora_final=hora_final,
                    ecoponto=ecoponto
                )
                dias_funcionamento_list.append(dia_funcionamento_obj)

        localizacao_obj = None
        if localizacao:
            localizacao = localizacao[0]
            latitude=localizacao['latitude']
            longitude=localizacao['longitude']
            url_localizacao = f"https://maps.google.com/?q={latitude},{longitude}"

            localizacao_obj = LocalizacaoModel(
                rua=localizacao['rua'],
                numero=localizacao['numero'],
                bairro=localizacao['bairro'],
                cep=localizacao['cep'],
                cidade=localizacao['cidade'],
                estado=localizacao['estado'],
                complemento=localizacao.get('complemento'),
                latitude=latitude,
                longitude=longitude,
                url_localizacao=url_localizacao,
                ecoponto=ecoponto
            )
             
        # # Salva em BD
        try:
            db.session.add(ecoponto)
            if localizacao_obj:
                db.session.add(localizacao_obj)
           
            for funcionamento in dias_funcionamento_list:
                 db.session.add(funcionamento)

            if residuos:
                for residuo in residuos:
                    id_residuo = residuo.get('id')
                    residuo_object = ResiduoModel().query.get_or_404(id_residuo)
                    
                    categoria_residuo = EcopontoResiduoModel(
                        residuo_id=residuo_object.id,
                        ecoponto_id=ecoponto.id
                    )
                    db.session.add(categoria_residuo)

            db.session.commit()


            message = f"Ecoponto criado com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error create ecoponto: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao criar ecoponto.",
            )
        except SQLAlchemyError as error:
            message = f"Error create ecoponto: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        ecoponto_schema = EcopontoLocalizacaoSchema()
        result = ecoponto_schema.dump(ecoponto)
        context = {
            "code": 201,
            "status": "Created",
            "message": "",
            "value": result
        }

        return jsonify(context)


    def delete(self):

        ecopontos = EcopontoModel.query.all()
        funcionamentos = DiaFuncionamentoModel.query.all()
        localizacoes = LocalizacaoModel.query.all()

        # Deletar
        try:

            for localizacao in localizacoes:
                db.session.delete(localizacao)

            for funcionamento in funcionamentos:
                db.session.delete(funcionamento)

            for ecoponto in ecopontos:
                db.session.delete(ecoponto)

            db.session.commit()

            message = f"Ecopontos deletadas com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error delete ecopontos: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao deletar ecopontos.",
            )
            
        except SQLAlchemyError as error:
            message = f"Error delete ecopontos: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        return {"message": "Todos registros deletados."}
      

@blp.route("/ecoponto/funcionamento")
class EcopontoFuncionamento(MethodView):

    @blp.arguments(EcopontoFuncionamentoSchema)
    @blp.response(200, RetornoEcopontoFuncionamentoSchema)
    def put(self, ecoponto_data):

        # Dados recebidos:

        ecoponto_id = ecoponto_data['ecoponto_id']
        dias_funcionamento = ecoponto_data.get('dia_funcionamento')
        dias_funcionamento_list = []

        # Cria objetos:
        ecoponto = EcopontoModel().query.get_or_404(ecoponto_id)

        dias_funcionamento_anterior = ecoponto.dia_funcionamento

        if dias_funcionamento:

            for funcionamento in dias_funcionamento:
                dia_semana = funcionamento.get('dia_semana')
                hora_inicial = funcionamento.get('hora_inicial')
                hora_final = funcionamento.get('hora_final')

                dia_funcionamento_obj = DiaFuncionamentoModel(
                    dia_semana=dia_semana,
                    hora_inicial=hora_inicial,
                    hora_final=hora_final,
                    ecoponto=ecoponto
                )

                dias_funcionamento_list.append(dia_funcionamento_obj)

        # Salva em BD
        try:
           
            for funcionamento in dias_funcionamento_anterior:
                 db.session.delete(funcionamento)
           
            for funcionamento in dias_funcionamento_list:
                 db.session.add(funcionamento)

            db.session.commit()

            message = f"Dias de funcionamento do Ecoponto criados com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error create ecoponto diasfuncionamento: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao criar dias de funcionamento do ecoponto.",
            )
        except SQLAlchemyError as error:
            message = f"Error create ecoponto diasfuncionamento: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        ecoponto_schema = EcopontoFuncionamentoSchema()
        result = ecoponto_schema.dump(ecoponto)

        dias_funcionamento = result.get('dia_funcionamento')

        # estrai valor do enum
        dia_funcionamento = transforma_dia_funcionamento(dias_funcionamento)
        result["dia_funcionamento"] = dia_funcionamento

        # agrupa horário de funcionamento em uma única string
        result["funcionamento"] = agrupar_horarios(dias_funcionamento)

        # estrai valor do enum
        situacao = result.get("situacao")
        result["situacao"] = retira_valor_enum(situacao)
        context = {
            "code": 200,
            "status": "OK",
            "message": "",
            "value": result
        }

        return jsonify(context)


    @blp.arguments(EcopontoFuncionamentoSchema)
    @blp.response(201, RetornoEcopontoFuncionamentoSchema)
    def post(self, ecoponto_data):

        # Dados recebidos:

        ecoponto_id = ecoponto_data['ecoponto_id']

        dias_funcionamento = ecoponto_data.get('dia_funcionamento')
        
        dias_funcionamento_list = []

        # Cria objetos:
        ecoponto = EcopontoModel().query.get_or_404(ecoponto_id)

        if dias_funcionamento:

            for funcionamento in dias_funcionamento:
                
                dia_semana = funcionamento.get('dia_semana')
                hora_inicial = funcionamento.get('hora_inicial')
                hora_final = funcionamento.get('hora_final')

                dia_funcionamento_obj = DiaFuncionamentoModel(
                    dia_semana=dia_semana,
                    hora_inicial=hora_inicial,
                    hora_final=hora_final,
                    ecoponto=ecoponto
                )

                dias_funcionamento_list.append(dia_funcionamento_obj)

 
        # # Salva em BD
        try:
           
            for funcionamento in dias_funcionamento_list:
                 db.session.add(funcionamento)

            db.session.commit()

            message = f"Dias de funcionamento do Ecoponto criados com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error create ecoponto diasfuncionamento: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao criar dias de funcionamento do ecoponto.",
            )
        except SQLAlchemyError as error:
            message = f"Error create ecoponto diasfuncionamento: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        ecoponto_schema = EcopontoFuncionamentoSchema()
        result = ecoponto_schema.dump(ecoponto)

        dias_funcionamento = result.get('dia_funcionamento')

        # estrai valor do enum
        dia_funcionamento = transforma_dia_funcionamento(dias_funcionamento)
        result["dia_funcionamento"] = dia_funcionamento

        # agrupa horário de funcionamento em uma única string
        result["funcionamento"] = agrupar_horarios(dias_funcionamento)

        # estrai valor do enum
        situacao = result.get("situacao")
        result["situacao"] = retira_valor_enum(situacao)

        context = {
            "code": 201,
            "status": "Created",
            "message": "",
            "value": result
        }

        return jsonify(context)


@blp.route("/ecoponto/residuo")
class EcopontoPostResiduo(MethodView):

    @blp.arguments(EcopontoResiduoSchema)
    @blp.response(200, RetornoEcopontoResiduoSchema)
    def put(self, ecoponto_data):

        # Dados recebidos:
        ecoponto_id = ecoponto_data['ecoponto_id']
        # descricao_outros_projetos = ecoponto_data.get('descricao_outros_projetos')
        residuos = ecoponto_data.get('residuo')
        residuos_list = []

        # Cria objetos:
        ecoponto = EcopontoModel().query.get_or_404(ecoponto_id)
        residuos_relacionados = EcopontoResiduoModel.query.filter(EcopontoResiduoModel.ecoponto_id == ecoponto_id)


        # # Salva em BD

        try:
            if residuos:
                for residuo in residuos:
                    
                    id_residuo = residuo.get('id')
                    residuos_list.append(id_residuo)

                    residuo_object = ResiduoModel().query.get_or_404(id_residuo)

                    residuo_ecoponto = EcopontoResiduoModel.query.filter(
                        EcopontoResiduoModel.residuo_id == id_residuo,
                        EcopontoResiduoModel.ecoponto_id == ecoponto_id,
                    ).first()

                    if not residuo_ecoponto:
                        
                        ecoponto_residuo = EcopontoResiduoModel(
                            residuo_id=residuo_object.id,
                            ecoponto_id=ecoponto_id
                        )
                        db.session.add(ecoponto_residuo)                

            if residuos_relacionados:

                for item in residuos_relacionados:
                    if item.residuo_id not in residuos_list:
                        db.session.delete(item)

            db.session.commit()

            message = f"Relação deresíduos do ecoponto criados com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error create ecoponto residuos: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao criar relação de residuos do ecoponto.",
            )
        except SQLAlchemyError as error:
            message = f"Error create ecoponto residuos: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        ecoponto_schema = EcopontoResiduoSchema()
        result = ecoponto_schema.dump(ecoponto)

        dias_funcionamento = result.get('dia_funcionamento')

        # estrai valor do enum
        if dias_funcionamento:
            dia_funcionamento = transforma_dia_funcionamento(dias_funcionamento)
            result["dia_funcionamento"] = dia_funcionamento

            # agrupa horário de funcionamento em uma única string
            result["funcionamento"] = agrupar_horarios(dias_funcionamento)

        # estrai valor do enum
        situacao = result.get("situacao")

        if situacao:
            result["situacao"] = retira_valor_enum(situacao)

        context = {
            "code": 200,
            "status": "OK",
            "message": "",
            "value": result
        }

        return jsonify(context)


    @blp.arguments(EcopontoResiduoSchema)
    @blp.response(201, RetornoEcopontoResiduoSchema)
    def post(self, ecoponto_data):

        # Dados recebidos:

        ecoponto_id = ecoponto_data['ecoponto_id']
        # descricao_outros_projetos = ecoponto_data.get('descricao_outros_projetos')
        residuos = ecoponto_data.get('residuo')
        
        # Cria objetos:
        ecoponto = EcopontoModel().query.get_or_404(ecoponto_id)

        empresa = ecoponto.empresa


        # # Salva em BD
        try:
            # if descricao_outros_projetos:
            #     empresa = ecoponto.empresa
            #     empresa.descricao_outros_projetos = descricao_outros_projetos
            #     db.session.add(empresa)


            if residuos:
                for residuo in residuos:
                    id_residuo = residuo.get('id')
                    residuo_object = ResiduoModel().query.get_or_404(id_residuo)
                    
                    categoria_residuo = EcopontoResiduoModel(
                        residuo_id=residuo_object.id,
                        ecoponto_id=ecoponto.id
                    )
                    db.session.add(categoria_residuo)

                db.session.commit()


            message = f"Relação deresíduos do ecoponto criados com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error create ecoponto residuos: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao criar relação de residuos do ecoponto.",
            )
        except SQLAlchemyError as error:
            message = f"Error create ecoponto residuos: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        ecoponto_schema = EcopontoResiduoSchema()
        result = ecoponto_schema.dump(ecoponto)

        dias_funcionamento = result.get('dia_funcionamento')

        # estrai valor do enum
        if dias_funcionamento:
            dia_funcionamento = transforma_dia_funcionamento(dias_funcionamento)
            result["dia_funcionamento"] = dia_funcionamento

            # agrupa horário de funcionamento em uma única string
            result["funcionamento"] = agrupar_horarios(dias_funcionamento)

        # estrai valor do enum
        situacao = result.get("situacao")

        if situacao:
            result["situacao"] = retira_valor_enum(situacao)

        context = {
            "code": 201,
            "status": "Created",
            "message": "",
            "value": result
        }

        return jsonify(context)


@blp.route("/ecoponto/ativar/<int:ecoponto_id>")
class Ecoponto(MethodView):

    @blp.response(200, RetornoEcopontoLocalizacaoSchema)
    def put(self, ecoponto_id):
        ecoponto = EcopontoModel().query.get_or_404(ecoponto_id)

        # Salva em BD
        try:
            db.session.add(ecoponto)
            if ecoponto:
                ecoponto.ativo = True
                db.session.add(ecoponto)
            db.session.commit()

            message = f"Ecoponto ativado com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error active ecoponto: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao active ecoponto.",
            )
        except SQLAlchemyError as error:
            message = f"Error active ecoponto: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        ecoponto_schema = EcopontoGetSchema()
        result = ecoponto_schema.dump(ecoponto)
        dias_funcionamento = result.get('dia_funcionamento')

        # estrai valor do enum
        if dias_funcionamento:
            dia_funcionamento = transforma_dia_funcionamento(dias_funcionamento)
            result["dia_funcionamento"] = dia_funcionamento

            # agrupa horário de funcionamento em uma única string
            result["funcionamento"] = agrupar_horarios(dias_funcionamento)

        # estrai valor do enum
        situacao = result.get("situacao")

        if situacao:
            result["situacao"] = retira_valor_enum(situacao)

        context = {
            "code": 200,
            "status": "OK",
            "message": "",
            "values": result
        }
        
        return jsonify(context)


@blp.route("/ecoponto/desativar/<int:ecoponto_id>")
class Ecoponto(MethodView):

    @blp.response(200, RetornoEcopontoLocalizacaoSchema)
    def put(self, ecoponto_id):
        ecoponto = EcopontoModel().query.get_or_404(ecoponto_id)

        # Salva em BD
        try:
            db.session.add(ecoponto)
            if ecoponto:
                ecoponto.ativo = False
                db.session.add(ecoponto)
            db.session.commit()

            message = f"Ecoponto ativado com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error active ecoponto: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao active ecoponto.",
            )
        except SQLAlchemyError as error:
            message = f"Error active ecoponto: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        ecoponto_schema = EcopontoGetSchema()
        result = ecoponto_schema.dump(ecoponto)
        dias_funcionamento = result.get('dia_funcionamento')

        # estrai valor do enum
        if dias_funcionamento:
            dia_funcionamento = transforma_dia_funcionamento(dias_funcionamento)
            result["dia_funcionamento"] = dia_funcionamento

            # agrupa horário de funcionamento em uma única string
            result["funcionamento"] = agrupar_horarios(dias_funcionamento)

        # estrai valor do enum
        situacao = result.get("situacao")

        if situacao:
            result["situacao"] = retira_valor_enum(situacao)

        context = {
            "code": 200,
            "status": "OK",
            "message": "",
            "values": result
        }
        
        return jsonify(context)

