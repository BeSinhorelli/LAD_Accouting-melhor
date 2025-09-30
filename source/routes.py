from config import server, database, get_aplicacoes
from flask import g, render_template, request, redirect, url_for, flash, abort, send_file
from models import *
from datetime import datetime
from peewee import IntegrityError
import json, os, calendar
import pandas as pd
from flask import app
from werkzeug.utils import secure_filename

# --------------------------------  DEFINIÇÃO DE FUNÇÕES - FLASK --------------------------------------- #
def create_tables():
    with database:
        database.create_tables([Cluster, Equipamento, Grupo, Usuario, Producao, Relatorio, Atividade, RebootHistory, MonitoramentoRede])

def drop_tables():
    with database:
        database.drop_tables([Cluster, Equipamento, Grupo, Usuario, Producao, Relatorio, Atividade, RebootHistory, MonitoramentoRede])

def get_object_or_404(model, *expressions):
    try:
        return model.get(*expressions)
    except model.DoesNotExist:
        abort(404)

@server.before_request
def before_request():
    g.db = database
    if g.db.is_closed():
        g.db.connect()

@server.teardown_request
def teardown_request(exception):
    if not g.db.is_closed():
        g.db.close()

# -------------------------  DEFINIÇÃO DE ROTAS E DIRECIONAMENTOS - FLASK ------------------------------ #
# --- HOMEPAGE  --- #
@server.route('/', methods=['GET', 'POST'])
def homepage():
    lista_cluster = Cluster.select().order_by(Cluster.name).prefetch(Equipamento)
    lista_grupo = Grupo.select().where(Grupo.status == True).order_by(Grupo.nome)
    aplicacoes = get_aplicacoes()  

    return render_template('homepage.html', lista_cluster=lista_cluster, lista_grupo=lista_grupo, aplicacoes=aplicacoes)

# --- DASH APP  --- #
@server.route("/dash")
def dash_app():
    return app.index()

# --- CONFIGURAÇÕES DE CLUSTERS  --- #
@server.route('/cluster/<clusterName>', methods=['GET', 'POST'])
def cluster(clusterName=None):
    mensagem = None
    form = request.form

    # --- CASO SEJA CADASTRO DE CLUSTER  --- #
    if clusterName == 'cadastro':
        if request.method == 'POST':
            name = form['cluster_name']

            if name:
                if create_cluster(name, form['description']):
                    return redirect(url_for('homepage'))
                else: mensagem = 'Cluster já existe'

        return render_template('cluster.html', clusterName='cadastro', msg=mensagem)

    # --- CASO SEJA ATUALIZAÇÃO DE CLUSTER  --- #
    else:
        if clusterName:
            cluster = get_object_or_404(Cluster, Cluster.name == clusterName)

            if request.method == 'POST':
                name = form['cluster_name']
                description = form['description']
                status = form['status']

                if name:
                    if update_cluster(cluster, name, description, status):
                        return redirect(url_for('homepage'))
                    else:
                        mensagem = 'Cluster já existe'

        return render_template('cluster.html', cluster=cluster, msg=mensagem)

def create_cluster(name, description):
    try:
        with database.atomic():
            Cluster.create(
                name=name,
                description=description,
                date_beg=datetime.now().strftime('%d-%m-%Y'),
                date_end='',
                status=True
            )
        return True
    except IntegrityError:
        return False

def update_cluster(cluster, name, description, status):
    try:
        cluster.name = name
        cluster.description = description
        if status == 'desativar':
            cluster.status = False
            cluster.date_end = datetime.now().strftime('%d-%m-%Y')
        else:
            cluster.status = True
        cluster.save()
        return True
    except IntegrityError:
        return False
    
# --- EXCLUSÃO DE CLUSTER DO DB  --- #
@server.route('/cluster/delete/<int:clusterId>', methods=['POST'])
def cluster_delete(clusterId):
    cluster = Cluster.get_or_none(Cluster.id == clusterId)
    if cluster:
        cluster.delete_instance()
        flash(f'Cluster "{cluster.name}" excluído com sucesso.', 'success')
    return redirect(url_for('homepage'))

# --- LISTA DE TODOS OS CLUSTERS  --- #
@server.route('/cluster', methods=['GET'])
def lista_cluster():
    lista_cluster = Cluster.select().order_by(Cluster.name)
    return render_template('lista_cluster.html', lista_cluster=lista_cluster)

# --- CONFIGURAÇÕES DE EQUIPAMENTOS  --- #
@server.route('/cluster/<clusterName>/equipamentos')
def lista_equipamentos_cluster(clusterName):
    cluster = Cluster.get_or_none(Cluster.name == clusterName)
    if not cluster:
        abort(404)
        
    equipamentos = Equipamento.select().where(Equipamento.cluster == cluster)
    # Armazenar os equipamentos agrupados por tipo
    equipamentos_agrupados = {
        'cluster': [],
        '24x7': [],
        'collocation': [],
        'inativo': []
    }
    for equipamento in equipamentos:
        tipo = equipamento.tipo
        if tipo in equipamentos_agrupados:
            equipamentos_agrupados[tipo].append(equipamento)
            
    return render_template('lista_equipamentos.html', cluster=cluster, equipamentos_agrupados=equipamentos_agrupados)

@server.route('/equipamento/<equipName>', methods=['GET', 'POST'])
def equipamento(equipName=None):
    mensagem = None
    lista_cluster = Cluster.select().where(Cluster.status == True).order_by(Cluster.name).prefetch(Equipamento)
    form = request.form

    # --- CASO SEJA CADASTRO DE EQUIPAMENTO --- #
    if equipName == 'cadastro':
        if request.method == 'POST':

            cluster = Cluster.get(Cluster.name == form['equip_cluster_name'])
            hostname = form['hostname']

            if hostname:
                if create_equipamento(cluster, hostname, form['modelo'], form['tipo'], form['patrimonio'], form['serviceTag'], form['nucleo'], form['memoria']):
                    redirect(url_for('homepage'))
                else: mensagem = 'Equipamento já existe'

        return render_template('equipamento.html', equipName='cadastro', msg=mensagem, lista_cluster=lista_cluster)
    
    # --- CASO SEJA ATUALIZAÇÃO DE EQUIPAMENTO --- #
    else:
        if equipName:
            equipamento = get_object_or_404(Equipamento, Equipamento.hostname == equipName)
            if request.method == 'POST':

                cluster = Cluster.get(Cluster.name == request.form['equip_cluster_name'])
                hostname = form['hostname']
            
                if hostname:
                    if update_equipamento(equipamento, cluster, hostname, form['modelo'], form['tipo'], form['patrimonio'], form['serviceTag'], form['nucleo'], form['memoria'], form['status']):
                        return redirect(url_for('homepage'))
                    else: mensagem='Equipamento já existe'

        return render_template('equipamento.html', equipamento=equipamento, msg=mensagem, lista_cluster=lista_cluster)
    
def create_equipamento(cluster, hostname, modelo, tipo, patrimonio, serviceTag, nucleo, memoria):
    try:
        with database.atomic():
            Equipamento.create(
                cluster=cluster,
                hostname=hostname,
                modelo=modelo,
                tipo=tipo,
                patrimonio=patrimonio,
                serviceTag=serviceTag,
                nucleo=nucleo,
                memoria=memoria,
                disco=0,
                date_beg=datetime.now().strftime('%d-%m-%Y'),
                date_end='',
                status=True
            )
        return True
    except IntegrityError:
        return False

def update_equipamento(equipamento, cluster, hostname, modelo, tipo, patrimonio, serviceTag, nucleo, memoria, status):
    try:
        equipamento.cluster = cluster
        equipamento.hostname = hostname
        equipamento.modelo = modelo
        equipamento.tipo = tipo
        equipamento.patrimonio = patrimonio
        equipamento.serviceTag = serviceTag
        equipamento.nucleo = nucleo
        equipamento.memoria = memoria

        if status == 'desativar':
            equipamento.status = False
            equipamento.date_end=datetime.now().strftime('%d-%m-%Y')
        else:
            equipamento.status = True

        equipamento.save()
        return True
    except IntegrityError:
        return False
    
# --- EXCLUSÃO DE EQUIPAMENTO DO DB  --- #
@server.route('/equipamento/delete/<int:equipamentoId>', methods=['POST'])
def equipamento_delete(equipamentoId):
    equipamento = Equipamento.get_or_none(Equipamento.id == equipamentoId)
    if equipamento:
        equipamento.delete_instance()
        flash(f'Equipamento "{equipamento.hostname}" excluído com sucesso.', 'success')
    return redirect(url_for('homepage'))
    
# --- CONFIGURAÇÕES DE GRUPOS  --- #
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "assets", "images")
@server.route('/grupo/<groupName>', methods=['GET', 'POST'])
def grupo(groupName=None):
    mensagem = None
    form = request.form
    lista_grupo = Grupo.select().order_by(Grupo.nome)

    # --- CASO SEJA CADASTRO DE GRUPO --- #
    if groupName == 'cadastro':
        if request.method == 'POST':
            nome = form['nome']

            if nome:
                if create_grupo(nome, form['demanda'], form['unidade'], form['coordenador'], form['observacoes'], form['tipo']):
                    
                    if "logotipo" in request.files:
                        file = request.files["logotipo"]
                        if file and file.filename.lower().endswith(".png"):
                            filename = secure_filename(f"{nome}.png")
                            file.save(os.path.join(UPLOAD_FOLDER, filename))

                    return redirect(url_for('homepage'))
                else:
                    mensagem = 'Grupo já existe'

        return render_template('grupo.html', groupName='cadastro', msg=mensagem, lista_grupo=lista_grupo)

    # --- CASO SEJA ATUALIZAÇÃO DE GRUPO --- #
    else:
        if groupName:
            grupo = get_object_or_404(Grupo, Grupo.nome == groupName)

            if request.method == 'POST':
                nome = form['nome']

                if nome:
                    if update_grupo(grupo, nome, form['demanda'], form['unidade'], form['coordenador'], form['observacoes'], form['tipo'], form['status']):

                        if "logotipo" in request.files:
                            file = request.files["logotipo"]
                            if file and file.filename.lower().endswith(".png"):
                                filename = secure_filename(f"{nome}.png")
                                file.save(os.path.join(UPLOAD_FOLDER, filename))

                        return redirect(url_for('lista_grupos'))
                    else:
                        mensagem = 'Grupo já existe'

        return render_template('grupo.html', grupo=grupo, msg=mensagem, lista_grupo=lista_grupo)

def create_grupo(nome, demanda, unidade, coordenador, observacoes, tipo):
    try:
        with database.atomic():
            Grupo.create(
                nome = nome,
                demanda = demanda,
                unidade = unidade,
                coordenador = coordenador,
                observacoes = observacoes,
                tipo = tipo,
                date_beg=datetime.now().strftime('%d-%m-%Y'),
                date_end='',
                status=True
            )
        return True
    except IntegrityError:
        return False
    
def update_grupo(grupo, nome, demanda, unidade, coordenador, observacoes, tipo, status):
    try:
        grupo.nome = nome
        grupo.demanda = demanda
        grupo.unidade = unidade
        grupo.coordenador = coordenador
        grupo.observacoes = observacoes
        grupo.tipo = tipo

        if status == 'desativar':
            grupo.status = False
            grupo.date_end=datetime.now().strftime('%d-%m-%Y')
        else: grupo.status = True

        grupo.save()
        return True
    except IntegrityError:
        return False
    
# --- EXCLUSÃO DE GRUPO DO DB  E IMAGEM --- #
@server.route('/grupo/delete/<groupName>', methods=['POST'])
def grupo_delete(groupName):
    grupo = Grupo.get_or_none(Grupo.nome == groupName)
    if grupo:
        filename = secure_filename(f"{grupo.nome}.png")
        image_path = os.path.join(BASE_DIR, "assets", "images", filename)
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception as e:
                print(f"Erro ao remover imagem: {e}")
        grupo.delete_instance()
        flash(f'Grupo "{groupName}" excluído com sucesso!', 'success')
    return redirect(url_for('homepage'))
    
# --- LISTA DE TODOS OS GRUPOS  --- #
@server.route('/grupo', methods=['GET'])
def lista_grupos():
    lista_grupo = Grupo.select().order_by(Grupo.nome)
    grupo_aberto = request.args.get("grupo")
    return render_template('lista_grupos.html', lista_grupo=lista_grupo, grupo_aberto=grupo_aberto)

# --- LISTA DE USUÁRIOS POR GRUPO  --- #  
@server.route('/grupo/<groupName>/usuarios')
def lista_usuarios(groupName):
    grupo = Grupo.get_or_none(Grupo.nome == groupName)
    if not grupo:
        abort(404)
    usuarios = Usuario.select().where(Usuario.grupo == grupo).order_by(Usuario.nome.asc())
    return render_template('lista_usuarios.html', grupo=grupo, usuarios=usuarios)

# --- LISTA DAS APLICAÇÕES  --- #  
@server.route('/aplicacao', methods=['GET'])
def lista_aplicacao():
    aplicacoes = get_aplicacoes()
    return render_template("lista_aplicacao.html", aplicacoes=aplicacoes)

# --- CONFIGURAÇÕES DE USUÁRIOS  --- #
@server.route('/usuario/<userName>', methods=['GET', 'POST'])
def usuario(userName=None):
    mensagem=None
    form = request.form
    lista_grupo = Grupo.select().where(Grupo.status == True).order_by(Grupo.nome).prefetch(Usuario)
    
    # --- CASO SEJA CADASTRO DE USUÁRIO --- #
    if userName == 'cadastro':
        if request.method == 'POST':
            
            grupo = Grupo.get(Grupo.nome == request.form['group_name'])
            nome = form['nome']

            if nome:
                print("ESTOU AQUI")
                if (create_usuario(grupo, nome, form['email'], form['observacoes'])):
                    return redirect(url_for('homepage'))
                else: mensagem = 'Usuario já existe'

        return render_template('usuario.html', userName='cadastro', msg=mensagem, lista_grupo=lista_grupo)
    
    # --- CASO SEJA ATUALIZAÇÃO DE USUÁRIO --- #
    else:
        if userName:
            usuario = get_object_or_404(Usuario, Usuario.nome == userName)
            if request.method == 'POST':

                grupo = Grupo.get(Grupo.nome == form['group_name'])
                nome = form['nome']

                if nome:
                    if (update_usuario(usuario, grupo, nome, form['email'], form['observacoes'], form['status'])):
                        return redirect(url_for('homepage'))
                    else: mensagem = 'Usuario já existe'

        return render_template('usuario.html', usuario=usuario, msg=mensagem, lista_grupo=lista_grupo)

def create_usuario(grupo, nome, email, observacoes):
    try:
        with database.atomic():
            Usuario.create(
                grupo=grupo,
                nome=nome,
                email=email,
                observacoes=observacoes,
                date_beg=datetime.now().strftime('%d-%m-%Y'),
                date_end='',
                status=True
            )
        return True
    except IntegrityError:
        return False

def update_usuario(usuario, grupo, nome, email, observacoes, status):
    try:
        usuario.grupo = grupo
        usuario.nome = nome
        usuario.email = email
        usuario.observacoes = observacoes
        if status == 'desativar':
            usuario.status = False
            usuario.date_end=datetime.now().strftime('%d-%m-%Y')
        else: 
            usuario.status = True
        usuario.save()
        return True
    except IntegrityError:
        return False
    
# --- EXCLUSÃO DE USUÁRIO DO DB  --- #
@server.route('/usuario/delete/<int:userId>', methods=['POST'])
def usuario_delete(userId):
    usuario = Usuario.get_or_none(Usuario.nome == userId)
    if usuario:
        usuario.delete_instance()
        flash(f'Usuário "{usuario.nome}" excluído com sucesso.', 'success')
    return redirect(url_for('homepage'))
    
# --- CONFIGURAÇÕES DE REGISTRO DE PRODUÇÕES --- #
@server.route('/producao', methods=['GET', 'POST'])    
def registrar_producao():
    if request.method == 'POST':
        unidade = request.form['unidade']
        cientifica = int(request.form['cientifica'])
        tcc = int(request.form['tcc'])
        ano = int(request.form['ano'])

        # Salva os dados no banco de dados
        prod, created = Producao.get_or_create(
            ano=ano,
            unidade=unidade,
            defaults={'cientifica': cientifica, 'tcc': tcc}
        )
        if not created:
            prod.cientifica += cientifica
            prod.tcc += tcc
            prod.save()

        # Atualiza o export.json
        try:
            with open('export.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        producao = data.get('producao', [])
        # Atualiza ou adiciona a unidade
        for item in producao:
            if item['Unidade/Escola'] == unidade:
                item['Produção Científica'] += cientifica
                item['TCC, Dissertação ou Tese'] += tcc
                break
        else:
            producao.append({
                'Unidade/Escola': unidade,
                'Produção Científica': cientifica,
                'TCC, Dissertação ou Tese': tcc
            })
        data['producao'] = producao

        # Atualiza o campo "ultima_atualizacao" com o maior ano registrado
        anos = [ano] + [item.get('ano', ano) for item in producao if 'ano' in item]
        data['ultima_atualizacao'] = max(anos)

        with open('export.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        flash('Registro bem sucedido!')
        return redirect(url_for('registrar_producao'))
    
    # Exibir as produções
    producoes = list(Producao.select().dicts())
    if producoes:
        import pandas as pd
        df_production = pd.DataFrame(producoes)
        df_production = df_production.rename(columns={
            'unidade': 'Unidade/Escola',
            'cientifica': 'Produção Científica',
            'tcc': 'TCC, Dissertação ou Tese'
        })
        df_production = df_production.groupby('Unidade/Escola', as_index=False)[['Produção Científica', 'TCC, Dissertação ou Tese']].sum()
        total_cientifica = df_production['Produção Científica'].sum()
        total_tcc = df_production['TCC, Dissertação ou Tese'].sum()
        total_row = pd.DataFrame([{
            'Unidade/Escola': 'Total',
            'Produção Científica': total_cientifica,
            'TCC, Dissertação ou Tese': total_tcc
        }])
        df_production = pd.concat([df_production, total_row], ignore_index=True)
        producao = df_production.to_dict(orient='records')
    else:
        producao = []

    return render_template('producao.html', producao=producao, now=datetime.now)
@server.route('/producao/editar/<unidade>', methods=['GET', 'POST'])
def editar_producao(unidade):
    producao = Producao.get_or_none(Producao.unidade == unidade)
    if not producao:
        flash('Produções não encontradas.', 'danger')
        return redirect(url_for('registrar_producao'))

    if request.method == 'POST':
        producao.cientifica = int(request.form['cientifica'])
        producao.tcc = int(request.form['tcc'])
        producao.save()
        flash('Dados atualizados com sucesso!', 'success')
        return redirect(url_for('registrar_producao'))

    return render_template('editar_producao.html', producao=producao)

# --- RELATÓRIO MENSAL  --- #
@server.route('/relatorio_mensal', methods=['GET', 'POST'])
def relatorio_mensal():
    grupos = Grupo.select().where(Grupo.status == True).order_by(Grupo.nome)
    ano = int(request.form.get('ano', datetime.now().year))
    mes = int(request.form.get('mes', datetime.now().month))

    if request.method == 'POST':
        if 'xlsx_file' in request.files:
            file = request.files['xlsx_file']
            if file.filename.endswith('.xlsx'):
                #salvar o arquivo na pasta relatorios/ano
                upload_dir = f'relatorios/{ano}'
                os.makedirs(upload_dir, exist_ok=True)
                file_path = os.path.join(upload_dir, file.filename)
                file.save(file_path)
                # Ler o arquivo 
                df = pd.read_excel(file)
                df = df.replace(r'^\s*$', 0, regex=True)
                df = df.fillna(0)

                # Renomear colunas para padronizar
                df = df.rename(columns={
                    'Projeto': 'projeto',
                    'Serviço': 'servico',
                    'Storage em cluster(GB)': 'storage_cluster',
                    'Storage em 24x7(GB)': 'storage_24x7',
                    'Máquina em Cluster': 'maquina_cluster',
                    'Máquina em 24x7': 'maquina_24x7'
                })
                
                # IMPORT PARA DB
                #for _, row in df.iterrows():
                    #projeto = row['projeto']
                    #relatorio, created = Relatorio.#get_or_create(
                        #ano=ano,
                        #mes=mes,
                        #projeto=projeto,
                        #defaults={
                            #'servico': row['servico'],
                            #'storage_cluster': row['storage_cluster'],
                            #'storage_24x7': row['storage_24x7'],
                            #'maquina_cluster': row['maquina_cluster'],
                            #'maquina_24x7': row['maquina_24x7']
                        #}
                    #)
                    #if not created:
                        #relatorio.servico = row['servico']
                        #relatorio.storage_cluster = row['storage_cluster']
                        #relatorio.storage_24x7 = row['storage_24x7']
                        #relatorio.maquina_cluster = row['maquina_cluster']
                        #relatorio.maquina_24x7 = row['maquina_24x7']
                        #relatorio.save()

                flash('Relatório importado e salvo com sucesso!')
                return redirect(url_for('relatorio_mensal'))

    relatorios = {(r.projeto, r.ano, r.mes): r for r in Relatorio.select().where((Relatorio.ano == ano) & (Relatorio.mes == mes))}
    return render_template('relatorio_mensal.html', grupos=grupos, relatorios=relatorios, ano=ano, mes=mes)

# --- CONFIGURAÇÕES GERAIS  --- #
@server.route('/config', methods=['GET'])
def config():
    paradas = RebootHistory.select().order_by(RebootHistory.data_inicio.desc()).limit(3)
    return render_template('config.html', paradas=paradas, show_all=False)

@server.route('/historico_completo', methods=['GET'])
def historico_completo():
    paradas = RebootHistory.select().order_by(RebootHistory.data_inicio.desc())
    return render_template("config.html", paradas=paradas, show_all=True)

@server.route('/adicionar_registro', methods=['POST'])
def registrar_parada():
    if request.method == 'POST':
        data_inicio_str = request.form['data_inicio']
        data_fim_str = request.form['data_fim']

        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%dT%H:%M')
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%dT%H:%M')

            with database.atomic():
                RebootHistory.insert(data_inicio=data_inicio, data_fim=data_fim).execute()

            flash('Registro adicionado com sucesso!', 'success')
            return redirect(url_for('config'))
        except ValueError as e:
            flash('Formato de data inválido', 'danger')
            return redirect(url_for('config'))
        except Exception as e:
            flash(f'Erro ao registrar: {e}', 'danger')
            return redirect(url_for('config'))
    return redirect(url_for('config'))

@server.route('/editar_registro/<int:parada_id>', methods=['GET'])
def editar_parada(parada_id):
    parada = RebootHistory.get_or_none(RebootHistory.id == parada_id)
    if not parada:
        flash('Registro não encontrado', 'danger')
        return redirect(url_for('config'))
    return render_template('editar_registro.html', parada=parada)

@server.route('/atualizar_parada/<int:parada_id>', methods=['POST'])
def atualizar_parada(parada_id):
    parada = RebootHistory.get_or_none(RebootHistory.id == parada_id)
    if not parada:
        flash('Registro não encontrado', 'danger')
        return redirect(url_for('config'))

    if request.method == 'POST':
        data_inicio_str = request.form['data_inicio']
        data_fim_str = request.form['data_fim']

        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%dT%H:%M')
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%dT%H:%M')

            parada.data_inicio = data_inicio
            parada.data_fim = data_fim
            parada.save()

            flash('Registro atualizado com sucesso!', 'success')
            return redirect(url_for('config'))
        except ValueError as e:
            flash('Formato de data inválido', 'danger')
            return render_template('editar_registro.html', parada=parada)
        except Exception as e:
            flash(f'Erro ao atualizar: {e}', 'danger')
            return render_template('editar_registro.html', parada=parada)
    return render_template('editar_registro.html', parada=parada)

@server.route('/excluir_parada/<int:parada_id>', methods=['GET'])
def excluir_parada(parada_id):
    parada = RebootHistory.get_or_none(RebootHistory.id == parada_id)
    if parada:
        parada.delete_instance()
        flash('Registro excluído com sucesso!', 'success')
    else:
        flash('Registro não encontrado', 'danger')
    return redirect(url_for('config'))

@server.route('/exportar', methods=['GET'])
def exportar():

    group_list = list(Grupo.select().dicts())
    user_list = list(Usuario.select().dicts())
    equip_list = list(Equipamento.select().dicts())
    cluster_list = list(Cluster.select().dicts())
    producao_list = list(Producao.select().dicts())
    
    export = {
        'grupo': group_list,
        'usuario': user_list,
        'equipamento': equip_list,
        'cluster': cluster_list,
        'producao': producao_list,
    }

    json_data = json.dumps(export, indent=2)
    
    with open("export.json", "w") as f:
        f.write(json_data)

    return redirect(url_for('homepage')) and send_file("export.json", as_attachment = True)

@server.route('/importar', methods=['POST'])
def importar():

    # --- CRIAÇÃO DE ARQUIVO TEMPORÁRIO POIS O DIRETO RESULTA EM ERRO --- #
    file_requested = request.files['file']
    file_path = 'temp.json'
    file_requested.save(file_path)

    with open(file_path) as file:

        # --- ORGANIZAÇÃO DOS DADOS --- #
        data = json.load(file)
        groups = data['grupo']
        users = data['usuario']
        equipments = data['equipamento']
        clusters = data['cluster']

        # --- LOOPS DE CRIAÇÃO E ATUALIZAÇÃO DO BANCO DE DADOS --- #
        for group_data in groups:

            nome = group_data['nome']
            demanda = group_data['demanda']
            unidade = group_data['unidade']
            coordenador = group_data['coordenador']
            status = group_data['status']
            date_beg = group_data['date_beg']
            observacoes = group_data['observacoes']
            tipo = group_data['tipo']

            group, created = Grupo.get_or_create(
                id = group_data['id'],
                defaults = {
                    'nome': nome, 'demanda': demanda,
                    'unidade': unidade, 'coordenador': coordenador,
                    'status': status, 'date_beg': date_beg,
                    'observacoes': observacoes, 'tipo': tipo
                    }
                )

            update_grupo(group, nome, demanda, unidade, coordenador, observacoes, tipo, status)
            group.date_beg = date_beg
            group.save()

        for user_data in users:

            grupo = Grupo.get(Grupo.id == user_data['grupo'])
            nome = user_data['nome']
            email = user_data['email']
            date_beg = user_data['date_beg']
            date_end = user_data['date_end']
            observacoes = user_data['observacoes']
            status = user_data['status']


            user, created = Usuario.get_or_create(
                id = user_data['id'],
                defaults = {
                    'grupo': grupo, 'nome': nome, 'email': email,
                    'date_beg': date_beg, 'date_end': date_end,
                    'observacoes': observacoes, 'status': status
                    }
                )

            update_usuario(user, grupo, nome, email, observacoes, status)
            user.date_beg = date_beg
            user.date_end = date_end
            user.save()

        for cluster_data in clusters:

            name = cluster_data['name']
            description = cluster_data['description']
            date_beg = cluster_data['date_beg']
            date_end = cluster_data['date_end']
            status = cluster_data['status']

            cluster, created = Cluster.get_or_create(
                id = cluster_data['id'],
                defaults = {
                    'name': name, 'description': description,
                    'date_beg': date_beg, 'date_end': date_end, 'status': status
                    }
                )

            update_cluster(cluster, name, description, status)
            cluster.date_beg = date_beg
            cluster.date_end = date_end
            cluster.save()

        for equip_data in equipments:

            cluster = Cluster.get(Cluster.id == equip_data['cluster'])
            hostname = equip_data['hostname']
            modelo = equip_data['modelo']
            tipo = equip_data['tipo']
            patrimonio = equip_data['patrimonio']
            serviceTag = equip_data['serviceTag']
            nucleo = equip_data['nucleo']
            memoria = equip_data['memoria']
            disco = equip_data['disco']
            date_beg = equip_data['date_beg']
            date_end = equip_data['date_end']
            status = equip_data['status']

            equipment, created = Equipamento.get_or_create(
                id = equip_data['id'],
                defaults = {
                    'cluster': cluster, 'hostname': hostname,  'modelo': modelo,
                    'tipo': tipo, 'patrimonio': patrimonio, 'serviceTag': serviceTag,
                    'nucleo': nucleo, 'memoria': memoria, 'disco': disco,
                    'date_beg': date_beg, 'date_end': date_end, 'status': status
                    }
                )

            update_equipamento(equipment, cluster, hostname, modelo, tipo, patrimonio, serviceTag, nucleo, memoria, status)
            equipment.date_beg = equip_data['date_beg']
            equipment.date_end = equip_data['date_end']
            equipment.save()

    os.remove(file_path)
    return redirect(url_for('homepage'))

@server.route('/delete', methods=['POST'])
def delete():
    # --- DERRUBA AS TABELAS ANTIGAS E CRIA NOVAS --- #
    drop_tables()
    create_tables()
    return redirect(url_for('homepage'))