from extensions.database import db


class CategoriaModel(db.Model):
    __tablename__ = "categoria"

    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String, nullable=False)
    icone = db.Column(db.String(256), nullable=True)
    url_midia = db.Column(db.String(256), nullable=True)
    ativo = db.Column(db.Boolean, default=True)

    residuo = db.relationship("ResiduoModel", back_populates="categoria", secondary="categoria_residuo")    
    publicacao = db.relationship("PublicacaoModel", back_populates="categoria", lazy="dynamic")
