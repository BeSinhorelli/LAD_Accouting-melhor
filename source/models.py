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

class Conta(BaseModel):
    id_usuario = ForeignKeyField(Usuario, backref='conta', unique=True, on_delete='cascade')
    nome_conta = CharField(unique=True)

"""class Job(BaseModel):
    id_job = CharField(unique=True) 
    id_conta = ForeignKeyField(Conta, backref='jobs')
    user = CharField() 
    account = CharField() 
    cpu_hours = FloatField()  
    elapsed_hours = FloatField()  
    start_time = DateTimeField() 
    end_time = DateTimeField() 
    job_state = CharField() 
    cluster = CharField()  
    mes_referencia = CharField()
    #job_name = CharField() #JobName
    #node_list = CharField() #NodeList
    #exit_code = CharField() #ExitCode
    #submit_time = DateTimeField() #Submit/SubmitLine
    #node_count = IntegerField() #NodeList?
    #partition = CharField() #Partition
    #time_limit = CharField() #Timelimit
    #work_dir = CharField() #WorkDir
    """

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

class Atividade(BaseModel):
    data = DateTimeField()
    uptime = CharField()

class RebootHistory(BaseModel):
    data_inicio = DateTimeField()
    data_fim = DateTimeField()

class MonitoramentoRede(BaseModel):
    timestamp = DateTimeField()
    latency = FloatField(null=True)
    packet_loss = FloatField(null=True)
    status = CharField()