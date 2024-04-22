from extensions.database import db


class TermoAceiteModel(db.Model):
    __tablename__ = "aceite_termo"

    id = db.Column(db.Integer, primary_key=True)
    aceite = db.Column(db.Boolean, default=False)
    
    termo_id = db.Column(db.Integer, db.ForeignKey("termo.id"), unique=False, nullable=False)
    termo = db.relationship("TermoModel", back_populates="aceite_termo")
    
    empresa_id = db.Column(db.Integer, db.ForeignKey("empresa.id"), unique=False, nullable=False)
    empresa = db.relationship("EmpresaModel", back_populates="aceite_termo")
    