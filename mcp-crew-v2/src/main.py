import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mcp_crew_main")

# Importar blueprints da nova estrutura
from src.api.routes.crew_routes import mcp_crew_bp
from src.api.routes.user import user_bp

# Inicializar instâncias globais
from src.core.orchestrator import mcp_crew_orchestrator
from src.core.mcp_tool_discovery import tool_discovery
from src.core.knowledge_manager import knowledge_manager
from src.redis_manager.redis_manager import redis_manager

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Enable CORS for all routes
CORS(app)

# Registrar blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(mcp_crew_bp)

# Configuração do banco de dados (se necessário)
try:
    from src.models.user import db
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()
    logger.info("Banco de dados inicializado com sucesso")
except ImportError:
    logger.warning("Módulo de banco de dados não encontrado, continuando sem suporte a banco de dados")
except Exception as e:
    logger.error(f"Erro ao inicializar banco de dados: {e}")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    port = int(os.getenv('FLASK_RUN_PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=True)
