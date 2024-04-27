from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required, get_jwt

from blocklist import BLOCKLIST
from extensions.database import db

from models import UsuarioModel
from schemas.usuario import PlainUsuarioSchema


blp = Blueprint("Usuários", "usuários", description="Operações sobre o usuário")


@blp.route("/registrar")
class RegistrarUsuario(MethodView):
    @blp.arguments(PlainUsuarioSchema)
    def post(self, usuario_data):

        email = usuario_data["email"]

        if UsuarioModel.query.filter(UsuarioModel.email == email).first():
            abort(409, message="E-mail já cadastrado")
        
        usuario = UsuarioModel(
            email=usuario_data["email"],
            senha=pbkdf2_sha256.hash(usuario_data["senha"])
        )
        db.session.add(usuario)
        db.session.commit()

        return {"message": "Usuário criado com sucesso."}, 201


# @blp.route("/login")
# class UsuarioLogin(MethodView):
#     @blp.arguments(PlainUsuarioSchema)
#     def post(self, usuario_data):
#         usuario = UsuarioModel.query.filter(
#             UsuarioModel.email == usuario_data["email"]
#         ).first()

#         if usuario and pbkdf2_sha256.verify(usuario_data["senha"], usuario.senha):
#             access_token = create_access_token(identity=usuario.id, fresh=True)
#             refresh_token = create_refresh_token(identity=usuario.id)
#             return {"access_token": access_token, "refresh_token": refresh_token}
        
#         abort(401, message="Credenciais inválidas.")


# @blp.route("/refresh")
# class TokenRefresh(MethodView):
#     @jwt_required(refresh=True)
#     def post(self):
#         usuario_atual = get_jwt_identity()
#         novo_token = create_access_token(identity=usuario_atual, fresh=False)
#         return {"access_token": novo_token}


# @blp.route("/logout")
# class usuarioLogout(MethodView):
#     @jwt_required()
#     def post(self):
#         jti = get_jwt()["jti"]
#         BLOCKLIST.add(jti)
#         return {"message": "Logout realizado com sucesso."}


# @blp.route("/usuario/<int:usuario_id>")
# class usuario(MethodView):
#     @blp.response(200, PlainUsuarioSchema)
#     def get(self, usuario_id):
#         usuario = UsuarioModel.query.get_or_404(usuario_id)
#         return usuario

#     def delete(self, usuario_id):
#         usuario = UsuarioModel.query.get_or_404(usuario_id)
#         db.session.delete(usuario)
#         db.session.commit()
#         return {"message": "Usuario excluido."}, 200
    