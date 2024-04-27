import logging.handlers
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from models.categoria import CategoriaModel
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from extensions.database import db
from models.categoria_residuo import CategoriaResiduoModel
from models.residuo import ResiduoModel
from schemas.categoria_residuo import CategoriaSchema, PlainCategoriaSchema

blp = Blueprint("Categorias", "Categorias", description="Operações sobre categorias de resíduos")


@blp.route("/categoria")
class Categorias(MethodView):

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
                    id_residuo = residuo.get('id_residuo')
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

        return categoria
    
    def delete(self):
    
        categorias = CategoriaModel.query.all()

        # Deletar
        try:

            for categoria in categorias:
                db.session.delete(categoria)
            db.session.commit()

            message = f"Categorias deletadas com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error delete categorias: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao deletar categorias.",
            )
            
        except SQLAlchemyError as error:
            message = f"Error delete categorias: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        return {"message": "Todos registros deletados."}
    