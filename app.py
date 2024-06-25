import os
import logging

from flask import Flask, jsonify
from flask_cors import CORS
from flask_smorest import Api
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from dotenv import load_dotenv

from extensions.database import db
from blocklist import BLOCKLIST


from resources.usuario import blp as UsuarioBlueprint
from resources.termo import blp as TermoBlueprint
from resources.empresa import blp as EmpresaBlueprint
from resources.ecoponto import blp as EcopontoBlueprint
from resources.categoria import blp as CategoriaBlueprint
from resources.residuo import blp as ResiduoBlueprint
from resources.publicacao import blp as PublicacaoBlueprint
from resources.arte_publicitaria import blp as ArtePublicitariaBlueprint


def create_app(db_url=None):
    app = Flask(__name__)
    load_dotenv()

    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["API_TITLE"] = "Ecoponto API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/docs/"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or os.getenv("DATABASE_URL", "sqlite:///data.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["API_SPEC_OPTIONS"] = {
        "components": {
            "securitySchemes": {
                "Bearer Auth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "Authorization",
                    "bearerFormat": "JWT",
                    "description": "Enter: **'Bearer &lt;JWT&gt;'**, where JWT is the access token",
                }
            }
        },
    }



    db.init_app(app)
    CORS(app, origins=["http://127.0.0.1:5000", "http://127.0.0.1:3000", "http://localhost:5000", "http://localhost:3000", "https://ecopontos.vercel.app", "https://ecopontos.vercel.app/"])

    migrate = Migrate(app, db)

    api = Api(app)
    app.config["JWT_SECRET_KEY"] = db_url or os.getenv("JWT_SECRET_KEY")
    jwt = JWTManager(app)




    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        return jwt_payload["jti"] in BLOCKLIST

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        
        return (
            jsonify(
                {
                    "code": 401,
                    "status": "Unauthorized",
                    "message": "Token inválido",
                }
            ),
            401,
        )
    
    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {
                    "code": 401,
                    "status": "Unauthorized",
                    "message": "Token prcisa ser atualizado",
                }
            ),
            401,
        )

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {
                    "code": 401,
                    "status": "Unauthorized",
                    "message": "Token expirou. ",
                }
            ),
            401,
        )

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return (
            jsonify(
                                {
                    "code": 401,
                    "status": "Unauthorized",
                    "message": "Falha na verificação da assinatura.",
                }
            ),
            401,
        )

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return (
            jsonify(
                {
                    "code": 401,
                    "status": "Unauthorized",
                    "message": "A solicitação não contém um token de acesso. ",
                }
            ),
            401,
        )
    



    api.register_blueprint(UsuarioBlueprint)
    api.register_blueprint(EmpresaBlueprint)
    api.register_blueprint(EcopontoBlueprint)
    api.register_blueprint(CategoriaBlueprint)
    api.register_blueprint(ResiduoBlueprint)
    api.register_blueprint(PublicacaoBlueprint)
    api.register_blueprint(ArtePublicitariaBlueprint)
    api.register_blueprint(TermoBlueprint)
    
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

        
    

    return app