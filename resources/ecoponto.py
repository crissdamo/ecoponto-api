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
from models.enums.dia_semana import DiasSemanaEnum
from models.enums.situacao_ecoponto import SituacaoEnum
from models.localizacao import LocalizacaoModel
from models.residuo import ResiduoModel
from schemas.empresa_ecoponto import (
    EcopontoFuncionamentoSchema,
    EcopontoGetSchema,
    EcopontoListaSituacaoSchema,
    EcopontoLocalizacaoResiduoSchema,
    EcopontoLocalizacaoSchema,
    EcopontoResiduoSchema,
    EcopontoSearchSchema,
    EcopontoSituacaoSchema,
    RetornoEcopontoFuncionamentoSchema,
    RetornoEcopontoSchema,
    RetornoEcopontoResiduoSchema,
    RetornoEcopontoSituacaoSchema,
    RetornoListaEcopontoLocalizacaoSchema,
    RetornoListaEcopontoSchema,
)
from schemas.paginacao import PaginacaoSearchSchema

blp = Blueprint("Ecopontos", "ecopontos", description="Operações sobre ecopontos")

def retira_valor_enumSituacao(valor):
    enum = str(valor).split('.')
    enum = enum[-1]

    valor = SituacaoEnum[enum].value
    nome = SituacaoEnum[enum].name
    return valor, nome

def retira_valor_enumDiasSemana(valor):
    enum = str(valor).split('.')
    enum = enum[-1]
    valor = DiasSemanaEnum[enum].value
    nome = DiasSemanaEnum[enum].name
    return valor, nome

def transforma_dia_funcionamento(dias_funcionamento):

    for horario in dias_funcionamento:
        enum, dia = retira_valor_enumDiasSemana(horario['dia_semana'])
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
    """
        Endpoint para gerenciar um ecoponto específico.

        Este endpoint permite buscar, atualizar e deletar um ecoponto pelo seu ID.

        Métodos:
        --------
        get(ecoponto_id):
            Busca um ecoponto pelo seu ID.
        
        delete(ecoponto_id):
            Deleta um ecoponto pelo seu ID.
        
        put(ecoponto_data, ecoponto_id):
            Atualiza um ecoponto pelo seu ID.
    """

    @blp.response(200, RetornoEcopontoSchema)
    def get(self, ecoponto_id):
        """
            Busca um ecoponto pelo seu ID.

            **Descrição:** Busca o ecoponto pelo ID.
            Se ocorrer um erro durante a operação de banco de dados, retorna um erro 400 ou 500.

            **Parâmetros:**
                ecoponto_id (int): O ID do ecoponto a ser buscado.

            **Retorna:**
                Um objeto JSON com as informações do ecoponto.
        """
        ecoponto = EcopontoModel().query.get_or_404(ecoponto_id)
        ecoponto_schema = EcopontoGetSchema()
        result = ecoponto_schema.dump(ecoponto)
        dias_funcionamento = result.get('dia_funcionamento')

        # extrai valor do enum
        if dias_funcionamento:
            dia_funcionamento = transforma_dia_funcionamento(dias_funcionamento)
            result["dia_funcionamento"] = dia_funcionamento

            # agrupa horário de funcionamento em uma única string
            result["funcionamento"] = agrupar_horarios(dias_funcionamento)

        # extrai valor do enum
        situacao = result.get("situacao")

        if situacao:
            valor, nome = retira_valor_enumSituacao(situacao)
            result["situacao_enum"] = nome
            result["situacao"] = valor

        context = {
            "code": 200,
            "status": "OK",
            "message": "",
            "values": result
        }
        
        return jsonify(context)

    def delete(self, ecoponto_id):
        """
            Deleta um ecoponto pelo seu ID.

            **Descrição:** Deleta o ecoponto pelo seu ID.
            Se ocorrer um erro durante a operação de banco de dados, retorna um erro 400 ou 500.

            **Parâmetros:**
                ecoponto_id (int): O ID do ecoponto a ser deletado.

            **Retorna:**
                Um objeto JSON com mensagem de confirmação.
        """

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


    @blp.arguments(EcopontoLocalizacaoResiduoSchema)
    @blp.response(200, RetornoEcopontoSchema)
    def put(self, ecoponto_data, ecoponto_id):
        """
            Atualiza um ecoponto pelo seu ID.

            **Descrição:** Atualiza um ecoponto pelo seu ID.
            Se ocorrer um erro durante a operação de banco de dados, retorna um erro 400 ou 500.

            **Parâmetros:**
                ecoponto_data : dict
                    Dados recebidos para atualizar o ecoponto.
                ecoponto_id : int
                    ID do ecoponto a ser atualizado.

            **Retorna:**
                Um objeto JSON com as informações do ecoponto.
        """

        ecoponto = EcopontoModel().query.get_or_404(ecoponto_id)

        ecoponto.empresa_id = ecoponto_data['empresa_id']
        ecoponto.nome = ecoponto_data['nome']
        ecoponto.ativo = ecoponto_data.get('ativo')
        ecoponto.aberto_publico = ecoponto_data.get('aberto_publico')
        ecoponto.data_inicio = ecoponto_data.get('data_inicio')
        ecoponto.data_final = ecoponto_data.get('data_final')
        localizacao = ecoponto_data.get('localizacao')
        residuos = ecoponto_data.get('residuo')

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
        
        residuos_list = []
        residuos_relacionados = EcopontoResiduoModel.query.filter(
            EcopontoResiduoModel.ecoponto_id == ecoponto_id)

        # Salva em BD
        try:
            db.session.add(ecoponto)

            if localizacao_obj:
                db.session.add(localizacao_obj)

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

        ecoponto_schema = EcopontoGetSchema()
        result = ecoponto_schema.dump(ecoponto)

        dias_funcionamento = result.get('dia_funcionamento')

        # extrai valor do enum
        if dias_funcionamento:
            dia_funcionamento = transforma_dia_funcionamento(dias_funcionamento)
            result["dia_funcionamento"] = dia_funcionamento

            # agrupa horário de funcionamento em uma única string
            result["funcionamento"] = agrupar_horarios(dias_funcionamento)

        # extrai valor do enum
        situacao = result.get("situacao")

        if situacao:
            valor, nome = retira_valor_enumSituacao(situacao)
            result["situacao_enum"] = nome
            result["situacao"] = valor

        context = {
            "code": 200,
            "status": "OK",
            "message": "",
            "value": result
        }

        return jsonify(context)


@blp.route("/ecoponto")
class Ecopontos(MethodView):
    """
        Endpoint para gerenciar ecopontos.

        Este endpoint permite buscar, criar e deletar ecopontos.

        Métodos:
        --------
        get(query_args):
            Busca ecopontos de acordo com os critérios fornecidos.
        
        post(ecoponto_data):
            Cria um novo ecoponto.
        
        delete():
            Deleta todos os ecopontos e suas relações associadas.
    """
    
    @blp.arguments(EcopontoSearchSchema, location="query")
    @blp.response(200, RetornoListaEcopontoSchema(many=True))
    def get(self, query_args):
        """
            Retorna uma lista paginada de ecopontos filtrados pelos critérios informados.

            **Descrição**: Filtra os ecopontos pelo ID do resíduo, se informado, e pela localização, se informado 
                (pesquisa termo informado em qualquer um dos campos da localização do ecoponto). 
                Serão retornados apenas ecopontos ativos e com a situação "aprovado"

            **Parâmetros**:
                query_args (dict): Argumentos de consulta e para paginação.
                    - residuo_id (string): string com isd dos resíduos. Exemplo: "1, 3, 5, 9, 10".
                    - localizacao (str): termo que corresponde a parte de uma localização.
                    - page (int): Número da página.
                    - page_size (int): Número de registros por página.
                    - page_size (int): Número de registros por página.

            **Retorna**:
                Um objeto JSON com a lista de ecopontos filtrados pelos critérios informados e informações 
                de paginação.
        """

        result_lista = []
        residuo_id = query_args.get("residuo_id")
        localizacao = query_args.get("localizacao")

        pagina = int(query_args.get("page", 1))
        limite = int(query_args.get("page_size", 0))

        query = EcopontoModel.query.filter(EcopontoModel.ativo, EcopontoModel.situacao == "aprovado")

        if localizacao:
            query = query.join(LocalizacaoModel).filter(
                or_(
                    LocalizacaoModel.rua.ilike(f'%{localizacao}%'),
                    LocalizacaoModel.numero.ilike(f'%{localizacao}%'),
                    LocalizacaoModel.bairro.ilike(f'%{localizacao}%'),
                    LocalizacaoModel.cep.ilike(f'%{localizacao}%'),
                    LocalizacaoModel.cidade.ilike(f'%{localizacao}%'),
                    LocalizacaoModel.estado.ilike(f'%{localizacao}%'),
                    LocalizacaoModel.complemento.ilike(f'%{localizacao}%'),
                )
            )

        if residuo_id:
            try:
                ecopontos_ids = []
                # Sua string original
                s = residuo_id

                # Remover os colchetes
                s = s.strip("[]")

                # Remove os espaços em branco
                s = s.replace(" ", "")

                # Dividir a string em elementos individuais e converter para inteiros
                numbers = s.split(',')

                # Remover duplicatas mantendo a ordem
                unique_numbers = list(dict.fromkeys(numbers))

                for id in unique_numbers:
                    if str(id).isdigit():
                        residuo = ResiduoModel.query.filter(ResiduoModel.id == id).first()
                        if residuo:
                            ecopontos_ids += [ecoponto.id for ecoponto in residuo.ecoponto]
                if ecopontos_ids:
                    query = query.filter(EcopontoModel.id.in_(ecopontos_ids))

            except Exception as e:
                mensagem = f"Erro ao converter string em lista. {e}"
                logging.error(mensagem)

        total_registros = query.count()

        if limite < 1:
            limite = total_registros
        ecopontos = query.offset((pagina - 1) * limite).limit(limite).all()

        for ecoponto in ecopontos:
            ecoponto_schema = EcopontoGetSchema()
            result = ecoponto_schema.dump(ecoponto)
            dias_funcionamento = result.get('dia_funcionamento')

            if dias_funcionamento:
                dia_funcionamento = transforma_dia_funcionamento(dias_funcionamento)
                result["dia_funcionamento"] = dia_funcionamento
                result["funcionamento"] = agrupar_horarios(dias_funcionamento)

            situacao = result.get("situacao")
            if situacao:
                valor, nome = retira_valor_enumSituacao(situacao)
                result["situacao_enum"] = nome
                result["situacao"] = valor
            
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


    @blp.arguments(EcopontoLocalizacaoResiduoSchema)
    @blp.response(201, RetornoEcopontoSchema)
    def post(self, ecoponto_data):

        """
           Cria um novo ecoponto.

            **Descrição**: Cria um novo ecoponto.

            **Parâmetros**:
                ecoponto_data : dict
                Dados recebidos para criar um novo ecoponto.

            **Retorna**:
                Um objeto JSON contendo:
                    - code: Código HTTP 201.
                    - status: Mensagem "Created".
                    - message: Mensagem vazia.
                    - value: Informações do ecoponto criado.
        """

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

        ecoponto_schema = EcopontoGetSchema()
        result = ecoponto_schema.dump(ecoponto)
        context = {
            "code": 201,
            "status": "Created",
            "message": "",
            "value": result
        }

        return jsonify(context)


    def delete(self):
        """
            Deleta todos os ecopontos e suas relações associadas.

            **ATENÇÃO**: Deleta **TODOS** os ecopontos e suas relações associadas.

            **Retorna**:
                Um objeto JSON contendo uma mensagem de confirmação.
        """

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
    """
        Endpoint para gerenciar a relação de dias de funcionamento de um ecoponto.

        Este endpoint permite criar ou atualizar a relação de dias de funcionamento 
        associados a um ecoponto específico.

        Métodos:
        --------
        put(ecoponto_data):
            Atualiza a relação de dias de funcionamento de um ecoponto específico.
        
        post(ecoponto_data):
            Cria a relação de dias de funcionamento de um ecoponto específico.
    """

    @blp.arguments(EcopontoFuncionamentoSchema)
    @blp.response(200, RetornoEcopontoFuncionamentoSchema)
    def put(self, ecoponto_data):
        """
            Atualiza relação de dias de funcionamento de um ecoponto.

            **Descrição:** Busca o ecoponto pelo ID  e atualiza a relação de dias de funcionamento.
                Se ocorrer um erro durante a operação de banco de dados, retorna um erro 400 ou 500.

            **Parâmetros:**
                ecoponto_data : dict
                Dados recebidos contendo o ID do ecoponto e a lista de dias de funcionamento a serem associados.

            **Retorna:**
                Um objeto JSON com os ids do ecoponto e dos dias de funcionamento relacionados.
        """

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

        # extrai valor do enum
        dia_funcionamento = transforma_dia_funcionamento(dias_funcionamento)
        result["dia_funcionamento"] = dia_funcionamento


        # agrupa horário de funcionamento em uma única string
        result["funcionamento"] = agrupar_horarios(dias_funcionamento)

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
        """
            Cria relação de dias de funcionamento de um ecoponto.

            **Descrição:** Busca o ecoponto pelo ID  e cria a relação de dias de funcionamento.
                Se ocorrer um erro durante a operação de banco de dados, retorna um erro 400 ou 500.

            **Parâmetros:**
                ecoponto_data : dict
                Dados recebidos contendo o ID do ecoponto e a lista de dias de funcionamento a serem associados.

            **Retorna:**
                Um objeto JSON com os ids do ecoponto e dos dias de funcionamento relacionados.
        """

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

        # extrai valor do enum
        dia_funcionamento = transforma_dia_funcionamento(dias_funcionamento)
        result["dia_funcionamento"] = dia_funcionamento

        # agrupa horário de funcionamento em uma única string
        result["funcionamento"] = agrupar_horarios(dias_funcionamento)

        # extrai valor do enum
        situacao = result.get("situacao")
        if situacao:
            valor, nome = retira_valor_enumSituacao(situacao)
            result["situacao_enum"] = nome
            result["situacao"] = valor

        context = {
            "code": 201,
            "status": "Created",
            "message": "",
            "value": result
        }

        return jsonify(context)


@blp.route("/ecoponto/residuo")
class EcopontoResiduo(MethodView):
    """
        Endpoint para gerenciar a relação de resíduos de um ecoponto.

        Este endpoint permite criar ou atualizar a relação de resíduos associados a um ecoponto específico.

        Métodos:
        --------
        put(ecoponto_data):
            Atualiza a relação de resíduos de um ecoponto específico.
        
        post(ecoponto_data):
            Cria a relação de resíduos de um ecoponto específico.
    """

    @blp.arguments(EcopontoResiduoSchema)
    @blp.response(200, RetornoEcopontoResiduoSchema)
    def put(self, ecoponto_data):
        """
            Atualiza relação de resíduos de um ecoponto.

            **Descrição:** Busca o ecoponto pelo ID, busca cada um dos resíduos pelo iD informado e 
                atualiza relação com o ecoponto.
                Se ocorrer um erro durante a operação de banco de dados, retorna um erro 400 ou 500.

            **Parâmetros:**
                ecoponto_data : dict
                Dados recebidos contendo o ID do ecoponto e a lista de resíduos a serem associados.

            **Retorna:**
                Um objeto JSON com os ids do ecoponto e dos resíduos relacionados.
        """

        # Dados recebidos:
        ecoponto_id = ecoponto_data['ecoponto_id']
        # descricao_outros_projetos = ecoponto_data.get('descricao_outros_projetos')
        residuos = ecoponto_data.get('residuo')
        residuos_list = []

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

        # extrai valor do enum
        if dias_funcionamento:
            dia_funcionamento = transforma_dia_funcionamento(dias_funcionamento)
            result["dia_funcionamento"] = dia_funcionamento

            # agrupa horário de funcionamento em uma única string
            result["funcionamento"] = agrupar_horarios(dias_funcionamento)

        # extrai valor do enum
        situacao = result.get("situacao")

        if situacao:
            valor, nome = retira_valor_enumSituacao(situacao)
            result["situacao_enum"] = nome
            result["situacao"] = valor

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
        """
            Cria relação de resíduos de um ecoponto.

            **Descrição:** Busca o ecoponto pelo ID, busca cada um dos resíduos pelo iD informado e 
                cria relação com o ecoponto.
                Se ocorrer um erro durante a operação de banco de dados, retorna um erro 400 ou 500.

            **Parâmetros:**
                ecoponto_data : dict
                Dados recebidos contendo o ID do ecoponto e a lista de resíduos a serem associados.

            **Retorna:**
                Um objeto JSON com os ids do ecoponto e dos resíduos relacionados.
        """

        # Dados recebidos:

        ecoponto_id = ecoponto_data['ecoponto_id']
        # descricao_outros_projetos = ecoponto_data.get('descricao_outros_projetos')
        residuos = ecoponto_data.get('residuo')
        
        # Cria objetos:
        ecoponto = EcopontoModel().query.get_or_404(ecoponto_id)

        # # Salva em BD
        try:

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

        # extrai valor do enum
        if dias_funcionamento:
            dia_funcionamento = transforma_dia_funcionamento(dias_funcionamento)
            result["dia_funcionamento"] = dia_funcionamento

            # agrupa horário de funcionamento em uma única string
            result["funcionamento"] = agrupar_horarios(dias_funcionamento)

        # extrai valor do enum
        situacao = result.get("situacao")

        if situacao:
            valor, nome = retira_valor_enumSituacao(situacao)
            result["situacao_enum"] = nome
            result["situacao"] = valor

        context = {
            "code": 201,
            "status": "Created",
            "message": "",
            "value": result
        }

        return jsonify(context)


@blp.route("/ecoponto/ativar/<int:ecoponto_id>")
class EcopontoAtiva(MethodView):
    """
        Endpoint para ativar um ecoponto específico.

        Este endpoint permite ativar um ecoponto identificado por seu ID, definindo o campo 
        'ativo' como True.

        Métodos:
        --------
        put(ecoponto_id):
            Ativa o ecoponto especificado pelo ID.

        Parâmetros da URL:
        -----------------
        ecoponto_id : int
            O ID do ecoponto a ser ativado.

        Retorno:
        --------
        JSON:
            Um objeto JSON contendo:
            - code: Código HTTP 200.
            - status: Mensagem "OK".
            - message: Mensagem vazia.
            - values: Informações do ecoponto desativado, contendo:
                - dia_funcionamento: Dias de funcionamento formatados.
                - funcionamento: Horários de funcionamento agrupados.
                - situacao_enum: Nome da situação.
                - situacao: Valor da situação.
    """

    @blp.response(200, RetornoEcopontoSchema)
    def put(self, ecoponto_id):
        """
            Ativa o ecoponto especificado pelo ID.

            **Descrição:** Busca o ecoponto pelo ID fornecido e define seu campo 'ativo' como True.
            Se ocorrer um erro durante a operação de banco de dados, retorna um erro 400 ou 500.

            **Parâmetros:**
                ecoponto_id (int): O ID do ecoponto a ser ativado.

            **Retorna:**
                Um objeto JSON com as informações do ecoponto ativado.
        """

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
                message="Erro ao ativar ecoponto.",
            )
        except SQLAlchemyError as error:
            message = f"Error active ecoponto: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        ecoponto_schema = EcopontoGetSchema()
        result = ecoponto_schema.dump(ecoponto)
        dias_funcionamento = result.get('dia_funcionamento')

        # extrai valor do enum
        if dias_funcionamento:
            dia_funcionamento = transforma_dia_funcionamento(dias_funcionamento)
            result["dia_funcionamento"] = dia_funcionamento

            # agrupa horário de funcionamento em uma única string
            result["funcionamento"] = agrupar_horarios(dias_funcionamento)

        # extrai valor do enum
        situacao = result.get("situacao")

        if situacao:
            valor, nome = retira_valor_enumSituacao(situacao)
            result["situacao_enum"] = nome
            result["situacao"] = valor

        context = {
            "code": 200,
            "status": "OK",
            "message": "",
            "values": result
        }
        
        return jsonify(context)


@blp.route("/ecoponto/desativar/<int:ecoponto_id>")
class EcopontoDesativa(MethodView):
    """
        Endpoint para desativar um ecoponto específico.

        Este endpoint permite desativar um ecoponto identificado por seu ID, definindo o campo 
        'ativo' como False.

        Métodos:
        --------
        put(ecoponto_id):
            Desativa o ecoponto especificado pelo ID.

        Parâmetros da URL:
        -----------------
        ecoponto_id : int
            O ID do ecoponto a ser desativado.

        Retorno:
        --------
        JSON:
            Um objeto JSON contendo:
            - code: Código HTTP 200.
            - status: Mensagem "OK".
            - message: Mensagem vazia.
            - values: Informações do ecoponto desativado, contendo:
                - dia_funcionamento: Dias de funcionamento formatados.
                - funcionamento: Horários de funcionamento agrupados.
                - situacao_enum: Nome da situação.
                - situacao: Valor da situação.
    """

    @blp.response(200, RetornoEcopontoSchema)
    def put(self, ecoponto_id):
        """
            Desativa o ecoponto especificado pelo ID.

            **Descrição:** Busca o ecoponto pelo ID fornecido e define seu campo 'ativo' como False.
            Se ocorrer um erro durante a operação de banco de dados, retorna um erro 400 ou 500.

            **Parâmetros:**
                ecoponto_id (int): O ID do ecoponto a ser desativado.

            **Retorna:**
                Um objeto JSON com as informações do ecoponto desativado.
        """
                
        ecoponto = EcopontoModel().query.get_or_404(ecoponto_id)

        # Salva em BD
        try:
            db.session.add(ecoponto)
            if ecoponto:
                ecoponto.ativo = False
                db.session.add(ecoponto)
            db.session.commit()

            message = f"Ecoponto desativado com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error deactive ecoponto: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao desativar ecoponto.",
            )
        
        except SQLAlchemyError as error:
            message = f"Error deactive ecoponto: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        ecoponto_schema = EcopontoGetSchema()
        result = ecoponto_schema.dump(ecoponto)
        dias_funcionamento = result.get('dia_funcionamento')

        # extrai valor do enum
        if dias_funcionamento:
            dia_funcionamento = transforma_dia_funcionamento(dias_funcionamento)
            result["dia_funcionamento"] = dia_funcionamento

            # agrupa horário de funcionamento em uma única string
            result["funcionamento"] = agrupar_horarios(dias_funcionamento)

        # extrai valor do enum
        situacao = result.get("situacao")

        if situacao:
            valor, nome = retira_valor_enumSituacao(situacao)
            result["situacao_enum"] = nome
            result["situacao"] = valor

        context = {
            "code": 200,
            "status": "OK",
            "message": "",
            "values": result
        }
        
        return jsonify(context)


@blp.route("/ecoponto/<string:situacao>/<int:ecoponto_id>")
class EcopontoPutSituacao(MethodView):
    """
        Endpoint para atualizar a situação de um ecoponto específico.

        Este endpoint permite atualizar a situação de um ecoponto identificado por seu ID.
        A situação deve ser uma das seguintes: 'em_analise', 'aprovado' ou 'rejeitado'.

        Métodos:
        --------
        put(ecoponto_id, situacao):
            Atualiza a situação de um ecoponto.

        Parâmetros da URL:
        -----------------
        ecoponto_id : int
            O ID do ecoponto a ser atualizado.
        situacao : str
            A nova situação do ecoponto. Deve ser 'em_analise', 'aprovado', 'rejeitado' ou 'desativado'.

        Retorno:
        --------
        JSON:
            Um objeto JSON contendo:
            - code: Código HTTP 200.
            - status: Mensagem "OK".
            - message: Mensagem vazia.
            - values: Informações do ecoponto atualizado, contendo:
                - dia_funcionamento: Dias de funcionamento formatados.
                - funcionamento: Horários de funcionamento agrupados.
                - situacao_enum: Nome da situação.
                - situacao: Valor da situação.
    """

    @blp.response(200, RetornoEcopontoSchema)
    def put(self, situacao, ecoponto_id):
        """
             Atualiza a situação de um ecoponto.

            **Descrição:** Busca o ecoponto pelo ID fornecido e atualiza sua situação se a nova situação for válida.
            Se a situação não for válida, retorna um erro 400. Se ocorrer um erro durante a operação
            de banco de dados, retorna um erro 400 ou 500.

            **Parâmetros:**
                ecoponto_id (int): O ID do ecoponto a ser atualizado.
                situacao (str): A nova situação do ecoponto. ["em_analise", "aprovado", "rejeitado"].

            **Retorna:**
                Um objeto JSON com as informações do ecoponto atualizado.
        """
        
        ecoponto = EcopontoModel().query.get_or_404(ecoponto_id)

        if situacao != "em_analise" and situacao != "aprovado" and situacao != "rejeitado":
            abort(
                400,
                message="status inválido. Status deve ser 'em_analise', 'aprovado' ou 'rejeitado'",)

        # Salva em BD
        try:
            db.session.add(ecoponto)
            if ecoponto:
                ecoponto.situacao = situacao
                db.session.add(ecoponto)
            db.session.commit()

            message = f"situação do Ecoponto alterado com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error status ecoponto: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao alterar situacao ecoponto.",
            )
        except SQLAlchemyError as error:
            message = f"Error status ecoponto: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        ecoponto_schema = EcopontoGetSchema()
        result = ecoponto_schema.dump(ecoponto)

        dias_funcionamento = result.get('dia_funcionamento')

        # extrai valor do enum
        if dias_funcionamento:
            dia_funcionamento = transforma_dia_funcionamento(dias_funcionamento)
            result["dia_funcionamento"] = dia_funcionamento

            # agrupa horário de funcionamento em uma única string
            result["funcionamento"] = agrupar_horarios(dias_funcionamento)

        # extrai valor do enum
        situacao = result.get("situacao")

        if situacao:
            valor, nome = retira_valor_enumSituacao(situacao)
            result["situacao_enum"] = nome
            result["situacao"] = valor

        context = {
            "code": 200,
            "status": "OK",
            "message": "",
            "values": result
        }
        
        return jsonify(context)


@blp.route("/ecoponto/<string:situacao>")
class EcopontoGetSituacao(MethodView):
    """
        Endpoint para obter ecopontos filtrados por situação com paginação.

        Este endpoint retorna uma lista de ecopontos que correspondem à situação especificada
        na URL, com suporte a paginação. Cada ecoponto é detalhado com suas informações de
        funcionamento e situação.

        Métodos:
        --------
        get(query_args, situacao):
            Retorna uma lista paginada de ecopontos filtrados pela situação especificada.

        Parâmetros da URL:
        -----------------
        situacao : str
            A situação dos ecopontos a serem filtrados 
            (e.g., "aprovado", "rejeitado", "em_analise").

        Parâmetros de Consulta:
        -----------------------
        query_args : dict
            Dicionário de argumentos de consulta contendo:
            - page: Número da página (padrão é 1).
            - page_size: Número de registros por página (padrão é 0, que retorna todos).

        Retorno:
        --------
        JSON:
            Um objeto JSON contendo:
            - code: Código HTTP 200.
            - status: Mensagem "OK".
            - message: Mensagem vazia.
            - values: Lista de ecopontos, cada um contendo:
                - dia_funcionamento: Dias de funcionamento formatados.
                - funcionamento: Horários de funcionamento agrupados.
                - situacao_enum: Nome da situação.
                - situacao: Valor da situação.
            - pagination: Informações de paginação, contendo:
                - total: Número total de registros.
                - page: Página atual.
                - page_size: Tamanho da página.
                - previous: Indicador se há página anterior.
                - next: Indicador se há próxima página.
    """

    @blp.arguments(PaginacaoSearchSchema, location="query")
    @blp.response(200, RetornoListaEcopontoLocalizacaoSchema)
    def get(self, query_args, situacao):
        """
            Retorna uma lista paginada de ecopontos filtrados pela situação especificada.

            **Descrição**: Filtra os ecopontos pela situação fornecida na URL, aplica paginação de acordo 
            com os parâmetros de consulta.

            **Parâmetros**:
                query_args (dict): Argumentos de consulta para paginação.
                    - page (int): Número da página.
                    - page_size (int): Número de registros por página.
                situacao (str): A situação dos ecopontos a serem filtrados ["em_analise", "aprovado", "rejeitado"].

            **Retorna**:
                Um objeto JSON com a lista de ecopontos filtrados pela situação e informações 
                de paginação.
        """

        if situacao != "em_analise" and situacao != "aprovado" and situacao != "rejeitado":
            abort(
                400,
                message="status inválido. Status deve ser 'em_analise', 'aprovado' ou 'rejeitado'",)

        
        result_lista = []

        pagina = int(query_args.get("page", 1))
        limite = int(query_args.get("page_size", 0))

        query = EcopontoModel.query.filter(EcopontoModel.situacao == situacao)

        total_registros = query.count()

        if limite < 1:
            limite = total_registros
        ecopontos = query.offset((pagina - 1) * limite).limit(limite).all()

        for ecoponto in ecopontos:
            ecoponto_schema = EcopontoLocalizacaoSchema()
            result = ecoponto_schema.dump(ecoponto)
            dias_funcionamento = result.get('dia_funcionamento')

            # extrai valor do enum
            if dias_funcionamento:
                dia_funcionamento = transforma_dia_funcionamento(dias_funcionamento)
                result["dia_funcionamento"] = dia_funcionamento

                # agrupa horário de funcionamento em uma única string
                result["funcionamento"] = agrupar_horarios(dias_funcionamento)

            # extrai valor do enum
            situacao = result.get("situacao")

            if situacao:
                valor, nome = retira_valor_enumSituacao(situacao)
                result["situacao_enum"] = nome
                result["situacao"] = valor
            
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


@blp.route("/ecoponto/situacao")
class EcopontoSituacao(MethodView):
    """
        Endpoint para obter a lista de todas as situações possíveis de um ecoponto.

        Este endpoint retorna todas as situações definidas no enum `SituacaoEnum`, 
        com seus respectivos valores e nomes.

        Métodos:
        --------
        get:
            Retorna a lista de todas as situações do ecoponto.

        Retorno:
        --------
        JSON:
            Um objeto JSON contendo:
            - code: Código HTTP 200.
            - status: Mensagem "OK".
            - message: Mensagem vazia.
            - values: Lista de situações do ecoponto, cada uma contendo:
                - situacao_enum: Nome da situação.
                - situacao: Valor da situação.
    """

    @blp.response(200, RetornoEcopontoSituacaoSchema)
    def get(self):
        """
            Retorna a lista de todas as situações possíveis de um ecoponto.

            **Descrição**: Consulta o enum `SituacaoEnum` para obter todas as situações, 
            formata cada situação em um dicionário.

            **Retorna**:
                Um objeto JSON com a lista de todas as situações do ecoponto:
                valor do enumerador e o valor para apresentar ao usuário
        """

        result_list = []

        situacoes = SituacaoEnum
        for e in situacoes:
            
            result = {}
            result["situacao_enum"] = e.name
            result["situacao"] = e.value
            situacao_schema = EcopontoSituacaoSchema()
            result = situacao_schema.dump(result)
            result_list.append(result)

        context = {
            "code": 200,
            "status": "OK",
            "message": "",
            "values": result_list
        }
        
        return jsonify(context)


@blp.route("/ecoponto/controle")
class EcopontoControle(MethodView):
    """
        Endpoint para obter listas de todos os ecopontos separados por situação.

        Rota:
        /ecoponto/controle

        Métodos:
        --------
        get:
            Retorna listas de ecopontos por situação.

    """

    @blp.response(200, EcopontoListaSituacaoSchema)
    def get(self):

        """
            Retorna uma lista de todos os ecopontos, agrupados por situação.

            **Descrição:** Recupera todos os ecopontos do banco de dados, organiza-os por suas situações
             e retorna um resumo contendo o total
            de ecopontos em cada situação e uma lista detalhada dos ecopontos.

            **Retorna:**
                Um objeto JSON contendo o código de status, a mensagem, e os dados agrupados 
                por situação, incluindo o total de ecopontos e detalhes de cada ecoponto.

            
        """

        result_list = []
        result_dict = {}
        ecopontos = EcopontoModel.query.all()

        for situacao in SituacaoEnum:
            result_dict[situacao.name] = {"total": 0, "situacao":situacao.value, "situacao_enum": situacao.name, "ecopontos": []}
   
        for ecoponto in ecopontos:
            ecoponto_schema = EcopontoGetSchema()
            result = ecoponto_schema.dump(ecoponto)
            dias_funcionamento = result.get('dia_funcionamento')
            result["funcionamento"] = ""

            if dias_funcionamento:
                dia_funcionamento = transforma_dia_funcionamento(dias_funcionamento)
                result["dia_funcionamento"] = dia_funcionamento
                
                # funcionamento como string
                funcionamento = agrupar_horarios(dias_funcionamento)
                result["funcionamento"] = funcionamento

                # Funcionamentos como lista
                funcionamentos = funcionamento.replace(' e ', ', ')
                lista = [item.strip() for item in funcionamentos.split(',')]
                result["funcionamentos"] = lista

            situacao = result.get("situacao")
            if situacao:
                valor, nome = retira_valor_enumSituacao(situacao)
                result["situacao_enum"] = nome
                result["situacao"] = valor

                result_dict[nome]['total'] += 1
                result_dict[nome]['ecopontos'].append(result)

        for result in result_dict:
            result_list.append(result_dict[result])
            
        context = {
            "code": 200,
            "status": "OK",
            "message": "",
            "values": result_list,
        }
        
        return jsonify(context)
        