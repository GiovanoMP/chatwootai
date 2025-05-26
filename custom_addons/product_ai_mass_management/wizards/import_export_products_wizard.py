# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64
import csv
import io
import xlrd
import xlwt
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class ProductImportExportWizard(models.TransientModel):
    _name = 'product.import.export.wizard'
    _description = 'Assistente para Importação/Exportação de Produtos'

    # Campos comuns
    operation = fields.Selection([
        ('import', 'Importar Produtos'),
        ('export', 'Exportar Produtos')
    ], string='Operação', default='import', required=True)
    
    file_format = fields.Selection([
        ('csv', 'CSV'),
        ('excel', 'Excel')
    ], string='Formato do Arquivo', default='csv', required=True)
    
    # Campos para importação
    import_file = fields.Binary(string='Arquivo para Importação')
    import_filename = fields.Char(string='Nome do Arquivo')
    
    # Campos para exportação
    export_file = fields.Binary(string='Arquivo Exportado', readonly=True)
    export_filename = fields.Char(string='Nome do Arquivo Exportado', readonly=True)
    
    # Opções de exportação
    export_scope = fields.Selection([
        ('selected', 'Produtos Selecionados'),
        ('all', 'Todos os Produtos'),
        ('filtered', 'Produtos Filtrados')
    ], string='Escopo da Exportação', default='selected', required=True)
    
    include_inactive = fields.Boolean(string='Incluir Produtos Inativos', default=False)
    
    # Campos para mapeamento
    channel_id = fields.Many2one(
        'product.sales.channel', 
        string='Canal de Vendas',
        help='Selecione um canal específico para importar/exportar preços específicos'
    )
    
    # Campos para status e feedback
    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('imported', 'Importado'),
        ('exported', 'Exportado')
    ], string='Status', default='draft')
    
    import_log = fields.Text(string='Log de Importação', readonly=True)
    
    # Estatísticas
    total_rows = fields.Integer(string='Total de Linhas', readonly=True)
    processed_rows = fields.Integer(string='Linhas Processadas', readonly=True)
    success_rows = fields.Integer(string='Sucessos', readonly=True)
    error_rows = fields.Integer(string='Erros', readonly=True)
    
    def action_import(self):
        """Importa produtos do arquivo selecionado."""
        self.ensure_one()
        
        if not self.import_file:
            raise UserError(_('Por favor, selecione um arquivo para importar.'))
        
        # Decodificar arquivo
        data = base64.b64decode(self.import_file)
        
        # Inicializar contadores
        self.total_rows = 0
        self.processed_rows = 0
        self.success_rows = 0
        self.error_rows = 0
        
        # Log de importação
        log_lines = []
        log_lines.append(f"Iniciando importação em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        try:
            # Processar arquivo CSV
            if self.file_format == 'csv':
                self._process_csv_import(data, log_lines)
            # Processar arquivo Excel
            else:
                self._process_excel_import(data, log_lines)
                
            # Atualizar log
            log_lines.append(f"Importação concluída em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            log_lines.append(f"Total de linhas: {self.total_rows}")
            log_lines.append(f"Linhas processadas: {self.processed_rows}")
            log_lines.append(f"Sucessos: {self.success_rows}")
            log_lines.append(f"Erros: {self.error_rows}")
            
            self.import_log = '\n'.join(log_lines)
            self.state = 'imported'
            
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'product.import.export.wizard',
                'view_mode': 'form',
                'res_id': self.id,
                'target': 'new',
                'context': self.env.context,
            }
            
        except Exception as e:
            log_lines.append(f"Erro fatal: {str(e)}")
            self.import_log = '\n'.join(log_lines)
            self.error_rows += 1
            self.state = 'draft'
            raise UserError(_('Erro ao importar arquivo: %s') % str(e))
    
    def _process_csv_import(self, data, log_lines):
        """Processa a importação de um arquivo CSV."""
        # Decodificar dados CSV
        file_input = io.StringIO(data.decode('utf-8'))
        reader = csv.reader(file_input, delimiter=',', quotechar='"')
        
        # Ler cabeçalho
        header = next(reader)
        self.total_rows = sum(1 for _ in reader)
        file_input.seek(0)
        next(reader)  # Pular cabeçalho novamente
        
        # Mapear colunas
        column_mapping = self._get_column_mapping(header)
        
        # Processar linhas
        for row_num, row in enumerate(reader, start=2):  # Começar de 2 para contar o cabeçalho
            try:
                self._process_import_row(row, column_mapping, row_num)
                self.success_rows += 1
            except Exception as e:
                log_lines.append(f"Erro na linha {row_num}: {str(e)}")
                self.error_rows += 1
            
            self.processed_rows += 1
    
    def _process_excel_import(self, data, log_lines):
        """Processa a importação de um arquivo Excel."""
        # Ler arquivo Excel
        book = xlrd.open_workbook(file_contents=data)
        sheet = book.sheet_by_index(0)
        
        # Ler cabeçalho
        header = [sheet.cell_value(0, col) for col in range(sheet.ncols)]
        self.total_rows = sheet.nrows - 1  # Subtrair cabeçalho
        
        # Mapear colunas
        column_mapping = self._get_column_mapping(header)
        
        # Processar linhas
        for row_num in range(1, sheet.nrows):  # Começar de 1 para pular o cabeçalho
            try:
                row = [sheet.cell_value(row_num, col) for col in range(sheet.ncols)]
                self._process_import_row(row, column_mapping, row_num + 1)  # +1 para contar o cabeçalho
                self.success_rows += 1
            except Exception as e:
                log_lines.append(f"Erro na linha {row_num + 1}: {str(e)}")
                self.error_rows += 1
            
            self.processed_rows += 1
    
    def _get_column_mapping(self, header):
        """Mapeia as colunas do arquivo para os campos do modelo."""
        # Mapeamento padrão de colunas
        mapping = {
            'default_code': -1,
            'name': -1,
            'list_price': -1,
            'standard_price': -1,
            'barcode': -1,
            'categ_id': -1,
            'type': -1,
            'uom_id': -1,
            'description': -1,
            'description_sale': -1,
            'weight': -1,
            'volume': -1,
            'sale_ok': -1,
            'purchase_ok': -1,
            'active': -1,
            'channel_price': -1,
        }
        
        # Mapear colunas do arquivo para campos do modelo
        for col_idx, col_name in enumerate(header):
            col_name = col_name.strip().lower()
            
            if col_name in ('default_code', 'código', 'code', 'sku', 'referência', 'reference'):
                mapping['default_code'] = col_idx
            elif col_name in ('name', 'nome', 'produto', 'product'):
                mapping['name'] = col_idx
            elif col_name in ('list_price', 'preço de venda', 'preço', 'price', 'sales price'):
                mapping['list_price'] = col_idx
            elif col_name in ('standard_price', 'custo', 'cost', 'preço de custo'):
                mapping['standard_price'] = col_idx
            elif col_name in ('barcode', 'código de barras', 'ean13', 'upc'):
                mapping['barcode'] = col_idx
            elif col_name in ('categ_id', 'categoria', 'category'):
                mapping['categ_id'] = col_idx
            elif col_name in ('type', 'tipo'):
                mapping['type'] = col_idx
            elif col_name in ('uom_id', 'unidade', 'unit', 'uom'):
                mapping['uom_id'] = col_idx
            elif col_name in ('description', 'descrição', 'desc'):
                mapping['description'] = col_idx
            elif col_name in ('description_sale', 'descrição de venda', 'sales description'):
                mapping['description_sale'] = col_idx
            elif col_name in ('weight', 'peso'):
                mapping['weight'] = col_idx
            elif col_name in ('volume'):
                mapping['volume'] = col_idx
            elif col_name in ('sale_ok', 'pode ser vendido', 'can be sold'):
                mapping['sale_ok'] = col_idx
            elif col_name in ('purchase_ok', 'pode ser comprado', 'can be purchased'):
                mapping['purchase_ok'] = col_idx
            elif col_name in ('active', 'ativo'):
                mapping['active'] = col_idx
            elif col_name in ('channel_price', 'preço no canal', 'preço específico', 'specific price'):
                mapping['channel_price'] = col_idx
        
        # Verificar campos obrigatórios
        if mapping['default_code'] == -1 and mapping['name'] == -1:
            raise UserError(_('O arquivo deve conter pelo menos uma coluna para identificar o produto (Código ou Nome).'))
        
        return mapping
    
    def _process_import_row(self, row, column_mapping, row_num):
        """Processa uma linha do arquivo de importação."""
        # Preparar valores
        vals = {}
        
        # Extrair valores das colunas mapeadas
        for field, col_idx in column_mapping.items():
            if col_idx >= 0 and col_idx < len(row):
                vals[field] = row[col_idx]
        
        # Buscar produto existente
        product = None
        if 'default_code' in vals and vals['default_code']:
            product = self.env['product.template'].search([
                ('default_code', '=', vals['default_code'])
            ], limit=1)
        
        if not product and 'name' in vals and vals['name']:
            product = self.env['product.template'].search([
                ('name', '=', vals['name'])
            ], limit=1)
        
        # Se não encontrou produto e tem dados suficientes, criar novo
        if not product and 'name' in vals and vals['name']:
            product_vals = self._prepare_product_values(vals)
            product = self.env['product.template'].create(product_vals)
            _logger.info(f"Produto criado: {product.name} (ID: {product.id})")
        
        # Se encontrou produto, atualizar
        elif product:
            product_vals = self._prepare_product_values(vals)
            product.write(product_vals)
            _logger.info(f"Produto atualizado: {product.name} (ID: {product.id})")
        
        # Se tem canal selecionado e preço específico, atualizar mapeamento
        if product and self.channel_id and 'channel_price' in vals and vals['channel_price']:
            self._update_channel_mapping(product, vals['channel_price'])
        
        # Atualizar data de importação
        if product:
            product.last_import_date = fields.Datetime.now()
    
    def _prepare_product_values(self, vals):
        """Prepara os valores para criação/atualização de produto."""
        product_vals = {}
        
        # Mapear valores para campos do produto
        if 'name' in vals and vals['name']:
            product_vals['name'] = vals['name']
        
        if 'default_code' in vals and vals['default_code']:
            product_vals['default_code'] = vals['default_code']
        
        if 'list_price' in vals and vals['list_price']:
            try:
                product_vals['list_price'] = float(vals['list_price'])
            except (ValueError, TypeError):
                pass
        
        if 'standard_price' in vals and vals['standard_price']:
            try:
                product_vals['standard_price'] = float(vals['standard_price'])
            except (ValueError, TypeError):
                pass
        
        if 'barcode' in vals and vals['barcode']:
            product_vals['barcode'] = vals['barcode']
        
        if 'description' in vals and vals['description']:
            product_vals['description'] = vals['description']
        
        if 'description_sale' in vals and vals['description_sale']:
            product_vals['description_sale'] = vals['description_sale']
        
        if 'weight' in vals and vals['weight']:
            try:
                product_vals['weight'] = float(vals['weight'])
            except (ValueError, TypeError):
                pass
        
        if 'volume' in vals and vals['volume']:
            try:
                product_vals['volume'] = float(vals['volume'])
            except (ValueError, TypeError):
                pass
        
        if 'sale_ok' in vals:
            product_vals['sale_ok'] = vals['sale_ok'] in ('True', 'true', '1', 'Yes', 'yes', 'Sim', 'sim', True, 1)
        
        if 'purchase_ok' in vals:
            product_vals['purchase_ok'] = vals['purchase_ok'] in ('True', 'true', '1', 'Yes', 'yes', 'Sim', 'sim', True, 1)
        
        if 'active' in vals:
            product_vals['active'] = vals['active'] in ('True', 'true', '1', 'Yes', 'yes', 'Sim', 'sim', True, 1)
        
        # Processar categoria se fornecida
        if 'categ_id' in vals and vals['categ_id']:
            category = self.env['product.category'].search([
                ('name', '=', vals['categ_id'])
            ], limit=1)
            
            if not category:
                category = self.env['product.category'].create({
                    'name': vals['categ_id']
                })
            
            product_vals['categ_id'] = category.id
        
        # Processar unidade de medida se fornecida
        if 'uom_id' in vals and vals['uom_id']:
            uom = self.env['uom.uom'].search([
                ('name', '=', vals['uom_id'])
            ], limit=1)
            
            if uom:
                product_vals['uom_id'] = uom.id
        
        # Processar tipo de produto se fornecido
        if 'type' in vals and vals['type']:
            type_mapping = {
                'consumable': 'consu',
                'consumível': 'consu',
                'service': 'service',
                'serviço': 'service',
                'stockable': 'product',
                'estocável': 'product',
                'product': 'product',
                'produto': 'product'
            }
            
            product_type = type_mapping.get(vals['type'].lower(), 'product')
            product_vals['type'] = product_type
        
        return product_vals
    
    def _update_channel_mapping(self, product, channel_price):
        """Atualiza o mapeamento de canal para o produto."""
        try:
            channel_price = float(channel_price)
        except (ValueError, TypeError):
            return
        
        # Buscar mapeamento existente
        mapping = self.env['product.channel.mapping'].search([
            ('product_id', '=', product.id),
            ('channel_id', '=', self.channel_id.id)
        ], limit=1)
        
        # Se não existe, criar
        if not mapping:
            mapping = self.env['product.channel.mapping'].create({
                'product_id': product.id,
                'channel_id': self.channel_id.id,
                'specific_price': channel_price,
                'use_specific_price': True,
                'sync_status': 'not_synced'
            })
        # Se existe, atualizar
        else:
            mapping.write({
                'specific_price': channel_price,
                'use_specific_price': True,
                'sync_status': 'needs_update'
            })
    
    def action_export(self):
        """Exporta produtos para o formato selecionado."""
        self.ensure_one()
        
        # Obter produtos conforme escopo selecionado
        products = self._get_products_for_export()
        
        if not products:
            raise UserError(_('Nenhum produto encontrado para exportar.'))
        
        # Exportar para o formato selecionado
        if self.file_format == 'csv':
            export_data = self._export_to_csv(products)
            filename = f'produtos_exportados_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        else:
            export_data = self._export_to_excel(products)
            filename = f'produtos_exportados_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xls'
        
        # Atualizar data de exportação
        for product in products:
            product.last_export_date = fields.Datetime.now()
        
        # Atualizar campos do wizard
        self.write({
            'export_file': export_data,
            'export_filename': filename,
            'state': 'exported',
            'total_rows': len(products),
            'processed_rows': len(products),
            'success_rows': len(products),
            'error_rows': 0
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.import.export.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': self.env.context,
        }
    
    def _get_products_for_export(self):
        """Obtém os produtos para exportação conforme o escopo selecionado."""
        domain = []
        
        # Filtrar por produtos ativos/inativos
        if not self.include_inactive:
            domain.append(('active', '=', True))
        
        # Aplicar escopo
        if self.export_scope == 'selected':
            active_ids = self.env.context.get('active_ids', [])
            if not active_ids:
                raise UserError(_('Nenhum produto selecionado para exportação.'))
            domain.append(('id', 'in', active_ids))
        elif self.export_scope == 'filtered':
            # Usar o domínio atual da vista de produtos
            action = self.env.ref('product_ai_mass_management.action_product_ai_mass_management')
            if action and action.domain:
                domain.extend(eval(action.domain))
        
        # Buscar produtos
        return self.env['product.template'].search(domain)
    
    def _export_to_csv(self, products):
        """Exporta produtos para CSV."""
        # Criar buffer para CSV
        output = io.StringIO()
        writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        # Escrever cabeçalho
        header = self._get_export_header()
        writer.writerow(header)
        
        # Escrever linhas de produtos
        for product in products:
            row = self._get_product_export_row(product)
            writer.writerow(row)
        
        # Codificar para base64
        data = output.getvalue().encode('utf-8')
        return base64.b64encode(data)
    
    def _export_to_excel(self, products):
        """Exporta produtos para Excel."""
        # Criar workbook
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Produtos')
        
        # Estilos
        header_style = xlwt.easyxf('font: bold on; align: horiz center')
        
        # Escrever cabeçalho
        header = self._get_export_header()
        for col_idx, col_name in enumerate(header):
            worksheet.write(0, col_idx, col_name, header_style)
        
        # Escrever linhas de produtos
        for row_idx, product in enumerate(products, start=1):
            row = self._get_product_export_row(product)
            for col_idx, cell_value in enumerate(row):
                worksheet.write(row_idx, col_idx, cell_value)
        
        # Salvar para buffer
        output = io.BytesIO()
        workbook.save(output)
        
        # Codificar para base64
        return base64.b64encode(output.getvalue())
    
    def _get_export_header(self):
        """Retorna o cabeçalho para exportação."""
        header = [
            'Código',
            'Nome',
            'Categoria',
            'Tipo',
            'Unidade',
            'Preço de Venda',
            'Preço de Custo',
            'Código de Barras',
            'Peso',
            'Volume',
            'Pode ser Vendido',
            'Pode ser Comprado',
            'Ativo',
            'Descrição',
            'Descrição de Venda',
        ]
        
        # Adicionar coluna para preço específico do canal se selecionado
        if self.channel_id:
            header.append(f'Preço no Canal {self.channel_id.name}')
        
        return header
    
    def _get_product_export_row(self, product):
        """Retorna uma linha de dados do produto para exportação."""
        row = [
            product.default_code or '',
            product.name or '',
            product.categ_id.name if product.categ_id else '',
            dict(product._fields['type'].selection).get(product.type, ''),
            product.uom_id.name if product.uom_id else '',
            product.list_price or 0.0,
            product.standard_price or 0.0,
            product.barcode or '',
            product.weight or 0.0,
            product.volume or 0.0,
            'Sim' if product.sale_ok else 'Não',
            'Sim' if product.purchase_ok else 'Não',
            'Sim' if product.active else 'Não',
            product.description or '',
            product.description_sale or '',
        ]
        
        # Adicionar preço específico do canal se selecionado
        if self.channel_id:
            mapping = self.env['product.channel.mapping'].search([
                ('product_id', '=', product.id),
                ('channel_id', '=', self.channel_id.id)
            ], limit=1)
            
            if mapping and mapping.use_specific_price:
                row.append(mapping.specific_price)
            else:
                row.append(product.list_price)
        
        return row
