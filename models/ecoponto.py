from datetime import datetime, timedelta
from extensions.database import db
from sqlalchemy import Enum

from models.enums.situacao_ecoponto import SituacaoEnum

class EcopontoModel(db.Model):
    __tablename__ = "ecoponto"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String, nullable=False)
    aberto_publico = db.Column(db.Boolean, default=True)
    situacao = db.Column(Enum(SituacaoEnum))
    data_inicio = db.Column(db.Date, default=datetime.now().date)
    data_final = db.Column(db.Date, default=lambda: (datetime.now() + timedelta(days=365*12)).date())
    ativo = db.Column(db.Boolean, default=True)
    
    empresa_id = db.Column(db.Integer, db.ForeignKey("empresa.id"), unique=False, nullable=False)
    empresa = db.relationship("EmpresaModel", back_populates="ecopontos")
    
    dia_funcionamento = db.relationship("DiaFuncionamentoModel", back_populates="ecoponto", lazy="dynamic")
    localizacao = db.relationship("LocalizacaoModel", back_populates="ecoponto")
    residuo = db.relationship("ResiduoModel", back_populates="ecoponto", secondary="ecoponto_residuo")
    