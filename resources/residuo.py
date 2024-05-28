import logging.handlers
from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from models.categoria import CategoriaModel
from models.categoria_residuo import CategoriaResiduoModel
from models.residuo import ResiduoModel
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from extensions.database import db
from models.residuo import ResiduoModel
from schemas.categoria_residuo import ResiduoPostSchema, ResiduoSchema, ResiduoSearchSchema, RetornoResiduoSchema

blp = Blueprint("Resíduos", "resíduos", description="Operações sobre resíduos")


@blp.route("/residuo/<int:residuo_id>")
class Residuos(MethodView):

    @blp.response(200, RetornoResiduoSchema)
    def get(self, residuo_id):
        
        residuo = ResiduoModel().query.get_or_404(residuo_id)
        residuo_schema = ResiduoSchema()
        result = residuo_schema.dump(residuo)

        context = {
            "code": 200,
            "status": "OK",
            "message": "",
            "values": result
        }
        
        return jsonify(context)


    # @blp.arguments(ResiduoPostSchema)
    # @blp.response(200, RetornoResiduoSchema)
    # def put(self, residuo_data, residuo_id):
        
    #     residuo = ResiduoModel().query.get_or_404(residuo_id)
    #     descricao = residuo_data['descricao']
    #     residuo.descricao = descricao
    #     residuo.icone = residuo_data.get('icone')
    #     residuo.url_midia = residuo_data.get('url_midia')
    #     residuo.recolhido_em_ecoponto = residuo_data.get('recolhido_em_ecoponto')
    #     categorias = residuo_data.get('categoria')

    #     # validações:
    #     if ResiduoModel.query.filter(ResiduoModel.descricao == descricao, ResiduoModel.id != residuo_id).first():
    #         abort(409, message="Resíduo com essa descrição já existe")

    #     # Salva em BD
    #     try:
    #         db.session.add(residuo)
           
    #         if categorias:
    #             for categoria in categorias:
    #                 categoria_id = categoria.get('id')
    #                 categoriao_object = CategoriaModel().query.get_or_404(categoria_id)

    #                 categoria_residuo = CategoriaResiduoModel(
    #                     residuo_id=residuo.id,
    #                     categoria_id=categoriao_object.id
    #                 )
    #                 db.session.add(categoria_residuo)

    #         db.session.commit()



    #         message = f"Ecoponto editado com sucesso"
    #         logging.debug(message)
    
    #     except IntegrityError as error:
    #         message = f"Error create ecoponto: {error}"
    #         logging.warning(message)
    #         abort(
    #             400,
    #             message="Erro ao criar ecoponto.",
    #         )
    #     except SQLAlchemyError as error:
    #         message = f"Error create ecoponto: {error}"
    #         logging.warning(message)
    #         abort(500, message="Server Error.")

    #     residuo_schema = ResiduoSchema()
    #     result = residuo_schema.dump(residuo)

    #     context = {
    #         "code": 200,
    #         "status": "OK",
    #         "message": "",
    #         "values": result
    #     }
        
    #     return jsonify(context)



    # def delete(self, residuo_id):


    #     try:
    #         residuo = ResiduoModel().query.get_or_404(residuo_id)

    #         categorias = residuo.categoria
    #         for cat in categorias:
    #             db.session.delete(cat)

    #         db.session.delete(residuo)
    #         db.session.commit()

    #         message = f"Resíduo excluído com sucesso"
    #         logging.debug(message)
    
    #     except IntegrityError as error:
    #         message = f"Error delete ecoponto: {error}"
    #         logging.warning(message)
    #         abort(
    #             400,
    #             message="Erro ao deletar resíduo."
    #         )
    #     except SQLAlchemyError as error:
    #         message = f"Error delete resíduo: {error}"
    #         logging.warning(message)
    #         abort(500, message="Server Error.")

    #     context = {
    #         "code": 200,
    #         "status": "OK",
    #         "message": message,
    #         "errors": {}
    #     }

    #     return jsonify(context)


        




@blp.route("/residuo")
class Residuos(MethodView):

    @blp.arguments(ResiduoSearchSchema, location="query")
    @blp.response(200, RetornoResiduoSchema)
    def get(self, query_args):
        
        result_lista = []
        categoria_id = query_args.get("categoria_id")
        recolhe_ecoponto = query_args.get("recolhe_ecoponto")
        descricao = query_args.get("descricao")

        try:
            residuos = db.session.query(ResiduoModel).filter(ResiduoModel.ativo == True)
       
            if recolhe_ecoponto:
                residuos = residuos.filter(ResiduoModel.recolhido_em_ecoponto == True)


            if descricao:
                residuos = residuos.filter(ResiduoModel.descricao.like(f'%{descricao}%'))

            set_ids_lista = {residuo for residuo in residuos}
            intersecao_ids = set_ids_lista

            if categoria_id:
                categoria = CategoriaModel().query.get_or_404(categoria_id)
                residuo_categoria = categoria.residuo

                set_ids_lista1 = {residuo for residuo in residuo_categoria}
                intersecao_ids = set_ids_lista.intersection(set_ids_lista1)
                set_ids_lista = set_ids_lista1

            for residuo in intersecao_ids:
                residuo_schema = ResiduoSchema()
                result = residuo_schema.dump(residuo)
                result_lista.append(result)
            
        except IntegrityError as error:
            logging.warning(message)
            abort(
                400,
                message="Erro pesquisar resíduos.",
            )

        except SQLAlchemyError as error:
            message = f"Error create ecoponto: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")
            
        context = {
            "code": 200,
            "status": "OK",
            "message": "",
            "values": result_lista
        }
        
        return jsonify(context)

    @blp.arguments(ResiduoPostSchema)
    @blp.response(201, RetornoResiduoSchema)
    def post(self, residuo_data):

        # Dados recebidos:
        
        descricao = residuo_data['descricao']
        icone = residuo_data.get('icone')
        url_midia = residuo_data.get('url_midia')
        recolhido_em_ecoponto = residuo_data.get('recolhido_em_ecoponto')
        categorias = residuo_data.get('categoria')

        # validações:
        if ResiduoModel.query.filter(ResiduoModel.descricao == descricao).first():
            abort(409, message="Resíduo com essa descrição já existe")

    
        # Cria objeto:

        residuo = ResiduoModel(
            descricao=descricao,
            icone=icone,
            url_midia=url_midia,
            recolhido_em_ecoponto=recolhido_em_ecoponto
        )

        # Salva em BD
        try:
            db.session.add(residuo)

            if categorias:
                for categoria in categorias:
                    categoria_id = categoria.get('id')
                    categoriao_object = CategoriaModel().query.get_or_404(categoria_id)

                    categoria_residuo = CategoriaResiduoModel(
                        residuo_id=residuo.id,
                        categoria_id=categoriao_object.id
                    )
                    db.session.add(categoria_residuo)

            db.session.commit()

            message = f"Resíduo criado com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error create residuo: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao criar resíduo.",
            )
        except SQLAlchemyError as error:
            message = f"Error create residuo: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")
    

        residuo_schema = ResiduoSchema()
        result = residuo_schema.dump(residuo)

        context = {
            "code": 201,
            "status": "Created",
            "message": "",
            "value": result
        }

        return jsonify(context)
    
   