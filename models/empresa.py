from extensions.database import db

class EmpresaModel(db.Model):
    __tablename__ = "empresa"

    id = db.Column(db.Integer, primary_key=True)
    nome_fantasia = db.Column(db.String, unique=True, nullable=False)
    razao_social = db.Column(db.String, nullable=True)
    cnpj = db.Column(db.String, unique=True, nullable=False)
    ramo_atuacao = db.Column(db.String, nullable=True)
    telefone = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    rede_social = db.Column(db.String, nullable=True)
    participacao_outros_projetos = db.Column(db.Boolean, default=False)
    descricao_outros_projetos = db.Column(db.String, nullable=True)
    nome_contato_responsavel = db.Column(db.String, nullable=False)
    
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), unique=False, nullable=False)
    usuario = db.relationship("UsuarioModel", back_populates="empresa")
    
    ecopontos = db.relationship("EcopontoModel", back_populates="empresa", lazy="dynamic")
    aceite_termo = db.relationship("TermoAceiteModel", back_populates="empresa", lazy="dynamic")
