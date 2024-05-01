from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import jsonify
from passlib.hash import pbkdf2_sha256
from models.aceite_termo import TermoAceiteModel
from models.dia_funcionamento import DiaFuncionamentoModel
from models.ecoponto import EcopontoModel
from models.ecoponto_residuo import EcopontoResiduoModel
from models.empresa import EmpresaModel
from models.enums.dia_semana import DiasSemanaEnum
from models.enums.situacao_ecoponto import SituacaoEnum
from models.localizacao import LocalizacaoModel
from models.perfil_usuario import PerfilUsuarioModel
from models.residuo import ResiduoModel
from models.termo import TermoModel
from models.usuario import UsuarioModel
from schemas.empresa_ecoponto import (
    EmpresaGetSchema, EmpresaSchema, EmpresaUpdateSchema, PlainEmpresaSchema, 
    RetornoEmpresaGetSchema, RetornoEmpresaSchema, 
    RetornoListaEmpresaSchema, RetornoPlainEmpresaSchema)
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from extensions.database import db

import logging.handlers

from utilities.apenas_digitos import apenas_digitos
from utilities.valida_email import validar_email
from utilities.valida_cnpj import validar_cnpj
from utilities.valida_telefone import validar_telefone

blp = Blueprint("Empresas", "empresas", description="Operations on empresas")


@blp.route("/empresa/<int:empresa_id>")
class Empresa(MethodView):

    @blp.response(200, RetornoEmpresaGetSchema)
    def get(self, empresa_id):
        empresa = EmpresaModel().query.get_or_404(empresa_id, )
        empresa_schema = EmpresaGetSchema()
        result = empresa_schema.dump(empresa)
        context = {
            "code": 200,
            "status": "OK",
            "message": "",
            "value": result
        }

        return jsonify(context)
    

    def delete(self, empresa_id):
        
        try:
            empresa = EmpresaModel().query.get_or_404(empresa_id)
            usuario = empresa.usuario
            perfil = PerfilUsuarioModel().query.filter(usuario).first()
            db.session.delete(empresa)
            db.session.delete(perfil)
            db.session.delete(usuario)
            db.session.commit()

            message = f"Empresa excluída com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error delete empresa: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao deletar empresa."
            )
        except SQLAlchemyError as error:
            message = f"Error delete empresa: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        context = {
            "code": 200,
            "status": "OK",
            "message": message,
            "errors": {}
        }

        return jsonify(context)
    
    @blp.arguments(EmpresaUpdateSchema)
    @blp.response(200, RetornoEmpresaSchema)
    def put(self, empresa_data, empresa_id):

        print(empresa_id)

        empresa = EmpresaModel().query.get_or_404(empresa_id)
        
        email = empresa_data['email']
        cnpj=empresa_data['cnpj']
        telefone_contato = empresa_data['telefone']
        senha = empresa_data["senha"]
        nome_contato_responsavel = empresa_data['nome_contato_responsavel']

        cnpj = apenas_digitos(str(cnpj))
        telefone_contato = apenas_digitos(str(telefone_contato))

        empresa.email = email
        empresa.nome_contato_responsavel = nome_contato_responsavel
        empresa.telefone_contato = telefone_contato
        empresa.nome_fantasia=empresa_data['nome_fantasia']
        empresa.razao_social=empresa_data.get('razao_social')
        empresa.cnpj=cnpj
        empresa.ramo_atuacao=empresa_data.get('ramo_atuacao')
        empresa.rede_social=empresa_data.get('rede_social')
        empresa.participacao_outros_projetos=empresa_data.get('participacao_outros_projetos')
        empresa.descricao_outros_projetos=empresa_data.get('descricao_outros_projetos')

        aceite_termo=empresa_data.get('aceite_termo')
        print(aceite_termo)

        termos_list = []

        # validações:

    
        if not validar_cnpj(cnpj):
            abort(409, message="CNPJ inválido")

        if  empresa.cnpj != cnpj:
            if EmpresaModel.query.filter(EmpresaModel.cnpj == cnpj).first():
                abort(409, message="CNPJ já cadastrado")

        if not validar_email(email):
            abort(409, message="CNPJ inválido")
        
        if not validar_telefone(telefone_contato):
            abort(409, message="Formato do telefone inválido")
        
        # Cria objetos:

        usuario = empresa.usuario

        if usuario.email != email:
            if UsuarioModel.query.filter(UsuarioModel.email == email).first():
                abort(409, message="E-mail já cadastrado")
            usuario.email = email
        
        if usuario.senha != pbkdf2_sha256.hash(senha):
            usuario.senha = pbkdf2_sha256.hash(senha)
        
        perfil_usuario = PerfilUsuarioModel.query.filter(PerfilUsuarioModel.usuario == usuario).first()
        perfil_usuario.nome=nome_contato_responsavel
        perfil_usuario.telefone=telefone_contato
        perfil_usuario.email=email
        
        if aceite_termo:
            for termo in aceite_termo:
                
                aceite=termo.get('aceite')
                termo_id=termo.get('termo_id')

                termo_object = TermoModel().query.get_or_404(termo_id)
                
                aceite_termo = TermoAceiteModel(
                    aceite=aceite,
                    termo=termo_object,
                    empresa=empresa
                )
                termos_list.append(aceite_termo)


        # Salva em BD
        try:
            db.session.add(usuario)
            db.session.add(perfil_usuario)
            db.session.add(empresa)

            for aceite in termos_list:
                db.session.add(aceite)

            db.session.commit()

            message = f"Empresa criada com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error create empresa: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao criar empresa.",
            )
        except SQLAlchemyError as error:
            message = f"Error create empresa: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        empresa_schema = EmpresaSchema()
        result = empresa_schema.dump(empresa)
        context = {
            "code": 201,
            "status": "Created",
            "message": message,
            "value": result
        }

        return jsonify(context)


@blp.route("/empresa")
class Empresas(MethodView):

    @blp.response(200, RetornoListaEmpresaSchema)
    def get(self):
        result_lista = []
        empresas = EmpresaModel().query.all()
        for empresa in empresas:
            empresa_schema = EmpresaGetSchema()
            result = empresa_schema.dump(empresa)
            result_lista.append(result)

        context = {
            "code": 200,
            "status": "OK",
            "message": "",
            "values": result_lista
        }
        
        return jsonify(context)
    

    @blp.arguments(PlainEmpresaSchema, 
        description="Cria um novo registro no banco de dados.")
    @blp.response(201, RetornoPlainEmpresaSchema)
    def post(self, empresa_data):

        # Dados recebidos:
        email = empresa_data['email']
        senha = empresa_data["senha"]
        nome_contato_responsavel = empresa_data['nome_contato_responsavel']
        telefone_contato = empresa_data['telefone']
        nome_fantasia=empresa_data['nome_fantasia']
        razao_social=empresa_data.get('razao_social')
        cnpj=empresa_data['cnpj']
        ramo_atuacao=empresa_data.get('ramo_atuacao')
        rede_social=empresa_data.get('rede_social')
        participacao_outros_projetos=empresa_data.get('participacao_outros_projetos')
        descricao_outros_projetos=empresa_data.get('descricao_outros_projetos')

        aceite_termo=empresa_data.get('aceite_termo')

        termos_list = []

        # validações:

        if UsuarioModel.query.filter(UsuarioModel.email == email).first():
            abort(409, message="E-mail já cadastrado")

        if not validar_cnpj(cnpj):
            abort(409, message="CNPJ inválido")
        
        if EmpresaModel.query.filter(EmpresaModel.cnpj == cnpj).first():
            abort(409, message="CNPJ já cadastrado")

        if not validar_email(email):
            abort(409, message="CNPJ inválido")
        
        if not validar_telefone(telefone_contato):
            abort(409, message="Formato do telefone inválido")
        
        cnpj = apenas_digitos(str(cnpj))
        telefone_contato = apenas_digitos(str(telefone_contato))

        # Cria objetos:

        usuario = UsuarioModel(
            email=email,
            senha=pbkdf2_sha256.hash(senha)
        )

        perfil_usuario = PerfilUsuarioModel(
            nome=nome_contato_responsavel,
            telefone=telefone_contato,
            email=email,
            usuario=usuario
        )

        empresa = EmpresaModel(
            nome_fantasia=nome_fantasia,
            razao_social=razao_social,
            cnpj=cnpj,
            ramo_atuacao=ramo_atuacao,
            telefone=telefone_contato,
            email=email,
            rede_social=rede_social,
            participacao_outros_projetos=participacao_outros_projetos,
            descricao_outros_projetos=descricao_outros_projetos,
            nome_contato_responsavel=nome_contato_responsavel,
            usuario=usuario
        )

        if aceite_termo:
            for termo in aceite_termo:
                
                aceite=termo.get('aceite')
                termo_id=termo.get('termo_id')

                termo_object = TermoModel().query.get_or_404(termo_id)
                
                aceite_termo = TermoAceiteModel(
                    aceite=aceite,
                    termo=termo_object,
                    empresa=empresa
                )
                termos_list.append(aceite_termo)


        # Salva em BD
        try:
            db.session.add(usuario)
            db.session.add(perfil_usuario)
            db.session.add(empresa)

            for aceite in termos_list:
                 db.session.add(aceite)

            db.session.commit()

            message = f"Empresa criada com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error create empresa: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao criar empresa.",
            )
        except SQLAlchemyError as error:
            message = f"Error create empresa: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        empresa_schema = EmpresaSchema()
        result = empresa_schema.dump(empresa)
        context = {
            "code": 201,
            "status": "Created",
            "message": "",
            "value": result
        }

        return jsonify(context)

    
    def delete(self):
    
        empresas = EmpresaModel.query.all()
        aceita_termo = TermoAceiteModel.query.all()
        perfilusuarios = PerfilUsuarioModel.query.all()
        usuarios = UsuarioModel.query.all()

        # Deletar
        try:

            for aceite in aceita_termo:
                db.session.delete(aceite)

            for empresa in empresas:
                db.session.delete(empresa)

            for perfil in perfilusuarios:
                db.session.delete(perfil)
                
            for usuario in usuarios:
                db.session.delete(usuario)
                
            db.session.commit()

            message = f"Empresas deletadas com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error delete empresas: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao deletar empresas.",
            )
            
        except SQLAlchemyError as error:
            message = f"Error delete empresas: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        return {"message": "Todos registros deletados."}
    

@blp.route("/empresa/ecoponto")
class Empresas(MethodView):

    @blp.arguments(EmpresaSchema, 
        description="Super rota: cria um novo registro no banco de dados para empresa e ecoponto e todas as suas dependências.")
    @blp.response(201, RetornoEmpresaSchema)
    def post(self, empresa_data):


        # Fase 1: Dados Empresa / Usuário / Perfil Usuário:
        email = empresa_data['email']
        senha = empresa_data["senha"]
        nome_contato_responsavel = empresa_data['nome_contato_responsavel']
        telefone_contato = empresa_data['telefone']
        nome_fantasia=empresa_data['nome_fantasia']
        razao_social=empresa_data.get('razao_social')
        cnpj=empresa_data['cnpj']
        ramo_atuacao=empresa_data.get('ramo_atuacao')
        rede_social=empresa_data.get('rede_social')
        participacao_outros_projetos=empresa_data.get('participacao_outros_projetos')
        descricao_outros_projetos=empresa_data.get('descricao_outros_projetos')

        aceite_termo=empresa_data.get('aceite_termo')

        termos_list = []

        # validações:

        if UsuarioModel.query.filter(UsuarioModel.email == email).first():
            abort(409, message="E-mail já cadastrado")

        if not validar_cnpj(cnpj):
            abort(409, message="CNPJ inválido")
        
        if EmpresaModel.query.filter(EmpresaModel.cnpj == cnpj).first():
            abort(409, message="CNPJ já cadastrado")

        if not validar_email(email):
            abort(409, message="CNPJ inválido")
        
        if not validar_telefone(telefone_contato):
            abort(409, message="Formato do telefone inválido")
        
        cnpj = apenas_digitos(str(cnpj))
        telefone_contato = apenas_digitos(str(telefone_contato))

        # Cria objetos:

        usuario = UsuarioModel(
            email=email,
            senha=pbkdf2_sha256.hash(senha)
        )

        perfil_usuario = PerfilUsuarioModel(
            nome=nome_contato_responsavel,
            telefone=telefone_contato,
            email=email,
            usuario=usuario
        )

        empresa = EmpresaModel(
            nome_fantasia=nome_fantasia,
            razao_social=razao_social,
            cnpj=cnpj,
            ramo_atuacao=ramo_atuacao,
            telefone=telefone_contato,
            email=email,
            rede_social=rede_social,
            participacao_outros_projetos=participacao_outros_projetos,
            descricao_outros_projetos=descricao_outros_projetos,
            nome_contato_responsavel=nome_contato_responsavel,
            usuario=usuario
        )

        if aceite_termo:
            for termo in aceite_termo:
                
                aceite=termo.get('aceite')
                termo_id=termo.get('termo_id')

                termo_object = TermoModel().query.get_or_404(termo_id)
                
                aceite_termo = TermoAceiteModel(
                    aceite=aceite,
                    termo=termo_object,
                    empresa=empresa
                )
                termos_list.append(aceite_termo)



        # Fase 2: Dados Ecoponto / Localização / dia funcionamento / residuos
        ecoponto = None
        ecoponto_data=empresa_data.get('ecopontos')

        if ecoponto_data:
            if len(ecoponto_data) > 1:
                abort(409, message="Enviar apenas um ecoponto por vez")
            
            ecoponto_data = ecoponto_data[0]
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

            ecoponto = EcopontoModel(
                nome=nome,
                ativo=ativo,
                aberto_publico=aberto_publico,
                data_inicio=data_inicio,
                data_final=data_final,
                situacao=SituacaoEnum.em_analise,
                empresa=empresa
            )

            if dias_funcionamento:
                for funcionamento in dias_funcionamento:
                    
                    dia_semana = funcionamento.get('dia_semana')
                    hora_inicial = funcionamento.get('hora_inicial')
                    hora_final = funcionamento.get('hora_final')

                    dia_funcionamento_obj = DiaFuncionamentoModel(
                        dia_semana=DiasSemanaEnum[dia_semana],
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

        # Salva em BD
        try:
            db.session.add(usuario)
            db.session.add(perfil_usuario)
            db.session.add(empresa)

            for aceite in termos_list:
                 db.session.add(aceite)

            if ecoponto:
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

            message = f"Empresa criada com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error create empresa: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao criar empresa.",
            )
        except SQLAlchemyError as error:
            message = f"Error create empresa: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        empresa_schema = EmpresaSchema()
        result = empresa_schema.dump(empresa)
        context = {
            "code": 201,
            "status": "Created",
            "message": message,
            "value": result
        }

        return jsonify(context)
