import logging.handlers
from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from models.dia_funcionamento import DiaFuncionamentoModel
from models.ecoponto import EcopontoModel

from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from extensions.database import db
from models.ecoponto_residuo import EcopontoResiduoModel
from models.empresa import EmpresaModel
from models.enums.situacao_ecoponto import SituacaoEnum
from models.localizacao import LocalizacaoModel
from models.residuo import ResiduoModel
from schemas.empresa_ecoponto import (
    EcopontoFuncionamentoSchema,
    EcopontoGetSchema,
    EcopontoLocalizacaoSchema, 
    EcopontoResiduoSchema, 
    EcopontoSchema,  
    RetornoEcopontoFuncionamentoSchema,
    RetornoEcopontoLocalizacaoSchema,
    RetornoEcopontoResiduoSchema,  
    RetornoListaEcopontoSchema)

blp = Blueprint("Ecopontos", "ecopontos", description="Operations on ecopontos")


@blp.route("/ecoponto")
class Ecopontos(MethodView):

    @blp.response(200, RetornoListaEcopontoSchema(many=True))
    def get(self):
        result_lista = []
        ecopontos = EcopontoModel().query.all()
        for ecoponto in ecopontos:
            ecoponto_schema = EcopontoGetSchema()
            result = ecoponto_schema.dump(ecoponto)
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
                    id_residuo = residuo.get('id_residuo')
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


    # def delete(self):

    #     ecopontos = EcopontoModel.query.all()
    #     funcionamentos = DiaFuncionamentoModel.query.all()
    #     localizacoes = LocalizacaoModel.query.all()

    #     # Deletar
    #     try:

    #         for localizacao in localizacoes:
    #             db.session.delete(localizacao)

    #         for funcionamento in funcionamentos:
    #             db.session.delete(funcionamento)

    #         for ecoponto in ecopontos:
    #             db.session.delete(ecoponto)

    #         db.session.commit()

    #         message = f"Ecopontos deletadas com sucesso"
    #         logging.debug(message)
    
    #     except IntegrityError as error:
    #         message = f"Error delete ecopontos: {error}"
    #         logging.warning(message)
    #         abort(
    #             400,
    #             message="Erro ao deletar ecopontos.",
    #         )
            
    #     except SQLAlchemyError as error:
    #         message = f"Error delete ecopontos: {error}"
    #         logging.warning(message)
    #         abort(500, message="Server Error.")

    #     return {"message": "Todos registros deletados."}
      

@blp.route("/ecoponto/funcionamento")
class EcopontoFuncionamento(MethodView):

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
        context = {
            "code": 201,
            "status": "Created",
            "message": "",
            "value": result
        }

        return jsonify(context)


@blp.route("/ecoponto/residuo")
class EcopontoResiduo(MethodView):

    @blp.arguments(EcopontoResiduoSchema)
    @blp.response(201, RetornoEcopontoResiduoSchema)
    def post(self, ecoponto_data):

        # Dados recebidos:

        ecoponto_id = ecoponto_data['ecoponto_id']
        # descricao_outros_projetos = ecoponto_data.get('descricao_outros_projetos')
        residuos = ecoponto_data.get('residuo')
        
        # Cria objetos:
        ecoponto = EcopontoModel().query.get_or_404(ecoponto_id)
        print(ecoponto)

        empresa = ecoponto.empresa

        print(empresa)

        # # Salva em BD
        try:
            # if descricao_outros_projetos:
            #     empresa = ecoponto.empresa
            #     empresa.descricao_outros_projetos = descricao_outros_projetos
            #     db.session.add(empresa)


            if residuos:
                for residuo in residuos:
                    id_residuo = residuo.get('id_residuo')
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
        context = {
            "code": 201,
            "status": "Created",
            "message": "",
            "value": result
        }

        return jsonify(context)

