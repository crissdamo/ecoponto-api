
import logging.handlers
from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from extensions.database import db

from models.arte_publicitaria import ArtePublicitariaModel
from models.ecoponto import EcopontoModel
from models.residuo import ResiduoModel
from schemas.arte_publicitaria import ArtePublicitariaSearchSchema, PlainArtePublicitariaGetListSchema, PlainArtePublicitariaGetSchema, PlainArtePublicitariaSchema

blp = Blueprint("Arte Publicitária", "arte publicitaria", description="Operações sobre arte publicitária")



@blp.route("/artepublicitaria/<int:artepublicitaria_id>")
class ArtePublicitaria(MethodView):
    """
        Classe para gerenciar as operações de obtenção, exclusão e atualização de arte publicitária.

        Rota:
            /artepublicitaria/<int:artepublicitaria_id>

        Métodos:
            get(artepublicitaria_id):
                Obtém os detalhes de uma arte publicitária.

            delete(artepublicitaria_id):
                Deleta uma arte publicitária.

            put(arte_publicitaria_data, artepublicitaria_id):
                Atualiza uma arte publicitária existente.
    """

    @blp.response(200, PlainArtePublicitariaGetSchema)
    def get(self, artepublicitaria_id):

        """
            Retorna os detalhes de uma arte publicitária.

            **Descrição**: Retorna os detalhes de uma arte publicitária.

            **Parâmetros**:
                artepublicitaria_id (int): ID da arte publicitária a ser obtida.

            **Retorna**:
                Um objeto JSON contendo:
                    - code: Código HTTP 200.
                    - status: "OK".
                    - message: Mensagem vazia.
                    - value: Informações da arte publicitária.
        """

        arte_publicitaria = ArtePublicitariaModel().query.get_or_404(artepublicitaria_id)
        arte_publicitaria_schema = PlainArtePublicitariaSchema()
        result = arte_publicitaria_schema.dump(arte_publicitaria)
        context = {
            "code": 200,
            "status": "OK",
            "message": "",
            "value": result
        }

        return jsonify(context)
    

    def delete(self, artepublicitaria_id):
        """
            Deleta uma arte publicitária.

            **Descrição**: Deleta uma arte publicitária.
            **Parâmetros**:
                artepublicitaria_id (int): ID da arte publicitária a ser deletada.

            **Retorna**:
                Um objeto JSON contendo:
                    - code: Código HTTP 200.
                    - status: "OK".
                    - message: Mensagem de sucesso ou erro.
                    - errors: Erros ocorridos durante a operação.
        """
        
        try:
            arte_publicitaria = ArtePublicitariaModel().query.get_or_404(artepublicitaria_id)
            db.session.delete(arte_publicitaria)
            db.session.commit()

            message = f"Arte publicitária excluída com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error delete arte publicitaria: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao deletar arte publicitária."
            )
        except SQLAlchemyError as error:
            message = f"Error delete arte publicitaria: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        context = {
            "code": 200,
            "status": "OK",
            "message": message,
            "errors": {}
        }

        return jsonify(context)
    
    @blp.arguments(PlainArtePublicitariaSchema)
    @blp.response(200, PlainArtePublicitariaGetSchema)
    def put(self, arte_publicitaria_data, artepublicitaria_id):

        """
            Atualiza uma arte publicitária existente.

            **Descrição**: Atualiza uma arte publicitária existente.

            **Parâmetros**:
                arte_publicitaria_data (dict): Dados recebidos para atualizar a arte publicitária.
                artepublicitaria_id (int): ID da arte publicitária a ser atualizada.

            **Retorna**:
                Um objeto JSON contendo:
                    - code: Código HTTP 200.
                    - status: "OK".
                    - message: Mensagem de sucesso ou erro.
                    - value: Informações da arte publicitária atualizada.
            
        """

        arte_publicitaria = ArtePublicitariaModel().query.get_or_404(artepublicitaria_id)
        arte_publicitaria.descricao = arte_publicitaria_data['descricao']
        arte_publicitaria.url_media = arte_publicitaria_data.get('url_media')
        arte_publicitaria.ativo = arte_publicitaria_data.get('ativo')
        arte_publicitaria.disponibilizar_ecoponto = arte_publicitaria_data.get('disponibilizar_ecoponto')
        arte_publicitaria.data_inicio = arte_publicitaria_data.get('data_inicio')
        arte_publicitaria.data_final = arte_publicitaria_data.get('data_final')
        arte_publicitaria.residuo_id = arte_publicitaria_data.get('residuo_id')
        

        # Salva em BD
        try:
            db.session.add(arte_publicitaria)
            db.session.commit()

            message = f"Arte publicitária editada com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error update arte publicitaria: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao editar arte publicitária.",
            )
        except SQLAlchemyError as error:
            message = f"Error update arte publicitaria: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        arte_publicitaria_schema = PlainArtePublicitariaSchema()
        result = arte_publicitaria_schema.dump(arte_publicitaria)

        context = {
            "code": 200,
            "status": "OK",
            "message": message,
            "value": result
        }

        return jsonify(context)


@blp.route("/artepublicitaria")
class ArtesPublicitarias(MethodView):
    """
        Endpoint para gerenciar artes publicitarias.

        Este endpoint permite buscar, criar e deletar artes publicitarias.

        Métodos:
        --------
        get(query_args):
            Busca artes publicitarias de acordo com os critérios fornecidos.
        
        post(arte_publicitaria_data):
            Cria um novo publicação.
        
      
    """
    
    @blp.arguments(ArtePublicitariaSearchSchema, location="query")
    @blp.response(200, PlainArtePublicitariaGetListSchema(many=True))
    def get(self, query_args):
        """
        Retorna uma lista paginada de artes publicitarias filtrados pelos critérios informados.

       **Descrição**: Filtra as artes publicitarias pelo ID do resíduo, se informado, 
        ou e pelos resíduos dos do ecoponto, se informado.
        Serão retornadas apenas artes publicitarias ativas e que estão disponíveis para ecoponto.

        **Parâmetros**:
            query_args (dict): Argumentos de consulta e para paginação.
                - residuo_id (int): ID do resíduo.
                - ecoponto_id (int): ID do ecoponto.
                - page (int): Número da página.
                - page_size (int): Número de registros por página.

            **Retorna**:
                Um objeto JSON com a lista de artes publicitarias filtrados pelos critérios informados e informações 
                de paginação.
        """

        result_lista = []

        residuo_id = query_args.get("residuo_id")
        ecoponto_id = query_args.get("ecoponto_id")

        pagina = int(query_args.get("page", 1))
        limite = int(query_args.get("page_size", 0))

        query = ArtePublicitariaModel.query.filter(ArtePublicitariaModel.ativo, ArtePublicitariaModel.disponibilizar_ecoponto)

  
        if residuo_id:
            query = query.filter(ArtePublicitariaModel.residuo_id == residuo_id)
        
        if ecoponto_id:
            ecoponto = EcopontoModel.query.filter(EcopontoModel.id == ecoponto_id).first()
            if ecoponto:
                residuos_ecoponto = ecoponto.residuo
                residuos_ecoponto_ids = [residuo_ecoponto.id for residuo_ecoponto in residuos_ecoponto]

                query = query.filter(ArtePublicitariaModel.residuo_id.in_(residuos_ecoponto_ids))


        total_registros = query.count()

        if limite < 1:
            limite = total_registros
        publicacoes = query.offset((pagina - 1) * limite).limit(limite).all()

        for arte in publicacoes:
            arte_publicitaria_schema = PlainArtePublicitariaSchema()
            result = arte_publicitaria_schema.dump(arte)
            
            result_lista.append(result)

        paginacao = {
            "total": total_registros,
            "page": pagina,
            "page_size": limite,
            "previous": pagina > 1,
            "next": total_registros > pagina * limite
        }

        context = {
            "code": 200,
            "status": "OK",
            "message": "",
            "values": result_lista,
            "pagination": paginacao
        }
        
        return jsonify(context)


    @blp.arguments(PlainArtePublicitariaSchema)
    @blp.response(201, PlainArtePublicitariaGetSchema)
    def post(self, arte_publicitaria_data):
        """
           Cria uma nova arte publicitária.

            **Descrição**: Cria uma nova arte publicitária.


            **Parâmetros**:
                arte_publicitaria_data : dict
                Dados recebidos para criar uma nova arte publicitária.
                Observação: são dados obrigatórios: url_midia e descrição. 
                O campo ativo, se não informado, receberá o valor de verdadeira.

            **Retorna**:
                Um objeto JSON contendo:
                    - code: Código HTTP 201.
                    - status: Mensagem "Created".
                    - message: Mensagem vazia.
                    - value: Informações do arte criado.
        """

        # Dados recebidos:

        descricao = arte_publicitaria_data['descricao']
        ativo = arte_publicitaria_data.get('ativo')
        disponibilizar_ecoponto = arte_publicitaria_data.get('disponibilizar_ecoponto')
        url_midia = arte_publicitaria_data.get('url_midia')
        data_inicio = arte_publicitaria_data.get('data_inicio')
        data_final = arte_publicitaria_data.get('data_final')
        residuo_id = arte_publicitaria_data.get('residuo_id')

        
        residuo = None
        if residuo_id:
            residuo = ResiduoModel().query.get_or_404(residuo_id)


        arte_publicitaria = ArtePublicitariaModel(
            descricao=descricao,
            url_midia=url_midia,
            data_inicio=data_inicio,
            data_final=data_final,
            ativo=ativo,
            disponibilizar_ecoponto=disponibilizar_ecoponto,
            residuo=residuo
        )


        # Salva em BD
        try:
            db.session.add(arte_publicitaria)
            db.session.commit()


            message = f"Arte publicitária criada com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            print(error)
            message = f"Error create arte publicitária: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao criar arte publicitária.",
            )
        except SQLAlchemyError as error:
            print(error)
            message = f"Error create arte publicitária: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        arte_publicitaria_schema = PlainArtePublicitariaSchema()
        result = arte_publicitaria_schema.dump(arte_publicitaria)
        context = {
            "code": 201,
            "status": "Created",
            "message": "",
            "value": result
        }

        return jsonify(context)

