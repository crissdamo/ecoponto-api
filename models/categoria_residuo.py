from extensions.database import db


class CategoriaResiduoModel(db.Model):
    __tablename__ = "categoria_residuo"

    id = db.Column(db.Integer, primary_key=True)

    residuo_id = db.Column(db.Integer, db.ForeignKey("residuo.id"), unique=False, nullable=False)    
    categoria_id = db.Column(db.Integer, db.ForeignKey("categoria.id"), unique=False, nullable=False)
    