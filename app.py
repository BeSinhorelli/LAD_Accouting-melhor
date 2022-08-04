from flask import Flask, template_rendered
from flask import g, request
from flask import url_for, abort, render_template, flash, redirect
from peewee import *

##########################################################################################

DATABASE = 'accounting.db'
DEBUG = True
SECRET_KEY = 'hin6bab8ge25*r=x&amp;+5$0kn=-#log$pt^#@vrqjld!^2ci@g*b'

app = Flask(__name__)
app.config.from_object(__name__)

database = SqliteDatabase(DATABASE)

##########################################################################################

class BaseModel(Model):
    class Meta:
        database = database

class Cluster(BaseModel):
    name = CharField()
    description = TextField()

class Equipamento(BaseModel):
    cluster = ForeignKeyField(Cluster, backref='equipamentos', on_delete='CASCADE')
    hostname = CharField()
    modelo = CharField()
    tipo = CharField()
    patrimonio = CharField()
    serviceTag = CharField()
    #no_break = CharField() 
    #status = CharField() 
    #tipo2 = CharField() 
    nucleo = IntegerField()
    memoria = IntegerField()
    disco = IntegerField() 
    
class Grupo(BaseModel):
    demanda = IntegerField()
    unidade = CharField()
    coordenador = CharField()
    status = CharField()
    data = DateField()
    tipo = CharField()
    observacoes = TextField()

class Usuario(BaseModel):
    grupo = ForeignKeyField(Grupo, backref='usuarios')
    nome = CharField()
    email = CharField()
    quota = IntegerField()

##########################################################################################

def create_tables():
    with database:
        database.create_tables([Cluster, Equipamento])

def get_object_or_404(model, *expressions):
    try:
        return model.get(*expressions)
    except model.DoesNotExist:
        abort(404)

def object_list(template_name, qr, var_name='object_list', **kwargs):
    kwargs[var_name] = qr
    return render_template(template_name, **kwargs)

@app.before_request
def before_request():
    g.db = database
    g.db.connect()

@app.after_request
def after_request(response):
    g.db.close()
    return response

##########################################################################################

@app.route('/')
def homepage():
    lista_cluster = Cluster.select().order_by(Cluster.name).prefetch(Equipamento)
    for cluster in lista_cluster:
        print(cluster.name)
        for equipamento in cluster.equipamentos:
            print('   - ', equipamento.hostname)
    return object_list('homepage.html', lista_cluster, 'lista_cluster')


@app.route('/cadastroCluster/', methods=['GET', 'POST'])
def cadastroCluster():
    if request.method == 'POST' and request.form['cluster_name']:
        try:
            with database.atomic():
                Cluster.create(
                    name=request.form['cluster_name'],
                    description=request.form['description']
                )
            return redirect(url_for('homepage'))
        except IntegrityError:
            flash('Cluster já existe')
    return render_template('cadastroCluster.html')


@app.route('/cadastroEquipamento/', methods=['GET', 'POST'])
def cadastroEquipamento():
    if request.method == 'POST' and request.form['equip_cluster_name']:
        try:
            with database.atomic():
                Equipamento.create(
                    cluster=Cluster.get(Cluster.name == request.form['equip_cluster_name']),
                    hostname=request.form['hostname'],
                    modelo=request.form['modelo'],
                    tipo=request.form['tipo'],
                    patrimonio=request.form['patrimonio'],
                    serviceTag=request.form['serviceTag'],
                    nucleo=request.form['nucleo'],
                    memoria=request.form['memoria'],
                    disco=0
                )
            return redirect(url_for('homepage'))
        except IntegrityError:
            flash('Equipamento já existe')
    lista = Cluster.select().order_by(Cluster.name).prefetch(Equipamento)
    return object_list('cadastroEquipamento.html', lista, 'lista_cluster')


##########################################################################################

#database.drop_tables([Cluster, Equipamento])

##########################################################################################

if __name__ == '__main__':
    create_tables()
    app.run()