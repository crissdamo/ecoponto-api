from extensions.database import db


class ResiduoModel(db.Model):
    __tablename__ = "residuo"

    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String, nullable=False)
    icone = db.Column(db.String(256), nullable=True)
    url_midia = db.Column(db.String(256), nullable=True)
    recolhido_em_ecoponto = db.Column(db.Boolean, default=True)
    ativo = db.Column(db.Boolean, default=True)

    ecoponto = db.relationship("EcopontoModel", back_populates="residuo", secondary="ecoponto_residuo")
    categoria = db.relationship("CategoriaModel", back_populates="residuo", secondary="categoria_residuo")    
    arte_publicitaria = db.relationship("ArtePublicitariaModel", back_populates="residuo", lazy="dynamic")
    publicacao = db.relationship("PublicacaoModel", back_populates="residuo", lazy="dynamic")
