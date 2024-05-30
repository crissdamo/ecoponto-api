from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required, get_jwt
import logging.handlers

from blocklist import BLOCKLIST
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from extensions.database import db


from models import UsuarioModel
from models.empresa import EmpresaModel
from models.perfil_usuario import PerfilUsuarioModel
from schemas.usuario import PlainUsuarioLoginSchema, UsuarioReturnSchema, UsuarioReturnTokenSchema, UsuarioSchema
from security import jwt_required_with_doc
from utilities.apenas_digitos import apenas_digitos
from utilities.valida_telefone import validar_telefone


blp = Blueprint("Usuários", "usuários", description="Operações sobre o usuário")


@blp.route("/registrar/admin")
class RegistrarUsuario(MethodView):
    @blp.response(200, UsuarioReturnSchema)
    @blp.arguments(UsuarioSchema)
    def post(self, usuario_data):

        email = usuario_data["email"]
        senha = usuario_data["senha"]
        telefone = usuario_data.get('telefone')
        nome = usuario_data.get('nome')
        equipe = True
        admin = True
        usuario_sistema = False

        if telefone:
            if not validar_telefone(telefone):
                abort(409, message="Formato do telefone inválido")
        
        telefone = apenas_digitos(str(telefone))
        

        if UsuarioModel.query.filter(UsuarioModel.email == email).first():
            abort(409, message="E-mail já cadastrado")
        
        usuario = UsuarioModel(
            email=email,
            senha=pbkdf2_sha256.hash(senha),
            equipe=equipe,
            admin=admin,
            sistema=usuario_sistema
        )

        perfil_usuario = PerfilUsuarioModel(
            nome=nome,
            telefone=telefone,
            email=email,
            usuario=usuario
        )

        # Salva em BD
        try:
            db.session.add(usuario)
            db.session.add(perfil_usuario)
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



        # return {"message": "Usuário criado com sucesso."}, 201

        usuario_schema = UsuarioSchema()
        result = usuario_schema.dump(usuario)
        result["nome"] = nome
        result["telefone"] = telefone
        result["equipe"] = equipe
        result["admin"] = admin
        result["sistema"] = usuario_sistema
    
        context = {
            "code": 201,
            "status": "Created",
            "message": "",
            "value": result
        }
        
        return jsonify(context)


@blp.route("/registrar/voluntario")
class RegistrarUsuario(MethodView):
    @blp.arguments(UsuarioSchema)
    @blp.response(200, UsuarioReturnSchema)
    def post(self, usuario_data):

        email = usuario_data["email"]
        senha = usuario_data["senha"]
        telefone = usuario_data.get('telefone')
        nome = usuario_data.get('nome')
        equipe = True
        admin = False
        usuario_sistema = False

        if telefone:
            print(telefone)
            if not validar_telefone(telefone):
                abort(409, message="Formato do telefone inválido")
        
        telefone = apenas_digitos(str(telefone))
        

        if UsuarioModel.query.filter(UsuarioModel.email == email).first():
            abort(409, message="E-mail já cadastrado")
        
        usuario = UsuarioModel(
            email=email,
            senha=pbkdf2_sha256.hash(senha),
            equipe=equipe,
            admin=admin,
            sistema=usuario_sistema
        )

        perfil_usuario = PerfilUsuarioModel(
            nome=nome,
            telefone=telefone,
            email=email,
            usuario=usuario
        )

        # Salva em BD
        try:
            db.session.add(usuario)
            db.session.add(perfil_usuario)
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



        # return {"message": "Usuário criado com sucesso."}, 201

        usuario_schema = UsuarioSchema()
        result = usuario_schema.dump(usuario)
        result["nome"] = nome
        result["telefone"] = telefone
        result["equipe"] = equipe
        result["admin"] = admin
        result["sistema"] = usuario_sistema
    
        context = {
            "code": 201,
            "status": "Created",
            "message": "",
            "value": result
        }
        
        return jsonify(context)


@blp.route("/registrar/usuariosistema")
class RegistrarUsuario(MethodView):
    @blp.arguments(UsuarioSchema)
    @blp.response(200, UsuarioReturnSchema)
    def post(self, usuario_data):

        email = usuario_data["email"]
        senha = usuario_data["senha"]
        telefone = usuario_data.get('telefone')
        nome = usuario_data.get('nome')
        equipe = False
        admin = False
        usuario_sistema = True

        if telefone:
            if not validar_telefone(telefone):
                abort(409, message="Formato do telefone inválido")
        
        telefone = apenas_digitos(str(telefone))
        

        if UsuarioModel.query.filter(UsuarioModel.email == email).first():
            abort(409, message="E-mail já cadastrado")
        
        usuario = UsuarioModel(
            email=email,
            senha=pbkdf2_sha256.hash(senha),
            equipe=equipe,
            admin=admin,
            sistema=usuario_sistema
        )

        perfil_usuario = PerfilUsuarioModel(
            nome=nome,
            telefone=telefone,
            email=email,
            usuario=usuario
        )

        # Salva em BD
        try:
            db.session.add(usuario)
            db.session.add(perfil_usuario)
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



        # return {"message": "Usuário criado com sucesso."}, 201

        usuario_schema = UsuarioSchema()
        result = usuario_schema.dump(usuario)
        result["nome"] = nome
        result["telefone"] = telefone
        result["equipe"] = equipe
        result["admin"] = admin
        result["sistema"] = usuario_sistema

        context = {
            "code": 201,
            "status": "Created",
            "message": "",
            "value": result
        }
        
        return jsonify(context)


@blp.route("/login")
class UsuarioLogin(MethodView):
    @blp.arguments(PlainUsuarioLoginSchema)
    @blp.response(200, UsuarioReturnTokenSchema)
    def post(self, usuario_data):
        email = usuario_data["email"]
        senha = usuario_data["senha"]
    
        usuario = UsuarioModel.query.filter(
            UsuarioModel.email == email
        ).first()

        if usuario and pbkdf2_sha256.verify(senha, usuario.senha):

            perfil_usuario = PerfilUsuarioModel.query.filter(
                PerfilUsuarioModel.usuario == usuario
            ).first()

            empresa_id = None
            nome_fantasia = None
            empresa = EmpresaModel.query.filter(EmpresaModel.usuario == usuario).first()
            if empresa:
                empresa_id = empresa.id
                nome_fantasia = empresa.nome_fantasia
            
            dados_usuario = {
                "sistema": usuario.sistema,
                "equipe": usuario.equipe,
                "admin": usuario.admin,
                "ativo": usuario.ativo,
                "empresa_id": empresa_id
            }

            access_token = create_access_token(
                identity=usuario.id, 
                additional_claims=dados_usuario, 
                fresh=True
            )
            refresh_token = create_refresh_token(identity=usuario.id)


            usuario_schema = UsuarioSchema()
            result = usuario_schema.dump(usuario)
            result["nome"] = perfil_usuario.nome
            result["telefone"] = perfil_usuario.telefone
            result["equipe"] = usuario.equipe
            result["admin"] = usuario.admin
            result["sistema"] = usuario.sistema
            result["token"] = {"access_token": access_token, "refresh_token": refresh_token}
            result["empresa"] = {"id": empresa_id,"nome_fantasia": nome_fantasia}

            context = {
                "code": 200,
                "status": "OK",
                "message": "",
                "value": result
            }
            
            return jsonify(context)
        
        abort(401, message="Credenciais inválidas.")


@blp.route("/refresh")
class TokenRefresh(MethodView):
    @jwt_required_with_doc(refresh=True)
    def post(self):
        usuario_atual = get_jwt_identity()
        novo_token = create_access_token(identity=usuario_atual, fresh=False)
        return {"access_token": novo_token}


@blp.route("/logout")
class usuarioLogout(MethodView):
    @jwt_required_with_doc()
    def post(self):
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"message": "Logout realizado com sucesso."}


# @blp.route("/usuario/<int:usuario_id>")
# class usuario(MethodView):
#     @blp.response(200, UsuarioSchema)
#     def get(self, usuario_id):
#         usuario = UsuarioModel.query.get_or_404(usuario_id)
#         return usuario

#     def delete(self, usuario_id):
#         usuario = UsuarioModel.query.get_or_404(usuario_id)
#         db.session.delete(usuario)
#         db.session.commit()
#         return {"message": "Usuario excluido."}, 200
    