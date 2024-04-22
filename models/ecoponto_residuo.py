from extensions.database import db


class EcopontoResiduoModel(db.Model):
    __tablename__ = "ecoponto_residuo"

    id = db.Column(db.Integer, primary_key=True)

    residuo_id = db.Column(db.Integer, db.ForeignKey("residuo.id"), unique=False, nullable=False)    
    ecoponto_id = db.Column(db.Integer, db.ForeignKey("ecoponto.id"), unique=False, nullable=False)
    