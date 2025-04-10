#!/usr/bin/env python3
import importlib.util
import sys
import os

# Adicionar diretório ao path
sys.path.append('./addons')

# Simular ambiente Odoo
class MockOdoo:
    class api:
        @staticmethod
        def model(func):
            return func
        
        @staticmethod
        def depends(*args):
            def decorator(func):
                return func
            return decorator
    
    class fields:
        Text = str
        Char = str
        Boolean = bool
        Datetime = str
        Selection = list
        
        @staticmethod
        def Selection(*args, **kwargs):
            return str
    
    class models:
        class Model:
            _inherit = None
            
            def __init__(self):
                pass
            
            def write(self, *args, **kwargs):
                pass
            
            def ensure_one(self):
                pass
            
            def search(self, *args, **kwargs):
                return []

# Adicionar mock ao sys.modules
sys.modules['odoo'] = MockOdoo
sys.modules['odoo.api'] = MockOdoo.api
sys.modules['odoo.fields'] = MockOdoo.fields
sys.modules['odoo.models'] = MockOdoo.models

# Tentar importar o módulo
try:
    print("Tentando carregar o módulo product_template.py...")
    spec = importlib.util.spec_from_file_location(
        "product_template", 
        "./addons/semantic_product_description/models/product_template.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    print("Módulo carregado com sucesso!")
    
    # Verificar se a classe ProductTemplate foi definida
    if hasattr(module, 'ProductTemplate'):
        print("Classe ProductTemplate encontrada!")
        
        # Listar campos definidos
        fields = [attr for attr in dir(module.ProductTemplate) if attr.startswith('semantic_')]
        print(f"Campos semânticos definidos: {fields}")
    else:
        print("Classe ProductTemplate não encontrada!")
        
except Exception as e:
    print(f"Erro ao carregar o módulo: {str(e)}")
    import traceback
    traceback.print_exc()
