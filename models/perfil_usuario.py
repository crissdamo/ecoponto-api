from extensions.database import db


class PerfilUsuarioModel(db.Model):
    __tablename__ = "perfil_usuario"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(256), nullable=False)
    telefone = db.Column(db.String(15), nullable=True)
    email = db.Column(db.String(256), nullable=True)

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), unique=True, nullable=False)
    usuario = db.relationship("UsuarioModel", back_populates="perfil_usuario")
    
