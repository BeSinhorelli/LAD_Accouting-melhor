from peewee import *
from config import DATABASE

database = SqliteDatabase(DATABASE, pragmas={'foreign_keys': 1})

class BaseModel(Model):
    class Meta:
        database = database

class Cluster(BaseModel):
    name = CharField(unique=True)
    description = TextField()
    date_beg = DateField()
    date_end = DateField()
    status = BooleanField()

class Equipamento(BaseModel):
    cluster = ForeignKeyField(Cluster, backref='equipamentos', on_delete='cascade')
    hostname = CharField()
    modelo = CharField()
    tipo = CharField()
    patrimonio = CharField()
    serviceTag = CharField()
    nucleo = IntegerField()
    memoria = IntegerField()
    disco = IntegerField()
    date_beg = DateField()
    date_end = DateField()
    status = BooleanField()
    
class Grupo(BaseModel):
    nome = CharField(unique=True)
    demanda = IntegerField()
    unidade = CharField()
    coordenador = CharField()
    status = BooleanField()
    date_beg = DateField()
    observacoes = TextField()
    tipo = CharField()

class Usuario(BaseModel):
    grupo = ForeignKeyField(Grupo, backref='usuarios')
    nome = CharField()
    email = CharField()
    date_beg = DateField()
    date_end = DateField()
    observacoes = TextField()
    status = BooleanField()

class Producao(BaseModel):
    ano = IntegerField()
    unidade = CharField()
    cientifica = IntegerField()
    tcc = IntegerField()
    
class Relatorio(BaseModel):
    ano = IntegerField()
    mes = IntegerField()
    projeto = CharField()
    servico = CharField()
    storage_cluster = FloatField()
    storage_24x7 = FloatField()
    maquina_cluster = FloatField()
    maquina_24x7 = FloatField()