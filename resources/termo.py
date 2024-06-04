from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from models.aceite_termo import TermoAceiteModel
from models.termo import TermoModel
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from extensions.database import db

import logging.handlers

from schemas.termo import AceiteTermoSchema, PlainTermoSchema, RetornoTermoListaSchema, RetornoTermoSchema, SearchSchema

blp = Blueprint("Termos", "termos", description="Operações sobre termos")


@blp.route("/termo/<int:termo_id>")
class Termo(MethodView):


    @blp.response(200, RetornoTermoSchema)
    def get(self, termo_id):
        
        termo = TermoModel().query.get_or_404(termo_id)
        termo_schema = PlainTermoSchema()
        result = termo_schema.dump(termo)

        context = {
            "code": 200,
            "status": "OK",
            "message": "",
            "values": result
        }
        
        return jsonify(context)


    def delete(self, termo_id):

        try:
            termo = TermoModel().query.get_or_404(termo_id)
            db.session.delete(termo)
            db.session.commit()

            message = f"Termo excluído com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error delete termo: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao deletar termo."
            )
        except SQLAlchemyError as error:
            message = f"Error delete termo: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        context = {
            "code": 200,
            "status": "OK",
            "message": message,
            "errors": {}
        }

        return jsonify(context)

    
    @blp.arguments(PlainTermoSchema)
    @blp.response(200, RetornoTermoSchema)
    def put(self, termo_data, termo_id):
        
        termo = TermoModel().query.get_or_404(termo_id)
        titulo = termo_data.get('titulo')
        termo.titulo = titulo
        termo.descricao = termo_data['descricao']
        termo.ativo = termo_data.get('ativo')

        # validações:
        termo_titulo =  TermoModel.query.filter(TermoModel.titulo == titulo).first()
        if termo_titulo.id != termo.id:
            abort(409, message="Termo com esse título já existe")

        # Salva em BD
        try:
            db.session.add(termo)
            db.session.commit()
            message = f"Termo editado com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error create termo: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao criar termo.",
            )
        except SQLAlchemyError as error:
            message = f"Error create termo: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        termo_schema = PlainTermoSchema()
        result = termo_schema.dump(termo)

        context = {
            "code": 200,
            "status": "OK",
            "message": "",
            "values": result
        }
        
        return jsonify(context)


@blp.route("/termo")
class Termos(MethodView):


    @blp.arguments(SearchSchema, location="query")
    @blp.response(200, RetornoTermoListaSchema)
    def get(self, query_args):
        
        result_lista = []
        descricao = query_args.get("descricao")

        try:
            termos = db.session.query(TermoModel).filter(TermoModel.ativo == True)

            if descricao:
                termos = termos.filter(TermoModel.descricao.like(f'%{descricao}%'))

            for termo in termos:
                termo_schema = PlainTermoSchema()
                result = termo_schema.dump(termo)
                result_lista.append(result)
            
        except IntegrityError as error:
            logging.warning(message)
            abort(
                400,
                message="Erro pesquisar termo.",
            )

        except SQLAlchemyError as error:
            message = f"Error create termo: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")
            
        context = {
            "code": 200,
            "status": "OK",
            "message": "",
            "values": result_lista
        }
        
        return jsonify(context)

    @blp.arguments(PlainTermoSchema)
    @blp.response(201, RetornoTermoSchema)
    def post(self, termo_data):


        # Dados recebidos:
        
        titulo = termo_data['titulo']
        descricao = termo_data['descricao']


        # validações:
        if TermoModel.query.filter(TermoModel.titulo == titulo).first():
            abort(409, message="Título do termo já cadastrado")

    
        # Cria objeto:

        termo = TermoModel(
            titulo=titulo,
            descricao=descricao
        )


        # Salva em BD
        try:
            db.session.add(termo)
            db.session.commit()


            message = f"Termo criado com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error create termo: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao criar termo.",
            )
        except SQLAlchemyError as error:
            message = f"Error create termo: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        termo_schema = PlainTermoSchema()
        result = termo_schema.dump(termo)

        context = {
            "code": 201,
            "status": "Created",
            "message": "",
            "value": result
        }

        return jsonify(context)
    
    
@blp.route("/termo/eceite")
class AceiteTermos(MethodView):

    @blp.arguments(AceiteTermoSchema)
    @blp.response(201, AceiteTermoSchema)
    def post(self, aceite_termo_data):


        # Dados recebidos:
        
        termo_id = aceite_termo_data['termo_id']
        empresa_id = aceite_termo_data['empresa_id']
        aceite = aceite_termo_data.get('aceite')


        # Cria objeto:

        aceite_termo = TermoAceiteModel(
            termo_id=termo_id,
            empresa_id=empresa_id,
            aceite=aceite
        )

        # Salva em BD
        try:
            db.session.add(aceite_termo)
            db.session.commit()


            message = f"aceite de termo criado com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error create aceite termo: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao aceitar termo.",
            )
        except SQLAlchemyError as error:
            message = f"Error create aceite termo: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        return aceite_termo
    