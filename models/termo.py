from extensions.database import db


class TermoModel(db.Model):
    __tablename__ = "termo"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(256), nullable=False)
    descricao = db.Column(db.String, nullable=False)
    ativo = db.Column(db.Boolean, default=True)

    aceite_termo = db.relationship("TermoAceiteModel", back_populates="termo", lazy="dynamic")
    