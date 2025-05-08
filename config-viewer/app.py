#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Aplicação web para visualizar as configurações armazenadas no PostgreSQL.

Esta aplicação permite:
1. Listar todas as configurações
2. Visualizar uma configuração específica
3. Verificar a seção enabled_collections
4. Visualizar o mapeamento Chatwoot
"""

import os
import yaml
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from markupsafe import Markup
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from dotenv import load_dotenv
import logging
from pygments import highlight
from pygments.lexers import JsonLexer, YamlLexer
from pygments.formatters import HtmlFormatter

# Configurar logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config-service", "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "config_viewer.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("config-viewer")
logger.info("Iniciando visualizador de configurações...")

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do banco de dados
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5433")
DB_NAME = os.getenv("DB_NAME", "config_service")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# Funções para formatação de código
def format_json(json_str):
    """Formata JSON com destaque de sintaxe."""
    formatted = highlight(json_str, JsonLexer(), HtmlFormatter(style='colorful'))
    return Markup(formatted)

def format_yaml(yaml_str):
    """Formata YAML com destaque de sintaxe."""
    formatted = highlight(yaml_str, YamlLexer(), HtmlFormatter(style='colorful'))
    return Markup(formatted)

# Criar aplicação Flask
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret_key")

# Adicionar funções de formatação aos templates
app.jinja_env.globals.update(format_json=format_json, format_yaml=format_yaml)

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Modelo de usuário simples
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Usuários hardcoded para demonstração
# Em produção, isso deve ser armazenado em um banco de dados
# Senha forte gerada aleatoriamente
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Config@Viewer2025!")
users = {
    "admin": User(1, "admin", generate_password_hash(ADMIN_PASSWORD))
}

@login_manager.user_loader
def load_user(user_id):
    for user in users.values():
        if user.id == int(user_id):
            return user
    return None

def connect_to_db():
    """Conecta ao banco de dados PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            cursor_factory=RealDictCursor
        )
        logger.info("Conexão com o banco de dados estabelecida com sucesso!")
        return conn
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco de dados: {str(e)}")
        return None

def get_all_configs(tenant_id=None, domain=None, config_type=None):
    """Obtém todas as configurações, com filtros opcionais."""
    conn = connect_to_db()
    if not conn:
        return []

    try:
        cursor = conn.cursor()

        query = """
            SELECT tenant_id, domain, config_type, version, created_at
            FROM crew_configurations
            WHERE 1=1
        """
        params = []

        if tenant_id:
            query += " AND tenant_id LIKE %s"
            params.append(f"%{tenant_id}%")

        if domain:
            query += " AND domain LIKE %s"
            params.append(f"%{domain}%")

        if config_type:
            query += " AND config_type = %s"
            params.append(config_type)

        query += " ORDER BY tenant_id, domain, config_type, version DESC"

        cursor.execute(query, params)

        configs = cursor.fetchall()
        cursor.close()
        return configs
    except Exception as e:
        logger.error(f"Erro ao obter configurações: {str(e)}")
        return []
    finally:
        conn.close()

def get_config(tenant_id, domain, config_type, version=None):
    """Obtém uma configuração específica."""
    conn = connect_to_db()
    if not conn:
        return None

    try:
        cursor = conn.cursor()

        if version:
            cursor.execute("""
                SELECT id, tenant_id, domain, config_type, version, yaml_content, json_data, created_at, updated_at
                FROM crew_configurations
                WHERE tenant_id = %s AND domain = %s AND config_type = %s AND version = %s
            """, (tenant_id, domain, config_type, version))
        else:
            cursor.execute("""
                SELECT id, tenant_id, domain, config_type, version, yaml_content, json_data, created_at, updated_at
                FROM crew_configurations
                WHERE tenant_id = %s AND domain = %s AND config_type = %s
                ORDER BY version DESC
                LIMIT 1
            """, (tenant_id, domain, config_type))

        config = cursor.fetchone()
        cursor.close()
        return config
    except Exception as e:
        logger.error(f"Erro ao obter configuração: {str(e)}")
        return None
    finally:
        conn.close()

def get_config_versions(tenant_id, domain, config_type):
    """Obtém todas as versões de uma configuração."""
    conn = connect_to_db()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT version, created_at
            FROM crew_configurations
            WHERE tenant_id = %s AND domain = %s AND config_type = %s
            ORDER BY version DESC
        """, (tenant_id, domain, config_type))

        versions = cursor.fetchall()
        cursor.close()
        return versions
    except Exception as e:
        logger.error(f"Erro ao obter versões: {str(e)}")
        return []
    finally:
        conn.close()

def get_mapping():
    """Obtém o mapeamento Chatwoot."""
    conn = connect_to_db()
    if not conn:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, version, mapping_data, created_at, updated_at
            FROM chatwoot_mapping
            ORDER BY version DESC
            LIMIT 1
        """)

        mapping = cursor.fetchone()
        cursor.close()
        return mapping
    except Exception as e:
        logger.error(f"Erro ao obter mapeamento: {str(e)}")
        return None
    finally:
        conn.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Verificar se o usuário existe
        if not username or username not in users:
            flash('Usuário não encontrado!', 'danger')
            logger.warning(f"Tentativa de login com usuário inexistente: {username}")
            return render_template('login.html')

        # Verificar se a senha está correta
        if not users[username].check_password(password):
            flash('Senha incorreta!', 'danger')
            logger.warning(f"Tentativa de login com senha incorreta para o usuário: {username}")
            return render_template('login.html')

        # Login bem-sucedido
        login_user(users[username])
        flash('Login realizado com sucesso!', 'success')
        logger.info(f"Login bem-sucedido para o usuário: {username}")

        next_page = request.args.get('next')
        return redirect(next_page or url_for('index'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout do usuário."""
    logout_user()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Página inicial com busca de configurações."""
    tenant_id = request.args.get('tenant_id')
    domain = request.args.get('domain')
    config_type = request.args.get('config_type')

    configs = get_all_configs(tenant_id, domain, config_type)
    return render_template('index.html', configs=configs)

@app.route('/config/<tenant_id>/<domain>/<config_type>')
@login_required
def view_config(tenant_id, domain, config_type):
    """Visualiza uma configuração específica."""
    version = request.args.get('version')
    config = get_config(tenant_id, domain, config_type, version)
    versions = get_config_versions(tenant_id, domain, config_type)

    if not config:
        return render_template('error.html', message=f"Configuração não encontrada: {tenant_id}/{domain}/{config_type}")

    # Formatar JSON para exibição
    json_formatted = json.dumps(config['json_data'], indent=2, ensure_ascii=False)

    return render_template(
        'config.html',
        config=config,
        versions=versions,
        json_formatted=json_formatted,
        tenant_id=tenant_id,
        domain=domain,
        config_type=config_type
    )

@app.route('/enabled_collections')
@login_required
def view_enabled_collections():
    """Visualiza a seção enabled_collections de todas as configurações."""
    configs = []
    conn = connect_to_db()
    if not conn:
        return render_template('error.html', message="Erro ao conectar ao banco de dados")

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tenant_id, domain, json_data->'enabled_collections' as enabled_collections, version
            FROM crew_configurations
            WHERE config_type = 'config'
            ORDER BY tenant_id, domain, version DESC
        """)

        configs = cursor.fetchall()
        cursor.close()
    except Exception as e:
        logger.error(f"Erro ao obter coleções habilitadas: {str(e)}")
        return render_template('error.html', message=f"Erro ao obter coleções habilitadas: {str(e)}")
    finally:
        conn.close()

    return render_template('enabled_collections.html', configs=configs)

@app.route('/mapping')
@login_required
def view_mapping():
    """Visualiza o mapeamento Chatwoot."""
    mapping = get_mapping()

    if not mapping:
        return render_template('error.html', message="Mapeamento não encontrado")

    # Formatar JSON para exibição
    json_formatted = json.dumps(mapping['mapping_data'], indent=2, ensure_ascii=False)

    return render_template('mapping.html', mapping=mapping, json_formatted=json_formatted)

@app.route('/api/config/<tenant_id>/<domain>/<config_type>')
@login_required
def api_config(tenant_id, domain, config_type):
    """API para obter uma configuração específica."""
    version = request.args.get('version')
    config = get_config(tenant_id, domain, config_type, version)

    if not config:
        return jsonify({"error": f"Configuração não encontrada: {tenant_id}/{domain}/{config_type}"}), 404

    return jsonify({
        "id": config['id'],
        "tenant_id": config['tenant_id'],
        "domain": config['domain'],
        "config_type": config['config_type'],
        "version": config['version'],
        "json_data": config['json_data'],
        "created_at": config['created_at'].isoformat(),
        "updated_at": config['updated_at'].isoformat()
    })

@app.route('/docs')
@login_required
def docs():
    """Página de documentação."""
    return render_template('docs.html')

@app.route('/api/enabled_collections')
@login_required
def api_enabled_collections():
    """API para obter a seção enabled_collections de todas as configurações."""
    configs = []
    conn = connect_to_db()
    if not conn:
        return jsonify({"error": "Erro ao conectar ao banco de dados"}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tenant_id, domain, json_data->'enabled_collections' as enabled_collections, version
            FROM crew_configurations
            WHERE config_type = 'config'
            ORDER BY tenant_id, domain, version DESC
        """)

        configs = cursor.fetchall()
        cursor.close()
    except Exception as e:
        logger.error(f"Erro ao obter coleções habilitadas: {str(e)}")
        return jsonify({"error": f"Erro ao obter coleções habilitadas: {str(e)}"}), 500
    finally:
        conn.close()

    return jsonify([{
        "tenant_id": config['tenant_id'],
        "domain": config['domain'],
        "enabled_collections": config['enabled_collections'],
        "version": config['version']
    } for config in configs])

@app.route('/health')
def health_check():
    """Endpoint de verificação de saúde."""
    try:
        conn = connect_to_db()
        if not conn:
            logger.error("Erro ao conectar ao banco de dados durante health check")
            return jsonify({"status": "error", "message": "Erro ao conectar ao banco de dados"}), 500

        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()

        logger.info("Health check bem-sucedido")
        return jsonify({"status": "ok", "message": "Serviço saudável"}), 200
    except Exception as e:
        logger.error(f"Erro durante health check: {str(e)}")
        return jsonify({"status": "error", "message": f"Erro: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
