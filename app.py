from unicodedata import name
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

database = SqliteDatabase(DATABASE, pragmas={'foreign_keys': 1})

##########################################################################################

class BaseModel(Model):
    class Meta:
        database = database

class Cluster(BaseModel):
    name = CharField(unique=True)
    num = IntegerField()
    description = TextField()
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
    status = BooleanField()
    #no_break = CharField() 
    #status_no_break = BooleanField() 
    #tipo = CharField() 
    
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

@app.route('/', methods=['GET', 'POST'])
def homepage():
    lista_cluster = Cluster.select().order_by(Cluster.name).prefetch(Equipamento)

    if request.method == 'POST':
        if request.form['desativar']:
            with database.atomic():
                Cluster.delete().where(Cluster.name == request.form['desativar']).execute()
            lista_cluster = Cluster.select().order_by(Cluster.name).prefetch(Equipamento)
            print(request.form['desativar'])
            return object_list('homepage.html', lista_cluster, 'lista_cluster')

    return object_list('homepage.html', lista_cluster, 'lista_cluster')


@app.route('/cluster/<clusterName>', methods=['GET', 'POST'])
def cluster(clusterName=None):
    msg=None
    if clusterName == 'cadastro':
        if request.method == 'POST' and request.form['cluster_name']:
            try:
                with database.atomic():
                    Cluster.create(
                        name=request.form['cluster_name'],
                        description=request.form['description'],
                        num = request.form['num-teste'],
                        status=True
                    )
                return redirect(url_for('homepage'))
            except IntegrityError:
                msg='Cluster já existe'
        return render_template('cluster.html', clusterName='cadastro', msg=msg)
    else:
        if clusterName:
            cluster = get_object_or_404(Cluster, Cluster.name == clusterName)
            print(cluster)
            if request.method == 'POST' and request.form['cluster_name']:
                try:
                    cluster.name = request.form['cluster_name']
                    cluster.description = request.form['description']
                    cluster.num = request.form['num-teste']
                    print(cluster.name)
                    print(cluster.description)
                    print(cluster.num)
                    cluster.save()
                    return redirect(url_for('homepage'))
                except IntegrityError:
                    msg='Cluster já existe'
        #return object_list('form.html', cluster=cluster)
        return render_template('cluster.html', cluster=cluster, msg=msg)


@app.route('/equipamento/<equipName>', methods=['GET', 'POST'])
def equipamento(equipName=None):
    msg=None
    lista_cluster = Cluster.select().order_by(Cluster.name).prefetch(Equipamento)
    if equipName == 'cadastro':
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
                        disco=0,
                        status=True
                    )
                return redirect(url_for('homepage'))
            except IntegrityError:
                msg='Equipamento já existe'
        return render_template('equipamento.html', equipName='cadastro', msg=msg, lista_cluster=lista_cluster)
    else:
        if equipName:
            equipamento = get_object_or_404(Equipamento, Equipamento.hostname == equipName)
            print(equipamento)
            if request.method == 'POST' and request.form['hostname']:
                try:
                    equipamento.cluster=Cluster.get(Cluster.name == request.form['equip_cluster_name'])
                    equipamento.hostname=request.form['hostname']
                    equipamento.modelo=request.form['modelo']
                    equipamento.tipo=request.form['tipo']
                    equipamento.patrimonio=request.form['patrimonio']
                    equipamento.serviceTag=request.form['serviceTag']
                    equipamento.nucleo=request.form['nucleo']
                    equipamento.memoria=request.form['memoria']
                    equipamento.disco=0
                    equipamento.status=True
                    equipamento.save()
                    return redirect(url_for('homepage'))
                except IntegrityError:
                    msg='Equipamento já existe'
        return render_template('equipamento.html', equipamento=equipamento, msg=msg, lista_cluster=lista_cluster)

##########################################################################################

#database.drop_tables([Cluster, Equipamento])

##########################################################################################

if __name__ == '__main__':
    create_tables()
    app.run()
