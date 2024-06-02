
import logging.handlers
from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from extensions.database import db

from models.categoria import CategoriaModel
from models.ecoponto import EcopontoModel
from models.publicacao import PublicacaoModel
from models.residuo import ResiduoModel
from models.secao_publicacao import SecaoPublicacaoModel
from schemas.publicacao import PlainPublicacaoSchema, PlainSecaoPublicacaoSchema, PublicacaoGetListSchema, PublicacaoGetSchema, PublicacaoPostSchema, PublicacaoSchema, PublicacaoSearchSchema, SecaoPublicacaoGetSchema

blp = Blueprint("Publicações", "publicacoes", description="Operações sobre publicações")



@blp.route("/publicacao/<int:publicacao_id>")
class Publicacao(MethodView):
    """
        Classe para gerenciar as operações de obtenção, exclusão e atualização de publicações.

        Rota:
            /publicacao/<int:publicacao_id>

        Métodos:
            get(publicacao_id):
                Obtém os detalhes de uma publicação.

            delete(publicacao_id):
                Deleta uma publicação e suas seções associadas.

            put(publicacao_data, publicacao_id):
                Atualiza uma publicação existente.
    """

    @blp.response(200, PublicacaoGetSchema)
    def get(self, publicacao_id):

        """
            Retorna os detalhes de uma publicação.

            **Descrição**: Retorna os detalhes de uma publicação.

            **Parâmetros**:
                publicacao_id (int): ID da publicação a ser obtida.

            **Retorna**:
                Um objeto JSON contendo:
                    - code: Código HTTP 200.
                    - status: "OK".
                    - message: Mensagem vazia.
                    - value: Informações da publicação.
        """

        publicacao = PublicacaoModel().query.get_or_404(publicacao_id)
        publicacao_schema = PublicacaoSchema()
        result = publicacao_schema.dump(publicacao)
        context = {
            "code": 200,
            "status": "OK",
            "message": "",
            "value": result
        }

        return jsonify(context)
    

    def delete(self, publicacao_id):
        """
            Deleta uma publicação e suas seções associadas.

            **Descrição**: Deleta uma publicação e suas seções associadas.
            **Parâmetros**:
                publicacao_id (int): ID da publicação a ser deletada.

            **Retorna**:
                Um objeto JSON contendo:
                    - code: Código HTTP 200.
                    - status: "OK".
                    - message: Mensagem de sucesso ou erro.
                    - errors: Erros ocorridos durante a operação.
        """
        
        try:
            publicacao = PublicacaoModel().query.get_or_404(publicacao_id)
            secoes = publicacao.secao_publicacao
            
            for secao in secoes:
                db.session.delete(secao)

            db.session.delete(publicacao)

            db.session.commit()

            message = f"Publicação excluída com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error delete publicacao: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao deletar publicação."
            )
        except SQLAlchemyError as error:
            message = f"Error delete publicação: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        context = {
            "code": 200,
            "status": "OK",
            "message": message,
            "errors": {}
        }

        return jsonify(context)
    
    @blp.arguments(PlainPublicacaoSchema)
    @blp.response(200, PublicacaoGetSchema)
    def put(self, publicacao_data, publicacao_id):

        """
            Atualiza uma publicação existente.

            **Descrição**: Atualiza uma publicação existente.

            **Parâmetros**:
                publicacao_data (dict): Dados recebidos para atualizar a publicação.
                publicacao_id (int): ID da publicação a ser atualizada.

            **Retorna**:
                Um objeto JSON contendo:
                    - code: Código HTTP 200.
                    - status: "OK".
                    - message: Mensagem de sucesso ou erro.
                    - value: Informações da publicação atualizada.
            
        """

        publicacao = PublicacaoModel().query.get_or_404(publicacao_id)
        publicacao.titulo = publicacao_data['titulo']
        publicacao.descricao = publicacao_data['descricao']
        publicacao.url_media = publicacao_data.get('url_media')
        publicacao.ativo = publicacao_data.get('ativo')
        publicacao.data_inicio = publicacao_data.get('data_inicio')
        publicacao.data_final = publicacao_data.get('data_final')
        publicacao.categoria_id = publicacao_data.get('categoria_id')
        publicacao.residuo_id = publicacao_data.get('residuo_id')
        

        # Salva em BD
        try:
            db.session.add(publicacao)
            db.session.commit()

            message = f"Publicação editada com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error update publicacao: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao editar publicação.",
            )
        except SQLAlchemyError as error:
            message = f"Error update publicacao: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        publicacao_schema = PublicacaoSchema()
        result = publicacao_schema.dump(publicacao)

        context = {
            "code": 200,
            "status": "OK",
            "message": message,
            "value": result
        }

        return jsonify(context)


@blp.route("/publicacao")
class Publicacoes(MethodView):
    """
        Endpoint para gerenciar publicações.

        Este endpoint permite buscar, criar e deletar publicações.

        Métodos:
        --------
        get(query_args):
            Busca publicações de acordo com os critérios fornecidos.
        
        post(publicacao_data):
            Cria um novo publicação.
        
    """
    
    @blp.arguments(PublicacaoSearchSchema, location="query")
    @blp.response(200, PublicacaoGetListSchema(many=True))
    def get(self, query_args):
        """
            Retorna uma lista paginada de publicações filtrados pelos critérios informados.

       **Descrição**: Filtra as publicações pelo ID do resíduo, se informado, e pelos resíduos dos do ecoponto, se informado, 
        ou pelo ID da categoria, se informado. Se uma palavra-chave for informada, irá pesquisar no texto da publicação e seção.
        Serão retornadas apenas publicações e seções ativas.

        **Parâmetros**:
            query_args (dict): Argumentos de consulta e para paginação.
                - residuo_id (int): ID do resíduo.
                - categoria_id (int): ID da categoria.
                - ecoponto_id (int): ID do ecoponto.
                - palavra_chave (str): Termo de pesquisa para buscar no texto da publicação e seção.
                - page (int): Número da página.
                - page_size (int): Número de registros por página.

            **Retorna**:
                Um objeto JSON com a lista de publicações filtrados pelos critérios informados e informações 
                de paginação.
        """

        result_lista = []

        residuo_id = query_args.get("residuo_id")
        categoria_id = query_args.get("categoria_id")
        ecoponto_id = query_args.get("ecoponto_id")
        palavra_chave = query_args.get("palavra_chave")

        pagina = int(query_args.get("page", 1))
        limite = int(query_args.get("page_size", 0))

        query = PublicacaoModel.query.filter(PublicacaoModel.ativo)

        if categoria_id:
            query = query.filter(PublicacaoModel.categoria_id == categoria_id)

        if residuo_id:
            query = query.filter(PublicacaoModel.residuo_id == residuo_id)
        
        if ecoponto_id:
            ecoponto = EcopontoModel.query.filter(EcopontoModel.id == ecoponto_id).first()
            if ecoponto:
                residuos_ecoponto = ecoponto.residuo
                residuos_ecoponto_ids = [residuo_ecoponto.id for residuo_ecoponto in residuos_ecoponto]

                query = query.filter(PublicacaoModel.residuo_id.in_(residuos_ecoponto_ids))

        if palavra_chave:
            query =  query.outerjoin(SecaoPublicacaoModel, PublicacaoModel.id == SecaoPublicacaoModel.publicacao_id).filter(or_(
                    PublicacaoModel.titulo.ilike(f'%{palavra_chave}%'), 
                    PublicacaoModel.descricao.ilike(f'%{palavra_chave}%'), 
                    SecaoPublicacaoModel.titulo.ilike(f'%{palavra_chave}%'), 
                    SecaoPublicacaoModel.descricao.ilike(f'%{palavra_chave}%'),
                )
            )

        total_registros = query.count()

        if limite < 1:
            limite = total_registros
        publicacoes = query.offset((pagina - 1) * limite).limit(limite).all()

        for publicacao in publicacoes:
            publicacao_schema = PublicacaoSchema()
            result = publicacao_schema.dump(publicacao)
            
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


    @blp.arguments(PublicacaoPostSchema)
    @blp.response(201, PublicacaoGetSchema)
    def post(self, publicacao_data):
        """
           Cria uma nova publicação.

            **Descrição**: Cria uma nova publicação. A publicação pode receber uma lista de seção (não obrigatória).


            **Parâmetros**:
                publicacao_data : dict
                Dados recebidos para criar uma nova publicação.
                Observação: são dados obrigatórios: título e descrição. 
                O campo ativo, se não informado, receberá o valor de verdadeira.
                Isso vale para Publicação e para a Seção.

            **Retorna**:
                Um objeto JSON contendo:
                    - code: Código HTTP 201.
                    - status: Mensagem "Created".
                    - message: Mensagem vazia.
                    - value: Informações do publicacao criado.
        """

        # Dados recebidos:

        titulo = publicacao_data['titulo']
        descricao = publicacao_data['descricao']
        ativo = publicacao_data.get('ativo')
        url_media = publicacao_data.get('url_media')
        data_inicio = publicacao_data.get('data_inicio')
        data_final = publicacao_data.get('data_final')

        categoria_id = publicacao_data.get('categoria_id')
        residuo_id = publicacao_data.get('residuo_id')

        secao_publicacao = publicacao_data.get('secao_publicacao')
        
        residuo = None
        if residuo_id:
            residuo = ResiduoModel().query.get_or_404(residuo_id)

        categoria = None
        if categoria_id:
            categoria = CategoriaModel().query.get_or_404(categoria_id)

        publicacao = PublicacaoModel(
            titulo=titulo,
            descricao=descricao,
            url_media=url_media,
            data_inicio=data_inicio,
            data_final=data_final,
            ativo=ativo,
            categoria=categoria,
            residuo=residuo
        )

        secao_list = []
        if secao_publicacao:
            for secao in secao_publicacao:
                
                titulo = secao['titulo']
                descricao = secao['descricao']
                ativo = secao.get('ativo')
                url_media = secao.get('url_media')
                data_inicio = secao.get('data_inicio')
                data_final = secao.get('data_final')

                secao_obj = SecaoPublicacaoModel(
                    titulo=titulo,
                    descricao=descricao,
                    url_media=url_media,
                    data_inicio=data_inicio,
                    data_final=data_final,
                    ativo=ativo,
                    publicacao=publicacao
                )
                secao_list.append(secao_obj)

    
        # Salva em BD
        try:
            db.session.add(publicacao)
           
            for secao in secao_list:
                 db.session.add(secao)

            db.session.commit()


            message = f"Publicação criada com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error create publicacao: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao criar publicação.",
            )
        except SQLAlchemyError as error:
            message = f"Error create publicacao: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        publicacao_schema = PublicacaoSchema()
        result = publicacao_schema.dump(publicacao)
        context = {
            "code": 201,
            "status": "Created",
            "message": "",
            "value": result
        }

        return jsonify(context)


@blp.route("/publicacao/secao/<int:publicacao_id>")
class PublicacaoSecao(MethodView):
    """
        Classe para gerenciar a criação de seções de publicações.

        Rota:
            /publicacao/secao/<int:publicacao_id>

        Métodos:
            post(secao_data, publicacao_id):
                Cria uma nova seção da publicação.
    """


    @blp.arguments(PlainSecaoPublicacaoSchema)
    @blp.response(201, SecaoPublicacaoGetSchema)
    def post(self, secao_data, publicacao_id):
        """
           Cria uma nova seção da publicação.

            **Descrição**: Cria uma nova seção para uma publicação existente.


            **Parâmetros**:
                secao_data : dict
                Dados recebidos para criar uma nova seção da publicação.
                Observação: são dados obrigatórios: título e descrição. 
                O campo ativo, se não informado, receberá o valor de verdadeira.

            **Retorna**:
                Um objeto JSON contendo:
                    - code: Código HTTP 201.
                    - status: Mensagem "Created".
                    - message: Mensagem vazia.
                    - value: Informações da seção criada.
        """

        publicacao = PublicacaoModel().query.get_or_404(publicacao_id)
        
        # Dados recebidos:
        titulo = secao_data['titulo']
        descricao = secao_data['descricao']
        ativo = secao_data.get('ativo')
        url_media = secao_data.get('url_media')
        data_inicio = secao_data.get('data_inicio')
        data_final = secao_data.get('data_final')

        secao = SecaoPublicacaoModel(
            titulo=titulo,
            descricao=descricao,
            url_media=url_media,
            data_inicio=data_inicio,
            data_final=data_final,
            ativo=ativo,
            publicacao=publicacao
        )
       
        # Salva em BD
        try:
            db.session.add(secao)
            db.session.commit()


            message = f"Seção da publicação criada com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error create secao_publicacao: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao criar seção da publicação.",
            )
        except SQLAlchemyError as error:
            message = f"Error create secao_publicacao: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        secao_schema = PlainSecaoPublicacaoSchema()
        result = secao_schema.dump(secao)
        context = {
            "code": 201,
            "status": "Created",
            "message": "",
            "value": result
        }

        return jsonify(context)


@blp.route("/publicacao/secao/<int:secao_id>")
class PublicacaoSecaoUpdate(MethodView):
    """
        Endpoint para gerenciar a atualização e exclusão de seções de publicações.

        Rota:
        /publicacao/secao/<int:secao_id>

        Métodos:
        --------
        delete(secao_id):
            Deleta uma seção da publicação.

        put(secao_data, secao_id):
            Edita uma seção da publicação.

    """

    
    def delete(self, secao_id):
        """
            Deleta uma seção da publicação.

            **Parâmetros**:
                secao_id (int): ID da seção a ser deletada.

            **Retorna**:
                Um objeto JSON contendo:
                    - code: Código HTTP 200.
                    - status: "OK".
                    - message: Mensagem de sucesso ou erro.
                    - errors: Erros ocorridos durante a operação.
        """
        
        try:
            secao = SecaoPublicacaoModel().query.get_or_404(secao_id)
            db.session.delete(secao)
            db.session.commit()

            message = f"Seção da publicação excluída com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error delete secao publicacao: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao deletar seção da publicação."
            )
        except SQLAlchemyError as error:
            message = f"Error delete secao publicação: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        context = {
            "code": 200,
            "status": "OK",
            "message": message,
            "errors": {}
        }

        return jsonify(context)
    

    @blp.arguments(PlainSecaoPublicacaoSchema)
    @blp.response(201, SecaoPublicacaoGetSchema)
    def put(self, secao_data, secao_id):
        """
           Edita uma seção de uma publicação.

            **Descrição**: Edita uma seção de uma publicação.


            **Parâmetros**:
                secao_data : dict
                Dados recebidos para editar uma seção da publicação.
                Observação: são dados obrigatórios: título e descrição. 
                O campo ativo, se não informado, receberá o valor de verdadeira.

            **Retorna**:
                Um objeto JSON contendo:
                    - code: Código HTTP 201.
                    - status: Mensagem "Created".
                    - message: Mensagem vazia.
                    - value: Informações da seção criada.
        """

        secao = SecaoPublicacaoModel().query.get_or_404(secao_id)
        
        # Dados recebidos:
        secao.titulo = secao_data['titulo']
        secao.descricao = secao_data['descricao']
        secao.ativo = secao_data.get('ativo')
        secao.url_media = secao_data.get('url_media')
        secao.data_inicio = secao_data.get('data_inicio')
        secao.data_final = secao_data.get('data_final')

       
        # Salva em BD
        try:
            db.session.add(secao)
            db.session.commit()


            message = f"Seção da publicação editada com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error update secao_publicacao: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao editar seção da publicação.",
            )
        except SQLAlchemyError as error:
            message = f"Error update secao_publicacao: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        secao_schema = PlainSecaoPublicacaoSchema()
        result = secao_schema.dump(secao)
        context = {
            "code": 201,
            "status": "Created",
            "message": "",
            "value": result
        }

        return jsonify(context)

