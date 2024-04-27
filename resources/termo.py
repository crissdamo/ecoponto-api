from flask.views import MethodView
from flask_smorest import Blueprint, abort
from models.termo import TermoModel
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from extensions.database import db

import logging.handlers

from schemas.termo import PlainTermoSchema

blp = Blueprint("Termos", "termos", description="Operações sobre termos")



@blp.route("/termo")
class Termos(MethodView):

    @blp.arguments(PlainTermoSchema)
    @blp.response(201, PlainTermoSchema)
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

        return termo
    
    
    def delete(self):
    
        termos = TermoModel.query.all()

        # Deletar
        try:

            for termo in termos:
                db.session.delete(termo)
            db.session.commit()

            message = f"Termos deletados com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error delete termos: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao deletar termos.",
            )
            
        except SQLAlchemyError as error:
            message = f"Error delete termos: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        return {"message": "Todos registros deletados."}
    
# @blp.route("/termo/eceite")
# class AceiteTermos(MethodView):

#     @blp.arguments(AceiteTermoSchema)
#     @blp.response(201, AceiteTermoSchema)
#     def post(self, aceite_termo_data):


#         # Dados recebidos:
        
#         id_termo = aceite_termo_data['id_termo']
#         id_empresa = aceite_termo_data['id_empresa']
#         aceite = aceite_termo_data.get('aceite')


#         # Cria objeto:

#         aceite_termo = TermoAceiteModel(
#             termo_id=id_termo,
#             empresa_id=id_empresa,
#             aceite=aceite
#         )


#         # Salva em BD
#         try:
#             db.session.add(aceite_termo)
#             db.session.commit()


#             message = f"aceite de termo criado com sucesso"
#             logging.debug(message)
    
#         except IntegrityError as error:
#             message = f"Error create aceite termo: {error}"
#             logging.warning(message)
#             abort(
#                 400,
#                 message="Erro ao aceitar termo.",
#             )
#         except SQLAlchemyError as error:
#             message = f"Error create aceite termo: {error}"
#             logging.warning(message)
#             abort(500, message="Server Error.")

#         return aceite_termo
    
