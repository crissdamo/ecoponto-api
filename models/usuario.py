from extensions.database import db


class UsuarioModel(db.Model):
    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    senha = db.Column(db.String(256), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    admin = db.Column(db.Boolean, default=False)
    equipe = db.Column(db.Boolean, default=False)
    sistema = db.Column(db.Boolean, default=False)
    
    empresa = db.relationship("EmpresaModel", back_populates="usuario", lazy="dynamic")
    perfil_usuario = db.relationship("PerfilUsuarioModel", back_populates="usuario", lazy="dynamic")
    
    