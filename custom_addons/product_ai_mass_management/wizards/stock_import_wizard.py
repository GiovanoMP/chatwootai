# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
import base64
import json
import tempfile
import os
import xlrd
from datetime import datetime

_logger = logging.getLogger(__name__)

class ProductImportWizard(models.TransientModel):
    _name = 'stock.import.wizard'
    _description = 'Assistente para Importação de Produtos'

    # Campos para importação
    file_format = fields.Selection([
        ('excel', 'Excel'),
        ('json', 'JSON')
    ], string='Formato do Arquivo', default='excel', required=True)
    
    import_file = fields.Binary(string='Arquivo para Importação', required=True)
    import_filename = fields.Char(string='Nome do Arquivo')
    
    # Opções de importação
    update_existing = fields.Boolean(string='Atualizar Produtos Existentes', default=True,
                                     help='Se marcado, produtos existentes serão atualizados. Caso contrário, apenas novos produtos serão criados.')
    
    create_categories = fields.Boolean(string='Criar Categorias Automaticamente', default=True,
                                      help='Se marcado, categorias não existentes serão criadas automaticamente.')
    
    def action_import(self):
        """Importa produtos do arquivo selecionado."""
        self.ensure_one()
        
        if not self.import_file:
            raise UserError(_('Por favor, selecione um arquivo para importar.'))
        
        # Decodificar o arquivo
        file_data = base64.b64decode(self.import_file)
        
        # Processar o arquivo de acordo com o formato
        if self.file_format == 'excel':
            products_data = self._process_excel_file(file_data)
        elif self.file_format == 'json':
            products_data = self._process_json_file(file_data)
        else:
            raise UserError(_('Formato de arquivo não suportado.'))
        
        # Importar os produtos
        result = self._import_products(products_data)
        
        # Retornar mensagem de sucesso
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Importação Concluída'),
                'message': _('%s produtos importados com sucesso. %s produtos atualizados. %s erros encontrados.') % 
                           (result['created'], result['updated'], result['errors']),
                'sticky': False,
                'type': 'success' if result['errors'] == 0 else 'warning',
            }
        }
    
    def _process_excel_file(self, file_data):
        """Processa arquivo Excel e retorna lista de dicionários com dados dos produtos."""
        # Salvar o arquivo temporariamente
        fd, temp_path = tempfile.mkstemp(suffix='.xlsx')
        try:
            with os.fdopen(fd, 'wb') as temp_file:
                temp_file.write(file_data)
            
            # Ler o arquivo Excel
            workbook = xlrd.open_workbook(temp_path)
            sheet = workbook.sheet_by_index(0)
            
            # Obter cabeçalhos
            headers = []
            for col in range(sheet.ncols):
                header = sheet.cell_value(0, col)
                if header:
                    headers.append(header)
            
            # Processar linhas
            products_data = []
            for row in range(1, sheet.nrows):
                product = {}
                for col, header in enumerate(headers):
                    if col < sheet.ncols:
                        value = sheet.cell_value(row, col)
                        # Converter tipos de dados
                        if sheet.cell_type(row, col) == xlrd.XL_CELL_DATE:
                            value = datetime(*xlrd.xldate_as_tuple(value, workbook.datemode))
                        elif sheet.cell_type(row, col) == xlrd.XL_CELL_BOOLEAN:
                            value = bool(value)
                        elif sheet.cell_type(row, col) == xlrd.XL_CELL_NUMBER:
                            # Manter como inteiro se for um número inteiro
                            if value == int(value):
                                value = int(value)
                        
                        # Normalizar nome da coluna
                        normalized_key = header.lower().strip().replace(' ', '_')
                        product[normalized_key] = value
                
                # Adicionar produto apenas se tiver dados
                if product:
                    products_data.append(product)
            
            return products_data
        
        finally:
            # Remover arquivo temporário
            os.unlink(temp_path)
    
    def _process_json_file(self, file_data):
        """Processa arquivo JSON e retorna lista de dicionários com dados dos produtos."""
        try:
            # Decodificar JSON
            products_data = json.loads(file_data.decode('utf-8'))
            
            # Verificar se é uma lista
            if not isinstance(products_data, list):
                if isinstance(products_data, dict) and 'products' in products_data:
                    products_data = products_data['products']
                else:
                    products_data = [products_data]
            
            # Normalizar nomes de chaves
            normalized_data = []
            for product in products_data:
                normalized_product = {}
                for key, value in product.items():
                    # Normalizar nomes de chaves
                    normalized_key = key.lower().strip().replace(' ', '_')
                    normalized_product[normalized_key] = value
                
                normalized_data.append(normalized_product)
            
            return normalized_data
        
        except json.JSONDecodeError as e:
            raise UserError(_('Erro ao decodificar arquivo JSON: %s') % str(e))
    
    def _import_products(self, products_data):
        """Importa produtos a partir dos dados processados."""
        Product = self.env['product.template']
        Category = self.env['product.category']
        
        result = {'created': 0, 'updated': 0, 'errors': 0}
        
        for product_data in products_data:
            try:
                # Mapear campos do arquivo para campos do Odoo
                vals = self._map_product_fields(product_data, Category)
                
                # Verificar se o produto já existe
                existing_product = None
                if 'default_code' in vals and vals['default_code']:
                    existing_product = Product.search([('default_code', '=', vals['default_code'])], limit=1)
                elif 'barcode' in vals and vals['barcode']:
                    existing_product = Product.search([('barcode', '=', vals['barcode'])], limit=1)
                elif 'name' in vals and vals['name']:
                    existing_product = Product.search([('name', '=', vals['name'])], limit=1)
                
                if existing_product and self.update_existing:
                    # Atualizar produto existente
                    existing_product.write(vals)
                    result['updated'] += 1
                    _logger.info(f"Produto {existing_product.id} - {existing_product.name} atualizado com sucesso")
                elif not existing_product:
                    # Criar novo produto
                    new_product = Product.create(vals)
                    result['created'] += 1
                    _logger.info(f"Produto {new_product.id} - {new_product.name} criado com sucesso")
            
            except Exception as e:
                result['errors'] += 1
                _logger.error(f"Erro ao importar produto: {str(e)}\nDados: {product_data}")
        
        return result
    
    def _map_product_fields(self, product_data, Category):
        """Mapeia campos do arquivo para campos do Odoo."""
        vals = {}
        
        # Mapeamento de campos básicos
        field_mapping = {
            'name': 'name',
            'codigo': 'default_code',
            'default_code': 'default_code',
            'code': 'default_code',
            'sku': 'default_code',
            'barcode': 'barcode',
            'ean13': 'barcode',
            'preco': 'list_price',
            'price': 'list_price',
            'list_price': 'list_price',
            'custo': 'standard_price',
            'cost': 'standard_price',
            'standard_price': 'standard_price',
            'descricao': 'description',
            'description': 'description',
            'descricao_venda': 'description_sale',
            'description_sale': 'description_sale',
            'peso': 'weight',
            'weight': 'weight',
            'volume': 'volume',
            'ativo': 'active',
            'active': 'active',
            'tipo': 'type',
            'type': 'type',
        }
        
        # Mapear campos
        for src_field, dst_field in field_mapping.items():
            if src_field in product_data and product_data[src_field] not in (None, '', False):
                # Converter valores booleanos
                if dst_field == 'active' and isinstance(product_data[src_field], str):
                    vals[dst_field] = product_data[src_field].lower() in ('1', 'true', 'yes', 'sim', 'ativo', 'active')
                # Converter valores numéricos
                elif dst_field in ('list_price', 'standard_price', 'weight', 'volume'):
                    try:
                        vals[dst_field] = float(product_data[src_field])
                    except (ValueError, TypeError):
                        pass
                else:
                    vals[dst_field] = product_data[src_field]
        
        # Processar categoria
        if any(field in product_data for field in ('category', 'categoria', 'categ_id', 'product_category')):
            category_name = next((product_data[field] for field in ('category', 'categoria', 'categ_id', 'product_category') 
                                if field in product_data and product_data[field]), None)
            
            if category_name and isinstance(category_name, str):
                category = Category.search([('name', '=', category_name)], limit=1)
                
                if not category and self.create_categories:
                    # Criar categoria se não existir
                    category = Category.create({'name': category_name})
                
                if category:
                    vals['categ_id'] = category.id
        
        # Garantir que campos obrigatórios estão presentes
        if 'name' not in vals and 'default_code' in vals:
            vals['name'] = vals['default_code']
        
        # Definir tipo padrão se não especificado
        if 'type' not in vals:
            vals['type'] = 'product'  # Produto estocável
        
        return vals
