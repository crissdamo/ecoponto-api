from datetime import datetime, timedelta
from extensions.database import db

class SecaoPublicacaoModel(db.Model):
    __tablename__ = "secao_publicacao"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(256), nullable=False)
    descricao = db.Column(db.String, nullable=False)
    url_media = db.Column(db.String, nullable=True)
    data_inicio = db.Column(db.Date, default=datetime.now().date())
    data_final = db.Column(db.Date, default=(datetime.now() + timedelta(days=12000)).date())
    ativo = db.Column(db.Boolean, default=True)
    
    publicacao_id = db.Column(db.Integer, db.ForeignKey("publicacao.id"), unique=False, nullable=False)
    publicacao = db.relationship("PublicacaoModel", back_populates="secao_publicacao")
