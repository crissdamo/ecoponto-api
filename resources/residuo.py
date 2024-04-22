import logging.handlers
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from models.categoria import CategoriaModel
from models.categoria_residuo import CategoriaResiduoModel
from models.residuo import ResiduoModel
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from extensions.database import db
from models.residuo import ResiduoModel
from schemas.categoria_residuo import PlainResiduoSchema, ResiduoSchema

blp = Blueprint("Resíduos", "resíduos", description="Operações sobre resíduos")


@blp.route("/residuo")
class Residuos(MethodView):

    @blp.arguments(PlainResiduoSchema)
    @blp.response(201, ResiduoSchema)
    def post(self, residuo_data):

        # Dados recebidos:
        
        descricao = residuo_data['descricao']
        icone = residuo_data.get('icone')
        url_midia = residuo_data.get('url_midia')
        recolhido_em_ecoponto = residuo_data.get('recolhido_em_ecoponto')
        categorias = residuo_data.get('categorias')

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
                    categoria_id = categoria.get('id_categoria')
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

        return residuo
    