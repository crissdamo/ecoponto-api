from datetime import datetime, timedelta
from extensions.database import db


class ArtePublicitariaModel(db.Model):
    __tablename__ = "arte_publicitaria"

    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String, nullable=False)
    url_midia = db.Column(db.String(256), nullable=False)
    disponibilizar_ecoponto = db.Column(db.Boolean, default=True)
    data_inicio = db.Column(db.Date, default=datetime.now().date())
    data_final = db.Column(db.Date, default=(datetime.now() + timedelta(days=12000)).date())
    ativo = db.Column(db.Boolean, default=True)

    residuo_id = db.Column(db.Integer, db.ForeignKey("residuo.id"), unique=False, nullable=True)
    residuo = db.relationship("ResiduoModel", back_populates="arte_publicitaria")
