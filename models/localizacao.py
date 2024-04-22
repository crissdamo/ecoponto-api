from extensions.database import db

class LocalizacaoModel(db.Model):
    __tablename__ = "localizacao"

    id = db.Column(db.Integer, primary_key=True)
    rua = db.Column(db.String(256), nullable=False)
    numero = db.Column(db.String(10), nullable=False)
    bairro = db.Column(db.String(256), nullable=False)
    cep = db.Column(db.String(10), nullable=False)
    cidade = db.Column(db.String(256), nullable=False)
    estado = db.Column(db.String(256), nullable=False)
    complemento = db.Column(db.String(256), nullable=True)
    latitude = db.Column(db.String(256), nullable=False)
    longitude = db.Column(db.String(256), nullable=False)
    url_localizacao = db.Column(db.String(256), nullable=True)
    
    ecoponto_id = db.Column(db.Integer, db.ForeignKey("ecoponto.id"), unique=True, nullable=False)
    ecoponto = db.relationship("EcopontoModel", back_populates="localizacao")
    