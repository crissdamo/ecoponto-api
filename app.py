import os
import logging

from flask import Flask
from flask_smorest import Api
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from dotenv import load_dotenv

from extensions.database import db
import models


from resources.usuario import blp as UsuarioBlueprint
from resources.termo import blp as TermoBlueprint
from resources.empresa import blp as EmpresaBlueprint
from resources.ecoponto import blp as EcopontoBlueprint
from resources.categoria import blp as CategoriaBlueprint
from resources.residuo import blp as ResiduoBlueprint


def create_app(db_url=None):
    app = Flask(__name__)
    load_dotenv()

    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["API_TITLE"] = "Ecoponto API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/docs"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or os.getenv("DATABASE_URL", "sqlite:///data.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
   

    db.init_app(app)
    migrate = Migrate(app, db)

    api = Api(app)
    app.config["JWT_SECRET_KEY"] = "fkc7OxB243axPAtwn8PV3tlFRemHvjwGs2ECMTMbQQuNNwSi"
    jwt = JWTManager(app)

    # api.register_blueprint(UsuarioBlueprint)
    api.register_blueprint(EmpresaBlueprint)
    api.register_blueprint(TermoBlueprint)
    api.register_blueprint(EcopontoBlueprint)
    api.register_blueprint(CategoriaBlueprint)
    api.register_blueprint(ResiduoBlueprint)

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

        
    # with app.app_context():
    #     db.create_all()
    
    return app