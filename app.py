import os, sqlite3, json

from unicodedata import name
from datetime import datetime

from flask import Flask, template_rendered
from flask import g, request, send_file
from flask import url_for, abort, render_template, flash, redirect

from peewee import *
from playhouse.shortcuts import model_to_dict, dict_to_model
from playhouse.reflection import generate_models, print_model, print_table_sql

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
    #no_break = CharField() 
    #status_no_break = BooleanField() 
    #tipo = CharField() 
    
class Grupo(BaseModel):
    nome = CharField()
    demanda = IntegerField()
    unidade = CharField()
    coordenador = CharField()
    status = BooleanField()
    date_beg = DateField()
    #date_end = DateField()
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
    #quota = ForeignKeyField(Quota, backref='quotas')

##########################################################################################

def create_tables():
    with database:
        database.create_tables([Cluster, Equipamento, Grupo, Usuario])

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
    lista_grupo = Grupo.select().order_by(Grupo.nome).prefetch(Usuario)

    #if request.method == 'POST':
    #    if request.form['desativar']:
    #        with database.atomic():
                #Cluster.delete().where(Cluster.name == request.form['desativar']).execute()
    #            Cluster.update(status=False).where(Cluster.name == request.form['desativar']).execute()
    #        lista_cluster = Cluster.select().order_by(Cluster.name).prefetch(Equipamento)
    #        print(request.form['desativar'])
    #        return object_list('homepage.html', lista_cluster, 'lista_cluster')

    return render_template('homepage.html', lista_cluster=lista_cluster, lista_grupo=lista_grupo)


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
                        date_beg=datetime.now().strftime('%d-%m-%Y'),
                        date_end='',
                        status=True
                    )
                return redirect(url_for('homepage'))
            except IntegrityError:
                msg='Cluster já existe'
        return render_template('cluster.html', clusterName='cadastro', msg=msg)
    else:
        if clusterName:
            cluster = get_object_or_404(Cluster, Cluster.name == clusterName)
            if request.method == 'POST' and request.form['cluster_name']:
                try:
                    cluster.name=request.form['cluster_name']
                    cluster.description=request.form['description']
                    if request.form['status'] == 'desativar':
                        cluster.status = False
                        cluster.date_end=datetime.now().strftime('%d-%m-%Y')
                    else:
                        cluster.status = True
                    cluster.save()
                    return redirect(url_for('homepage'))
                except IntegrityError:
                    msg='Cluster já existe'
        return render_template('cluster.html', cluster=cluster, msg=msg)


@app.route('/equipamento/<equipName>', methods=['GET', 'POST'])
def equipamento(equipName=None):
    msg=None
    lista_cluster = Cluster.select().where(Cluster.status == True).order_by(Cluster.name).prefetch(Equipamento)
    if equipName == 'cadastro':
        if request.method == 'POST' and request.form['hostname']:
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
                        date_beg=datetime.now().strftime('%d-%m-%Y'),
                        date_end='',
                        status=True
                    )
                return redirect(url_for('homepage'))
            except IntegrityError:
                msg='Equipamento já existe'
        return render_template('equipamento.html', equipName='cadastro', msg=msg, lista_cluster=lista_cluster)
    else:
        if equipName:
            equipamento = get_object_or_404(Equipamento, Equipamento.hostname == equipName)
            #print(equipamento)
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
                    if request.form['status'] == 'desativar':
                        equipamento.status = False
                        equipamento.date_end=datetime.now().strftime('%d-%m-%Y')
                    else:
                        equipamento.status = True
                    equipamento.save()
                    return redirect(url_for('homepage'))
                except IntegrityError:
                    msg='Equipamento já existe'
        return render_template('equipamento.html', equipamento=equipamento, msg=msg, lista_cluster=lista_cluster)


@app.route('/grupo/<groupName>', methods=['GET', 'POST'])
def grupo(groupName=None):
    msg=None
    lista_grupo = Grupo.select().order_by(Grupo.nome)
    if groupName == 'cadastro':
        print('cadastro')
        if request.method == 'POST' and request.form['nome']:
            try:
                with database.atomic():
                    print('grupo')
                    Grupo.create(
                        nome=request.form['nome'],
                        demanda=request.form['demanda'],
                        unidade=request.form['unidade'],
                        coordenador=request.form['coordenador'],
                        observacoes=request.form['observacoes'],
                        tipo=request.form['tipo'],
                        date_beg=datetime.now().strftime('%d-%m-%Y'),
                        date_end='',
                        status=True
                    )
                return redirect(url_for('homepage'))
            except IntegrityError:
                msg='Grupo já existe'
        return render_template('grupo.html', groupName='cadastro', msg=msg, lista_grupo=lista_grupo)
    else:
        if groupName:
            grupo = get_object_or_404(Grupo, Grupo.nome == groupName)
            if request.method == 'POST' and request.form['nome']:
                try:
                    grupo.nome=request.form['nome']
                    grupo.demanda=request.form['demanda']
                    grupo.unidade=request.form['unidade']
                    grupo.coordenador=request.form['coordenador']
                    grupo.observacoes=request.form['observacoes']
                    grupo.tipo=request.form['tipo']
                    if request.form['status'] == 'desativar':
                        grupo.status = False
                        grupo.date_end=datetime.now().strftime('%d-%m-%Y')
                    else:
                        grupo.status = True
                    grupo.save()
                    return redirect(url_for('homepage'))
                except IntegrityError:
                    msg='Grupo já existe'
        return render_template('grupo.html', grupo=grupo, msg=msg, lista_grupo=lista_grupo)


@app.route('/usuario/<userName>', methods=['GET', 'POST'])
def usuario(userName=None):
    msg=None
    lista_grupo = Grupo.select().where(Grupo.status == True).order_by(Grupo.nome).prefetch(Usuario)
    if userName == 'cadastro':
        if request.method == 'POST' and request.form['nome']:
            try:
                with database.atomic():
                    Usuario.create(
                        grupo = Grupo.get(Grupo.nome == request.form['group_name']),
                        nome=request.form['nome'],
                        email=request.form['email'],
                        observacoes=request.form['observacoes'],
                        date_beg=datetime.now().strftime('%d-%m-%Y'),
                        date_end='',
                        status=True
                    )
                return redirect(url_for('homepage'))
            except IntegrityError:
                msg='Usuario já existe'
        return render_template('usuario.html', userName='cadastro', msg=msg, lista_grupo=lista_grupo)
    else:
        if userName:
            usuario = get_object_or_404(Usuario, Usuario.nome == userName)
            if request.method == 'POST' and request.form['nome']:
                try:
                    usuario.grupo=Grupo.get(Grupo.nome == request.form['group_name'])
                    usuario.nome=request.form['nome']
                    usuario.email=request.form['email']
                    usuario.observacoes=request.form['observacoes']
                    if request.form['status'] == 'desativar':
                        usuario.status = False
                        usuario.date_end=datetime.now().strftime('%d-%m-%Y')
                    else:
                        usuario.status = True
                    usuario.save()
                    return redirect(url_for('homepage'))
                except IntegrityError:
                    msg='Usuario já existe'
        return render_template('usuario.html', usuario=usuario, msg=msg, lista_grupo=lista_grupo)

@app.route('/export', methods=['GET'])
def export():

    lista_grupo = [grupo for grupo in Grupo.select().dicts()]
    lista_usuario = [usuario for usuario in Usuario.select().dicts()]
    lista_equipamento = [equipamento for equipamento in Equipamento.select().dicts()]
    lista_cluster = [cluster for cluster in Cluster.select().dicts()]
    
    listageral = {}

    listageral['grupo']=lista_grupo
    listageral['usuario']=lista_usuario
    listageral['equipamento']=lista_equipamento
    listageral['cluster']=lista_cluster
    json_data = json.dumps(listageral, indent=2)
    
    f = open("listageral.json", "w")
    f.write(str(json_data))
    f.close()

    return redirect(url_for('homepage')) and send_file("listageral.json", as_attachment = True)

@app.route('/upload', methods=['GET'])
def upload ():
    return render_template('upload.html')

@app.route('/import_json', methods=['POST'])
def import_json():

    file_requested = request.files['file']
    file_path = 'temp.json'
    file_requested.save(file_path)

    database.create_tables([Cluster, Equipamento, Grupo, Usuario])

    with open(file_path) as file:

        data = json.load(file)

        grupos = data['grupo']
        usuarios = data['usuario']
        equipamentos = data['equipamento']
        clusters = data['cluster']

        for dados_grupo in grupos:

            Grupo.create(
                nome=dados_grupo['nome'],
                demanda=dados_grupo['demanda'],
                unidade=dados_grupo['unidade'],
                coordenador=dados_grupo['coordenador'],
                status=dados_grupo['status'],
                date_beg=dados_grupo['date_beg'],
                observacoes=dados_grupo['observacoes'],
                tipo=dados_grupo['tipo']
            )

        for dados_usuario in usuarios:

            grupo_id = dados_usuario['grupo']
            grupo = Grupo.get(Grupo.id == grupo_id)

            Usuario.create(
                grupo=grupo,
                nome=dados_usuario['nome'],
                email=dados_usuario['email'],
                date_beg=dados_usuario['date_beg'],
                date_end=dados_usuario['date_end'],
                observacoes=dados_usuario['observacoes'],
                status=dados_usuario['status']
            )
    
        for cluster_data in clusters:

            Cluster.create(
                name=cluster_data['name'],
                description=cluster_data['description'],
                date_beg=cluster_data['date_beg'],
                date_end=cluster_data['date_end'],
                status=cluster_data['status']
            )

        for dados_equipamentos in equipamentos:
            cluster_id = dados_equipamentos['cluster']
            cluster = Cluster.get(Cluster.id == cluster_id)

            Equipamento.create(
                cluster=cluster,
                hostname=dados_equipamentos['hostname'],
                modelo=dados_equipamentos['modelo'],
                tipo=dados_equipamentos['tipo'],
                patrimonio=dados_equipamentos['patrimonio'],
                serviceTag=dados_equipamentos['serviceTag'],
                nucleo=dados_equipamentos['nucleo'],
                memoria=dados_equipamentos['memoria'],
                disco=dados_equipamentos['disco'],
                date_beg=dados_equipamentos['date_beg'],
                date_end=dados_equipamentos['date_end'],
                status=dados_equipamentos['status']
            )

    os.remove(file_path)
    return redirect(url_for('homepage'))


##########################################################################################

# É possível LIMPAR o banco de dados 'descomentando' o seguinte comando:
# database.drop_tables([Cluster, Equipamento, Grupo, Usuario])

##########################################################################################

if __name__ == '__main__':
    create_tables()
    app.run()
