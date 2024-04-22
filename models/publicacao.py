from datetime import datetime, timedelta
from extensions.database import db

class PublicacaoModel(db.Model):
    __tablename__ = "publicacao"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(256), nullable=False)
    descricao = db.Column(db.String, nullable=False)
    url_media = db.Column(db.String, nullable=True)
    data_inicio = db.Column(db.Date, default=datetime.now().date())
    data_final = db.Column(db.Date, default=(datetime.now() + timedelta(days=12000)).date())
    ativo = db.Column(db.Boolean, default=True)

    categoria_id = db.Column(db.Integer, db.ForeignKey("categoria.id"), unique=False, nullable=True)
    categoria = db.relationship("CategoriaModel", back_populates="publicacao")
   
    residuo_id = db.Column(db.Integer, db.ForeignKey("residuo.id"), unique=False, nullable=True)
    residuo = db.relationship("ResiduoModel", back_populates="publicacao")
    
    secao_publicacao = db.relationship("SecaoPublicacaoModel", back_populates="publicacao", lazy="dynamic")

