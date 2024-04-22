from extensions.database import db

from sqlalchemy import Enum

from models.enums.dia_semana import DiasSemanaEnum

class DiaFuncionamentoModel(db.Model):
    __tablename__ = "dia_funcionamento"

    id = db.Column(db.Integer, primary_key=True)
    dia_semana = db.Column(Enum(DiasSemanaEnum))

    hora_inicial = db.Column(db.Time)
    hora_final = db.Column(db.Time)
    
    ecoponto_id = db.Column(db.Integer, db.ForeignKey("ecoponto.id"), unique=False, nullable=False)
    ecoponto = db.relationship("EcopontoModel", back_populates="dia_funcionamento")
    