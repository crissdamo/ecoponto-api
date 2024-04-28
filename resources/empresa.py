from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from models.aceite_termo import TermoAceiteModel
from models.empresa import EmpresaModel
from models.perfil_usuario import PerfilUsuarioModel
from models.termo import TermoModel
from models.usuario import UsuarioModel
from schemas.empresa_ecoponto import EmpresaSchema, PlainEmpresaSchema
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

    @blp.response(200, EmpresaSchema)
    def get(self, empresa_id):
        empresa = EmpresaModel().query.get_or_404(empresa_id)
        return empresa

    def delete(self, empresa_id):
        
        try:
            empresa = EmpresaModel().query.get_or_404(empresa_id)
            db.session.delete(empresa)
            db.session.commit()

            message = f"Empresa excluída com sucesso"
            logging.debug(message)
    
        except IntegrityError as error:
            message = f"Error delete empresa: {error}"
            logging.warning(message)
            abort(
                400,
                message="Erro ao deletar empresa.",
            )
        except SQLAlchemyError as error:
            message = f"Error delete empresa: {error}"
            logging.warning(message)
            abort(500, message="Server Error.")

        return {"mensagem": message}
    
    # @blp.arguments(EmpresaUpdateSchema)
    # @blp.response(200, EmpresaSchema)
    # def put(self, empresa_data, empresa_id):

    #     empresa = EmpresaModel.query.get(empresa_id)
    #     if empresa:
    #         item.price = item_data["price"]
    #         item.name = item_data["name"]


    #     else:
    #         item = EmpresaModel(id=empresa_id, **item_data)
        
    #     db.session.add(item)
    #     db.session.commit()

    #     return item


    #     empresa = EmpresaModel().query.get_or_404(empresa_id)
    #     raise NotImplementedError("Edição de empresa não está implementada")


@blp.route("/empresa")
class Empresas(MethodView):

    @blp.response(200, EmpresaSchema(many=True))
    def get(self):
        empresas = EmpresaModel().query.all()
        return empresas

    @blp.arguments(PlainEmpresaSchema, 
        description="Cria um novo registro no banco de dados.")
    @blp.response(201, EmpresaSchema)
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

        aceite_termos=empresa_data.get('aceite_termos')

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

        if aceite_termos:
            for termo in aceite_termos:
                
                aceite=termo.get('aceite')
                id_termo=termo.get('id_termo')

                termo_object = TermoModel().query.get_or_404(id_termo)
                
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

        return empresa
    
    # @blp.arguments(None, description="ATENÇÃO: resurso irá excluir todos os registros - usar somente em desenvolimento")
    # def delete(self):
    
    #     empresas = EmpresaModel.query.all()
    #     aceita_termo = TermoAceiteModel.query.all()

    #     # Deletar
    #     try:

    #         for aceite in aceita_termo:
    #             db.session.delete(aceite)

    #         for empresa in empresas:
    #             db.session.delete(empresa)
                
    #         db.session.commit()

    #         message = f"Empresas deletadas com sucesso"
    #         logging.debug(message)
    
    #     except IntegrityError as error:
    #         message = f"Error delete empresas: {error}"
    #         logging.warning(message)
    #         abort(
    #             400,
    #             message="Erro ao deletar empresas.",
    #         )
            
    #     except SQLAlchemyError as error:
    #         message = f"Error delete empresas: {error}"
    #         logging.warning(message)
    #         abort(500, message="Server Error.")

    #     return {"message": "Todos registros deletados."}
    