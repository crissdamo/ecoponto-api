import logging.handlers
from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from models.categoria import CategoriaModel
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from extensions.database import db
from models.categoria_residuo import CategoriaResiduoModel
from models.residuo import ResiduoModel
from schemas.categoria_residuo import CategoriaSchema, PlainCategoriaSchema, RetornoCategoriaSchema, SearchSchema

blp = Blueprint("Categorias", "Categorias", description="Operações sobre categorias de resíduos")



@blp.route("/categoria/<int:categoria_id>")
class Categoria(MethodView):

    @blp.response(200, RetornoCategoriaSchema)
    def get(self, categoria_id):
        
        categoria = CategoriaModel().query.get_or_404(categoria_id)
        categoria_schema = CategoriaSchema()
        result = categoria_schema.dump(categoria)

        context = {
            "code": 200,
            "status": "OK",
            "message": "",
            "values": result
        }
        
        return jsonify(context)


    def delete(self, categoria_id):
        
        try:
            categoria = CategoriaModel().query.get_or_404(categoria_id)
            db.session.delete(categoria)
            db.session.commit()

            message = f"Categoria excluído com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error delete categoria: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao deletar categoria."
            )
        except SQLAlchemyError as error:
            message = f"Error delete categoria: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        context = {
            "code": 200,
            "status": "OK",
            "message": message,
            "errors": {}
        }

        return jsonify(context)

    
    @blp.arguments(PlainCategoriaSchema)
    @blp.response(200, CategoriaSchema)
    def put(self, categoria_data, categoria_id):

        categoria = CategoriaModel().query.get_or_404(categoria_id)
        descricao = categoria_data['descricao']
        categoria.descricao = descricao
        categoria.icone = categoria_data.get('icone')
        categoria.url_midia = categoria_data.get('url_midia')


        # validações:
        categoria_descricao =  CategoriaModel.query.filter(CategoriaModel.descricao == descricao).first()
        
        if categoria_descricao.id != categoria.id:
            abort(409, message="Categoria com essa descrição já existe")

        # Salva em BD
        try:
            db.session.add(categoria)
            db.session.commit()

            message = f"Categoria editada com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error update categoria: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao editar categoria.",
            )
        except SQLAlchemyError as error:
            message = f"Error update categoria: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        categoria_schema = CategoriaSchema()
        result = categoria_schema.dump(categoria)

        context = {
            "code": 200,
            "status": "OK",
            "message": message,
            "value": result
        }

        return jsonify(context)
    

@blp.route("/categoria")
class Categorias(MethodView):

    @blp.arguments(SearchSchema, location="query")
    @blp.response(200, RetornoCategoriaSchema(many=True))
    def get(self, query_args):
        """
        Retorna uma lista de categoria filtrados pelos critérios informados.

       **Descrição**: Filtra as categorias por palavra cheve, se informado.
        Serão retornadas apenas categorias ativas e que estão disponíveis para ecoponto.

        **Parâmetros**:
            query_args (dict): Argumentos de consulta e para paginação.
                - palavra_chave (str): descrição da categoria.

            **Retorna**:
                Um objeto JSON com a lista de categorias filtrados pelos critérios informados.
        """

        result_lista = []

        descricao = query_args.get("descricao")

        query = CategoriaModel.query.filter(CategoriaModel.ativo)

  
        if descricao:
            query = query.filter(CategoriaModel.descricao.ilike(f'%{descricao}%'))
        

        for categoria in query:
            categoria_schema = CategoriaSchema()
            result = categoria_schema.dump(categoria)
            
            result_lista.append(result)

        context = {
            "code": 200,
            "status": "OK",
            "message": "",
            "values": result_lista,
        }
        
        return jsonify(context)



    @blp.arguments(PlainCategoriaSchema)
    @blp.response(201, CategoriaSchema)
    def post(self, categoria_data):


        # Dados recebidos:
        
        descricao = categoria_data['descricao']
        icone = categoria_data.get('icone')
        url_midia = categoria_data.get('url_midia')
        residuos = categoria_data.get('residuos')


        # validações:
        if CategoriaModel.query.filter(CategoriaModel.descricao == descricao).first():
            abort(409, message="Categoria com essa descrição já existe")

    
        # Cria objeto:

        categoria = CategoriaModel(
            descricao=descricao,
            icone=icone,
            url_midia=url_midia
        )

       
        # Salva em BD
        try:
            db.session.add(categoria)

            if residuos:
                for residuo in residuos:
                    id_residuo = residuo.get('id')
                    residuo_object = ResiduoModel().query.get_or_404(id_residuo)
                    
                    categoria_residuo = CategoriaResiduoModel(
                        residuo_id=residuo_object.id,
                        categoria_id=categoria.id
                    )
                    db.session.add(categoria_residuo)

            db.session.commit()

            message = f"Categoria criada com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error create categoria: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao criar categoria.",
            )
        except SQLAlchemyError as error:
            message = f"Error create categoria: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")


        categoria_schema = CategoriaSchema()
        result = categoria_schema.dump(categoria)

        context = {
            "code": 200,
            "status": "OK",
            "message": message,
            "value": result
        }

        return jsonify(context)
    
