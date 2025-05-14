# Melhores Práticas para Desenvolvimento de Módulos no Odoo 18

Este documento contém as melhores práticas e aprendizados obtidos durante o desenvolvimento de módulos para o Odoo 18.

## Índice

1. [Estrutura de Arquivos](#estrutura-de-arquivos)
2. [Ordem de Carregamento](#ordem-de-carregamento)
3. [Referências a IDs Externos](#referências-a-ids-externos)
4. [Campos e Modelos](#campos-e-modelos)
5. [Vistas XML](#vistas-xml)
6. [Segurança e Permissões](#segurança-e-permissões)
7. [Migração de Módulos](#migração-de-módulos)
8. [Problemas Comuns e Soluções](#problemas-comuns-e-soluções)
9. [Testes e Depuração](#testes-e-depuração)
10. [Referências Úteis](#referências-úteis)

## Estrutura de Arquivos

A estrutura básica de um módulo Odoo 18 deve seguir o seguinte padrão:

```
nome_do_modulo/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── controllers.py
├── data/
│   └── dados_iniciais.xml
├── models/
│   ├── __init__.py
│   └── models.py
├── security/
│   ├── ir.model.access.csv
│   └── regras_seguranca.xml
├── static/
│   ├── description/
│   │   └── icon.png
│   └── src/
├── views/
│   └── views.xml
└── wizards/
    ├── __init__.py
    └── wizards.py
```

**Dicas:**
- Mantenha os arquivos organizados em diretórios apropriados
- Divida modelos grandes em arquivos menores e mais específicos
- Use nomes descritivos para arquivos e diretórios

## Ordem de Carregamento

A ordem de carregamento dos arquivos no `__manifest__.py` é **crucial** para o funcionamento correto do módulo. Siga esta ordem:

1. Arquivos de segurança (`security/`)
2. Arquivos de dados que definem registros referenciados por outros arquivos
3. Arquivos de wizards que são referenciados em views
4. Arquivos de views
5. Arquivos de dados que dependem de views ou outros registros

**Exemplo correto:**
```python
'data': [
    'security/regras_seguranca.xml',
    'security/ir.model.access.csv',
    'wizards/wizard_upload.xml',  # Carregado antes das views que o referenciam
    'views/views_principais.xml',
    'views/views_secundarias.xml',
    'data/dados_iniciais.xml',
],
```

**Problema comum:** Erros de "External ID not found in the system" geralmente indicam problemas na ordem de carregamento.

## Referências a IDs Externos

Ao referenciar IDs externos em arquivos XML, sempre use o formato completo com o nome do módulo:

```xml
<!-- Correto -->
<button name="%(nome_do_modulo.action_wizard)d" type="action"/>

<!-- Incorreto -->
<button name="%(action_wizard)d" type="action"/>
```

**Importante:** No Odoo 18, as referências a IDs externos sem o nome do módulo não funcionam mais em muitos contextos.

## Campos e Modelos

### Mudanças no Odoo 18:

1. **Campos Deprecados:**
   - Alguns campos como `mimetype` foram removidos de modelos como `product.template`
   - Verifique a documentação para campos que foram removidos ou renomeados
   - Certifique-se de remover referências a campos deprecados em todas as views XML

2. **Novos Campos Obrigatórios:**
   - Alguns modelos agora exigem campos que eram opcionais em versões anteriores

3. **Tipos de Campos:**
   - Use `fields.Boolean` em vez de `fields.boolean`
   - Use `fields.Char` em vez de `fields.char`
   - Todos os tipos de campos agora começam com letra maiúscula

4. **Remoção de Campos:**
   - Ao remover um campo de um modelo, certifique-se de remover todas as referências a ele nas views XML
   - Comente no código a razão da remoção do campo para referência futura
   - Exemplo: `# Removido o campo rule_type que estava causando problemas no Odoo 18`

### Boas Práticas:

- Sempre defina um `_description` para seus modelos
- Use `_inherit` para estender modelos existentes
- Defina `_order` para controlar a ordem padrão dos registros
- Use `tracking=True` para campos que devem ser rastreados no chatter

## Vistas XML

### Mudanças no Odoo 18:

1. **Atributos de Vista:**
   - O atributo `type` para `ir.ui.view` agora aceita apenas valores específicos
   - `tree` foi substituído por `list` em alguns contextos

2. **Widgets:**
   - Alguns widgets foram renomeados ou substituídos
   - Use `widget="boolean_toggle"` em vez de `widget="boolean"`

3. **Ícones:**
   - A sintaxe para ícones mudou em alguns elementos
   - Use classes de ícones do Font Awesome 5 (fa5)

### Boas Práticas:

- Use `attrs` para controlar a visibilidade e estados dos campos
- Agrupe campos relacionados em `<group>` para melhor organização
- Use `placeholder` para fornecer dicas nos campos
- Defina `string` para labels claros e descritivos

## Segurança e Permissões

1. **Grupos de Segurança:**
   - Defina grupos de segurança no arquivo `security/regras_seguranca.xml`
   - Use categorias para organizar os grupos

2. **Permissões de Acesso:**
   - Defina permissões no arquivo `ir.model.access.csv`
   - Conceda apenas as permissões necessárias (princípio do menor privilégio)

3. **Regras de Registro:**
   - Use regras de registro para restringir o acesso a registros específicos
   - Teste cuidadosamente as regras para evitar problemas de acesso

## Migração de Módulos

Ao migrar módulos de versões anteriores para o Odoo 18:

1. **Atualize a versão no `__manifest__.py`:**
   ```python
   'version': '18.0.1.0.0',
   ```

2. **Verifique campos deprecados:**
   - Remova ou substitua campos que foram deprecados

3. **Atualize as dependências:**
   - Verifique se os módulos dependentes estão disponíveis no Odoo 18

4. **Teste gradualmente:**
   - Comece com funcionalidades básicas e adicione gradualmente
   - Teste cada etapa antes de prosseguir

## Problemas Comuns e Soluções

### 1. "External ID not found in the system"

**Problema:** Referência a um ID externo que não existe ou não foi carregado ainda.

**Solução:**
- Verifique a ordem de carregamento no `__manifest__.py`
- Use o formato completo com o nome do módulo: `%(nome_do_modulo.id_externo)d`
- Verifique se o ID externo está definido corretamente

### 2. "O campo X não existe no modelo Y"

**Problema:** Referência a um campo que não existe no modelo.

**Solução:**
- Verifique se o campo está definido no modelo
- Remova referências ao campo nas views XML
- Verifique se o campo foi removido ou renomeado em versões anteriores
- Certifique-se de que todas as views estão atualizadas para refletir a estrutura atual do modelo

**Caso especial - Campos em modelos relacionados:**
- No Odoo 18, há um problema com campos em views embutidas (embedded views) dentro de campos One2many/Many2many
- Por exemplo, se você tem um campo One2many `temporary_rule_ids` que aponta para o modelo `business.temporary.rule`, e este modelo tem um campo `date_start`, o Odoo 18 pode gerar um erro dizendo que o campo `date_start` não existe no modelo principal
- Solução: Adicione campos dummy com os mesmos nomes no modelo principal para todos os campos referenciados nas views embutidas:
  ```python
  # Campos dummy para compatibilidade com views embutidas
  date_start = fields.Date(string='Data de Início', compute='_compute_dummy_fields')
  date_end = fields.Date(string='Data de Término', compute='_compute_dummy_fields')
  rule_type = fields.Selection([
      ('promotion', 'Promoção'),
      ('discount', 'Desconto'),
      ('seasonal', 'Sazonal'),
      ('event', 'Evento'),
      ('holiday', 'Feriado'),
      ('other', 'Outro')
  ], string='Tipo de Regra', compute='_compute_dummy_fields')

  def _compute_dummy_fields(self):
      """Método dummy para campos computados de compatibilidade"""
      for record in self:
          record.date_start = fields.Date.today()
          record.date_end = fields.Date.today()
          record.rule_type = 'other'
  ```

- É importante adicionar **todos** os campos referenciados nas views embutidas, mesmo que eles sejam usados apenas em condições ou atributos
- Organize os campos dummy por modelo relacionado e adicione comentários claros para facilitar a manutenção
- Certifique-se de que o método `_compute_dummy_fields` define valores padrão para todos os campos dummy

### 3. "ValueError: Invalid view definition"

**Problema:** Erro na definição de uma vista XML.

**Solução:**
- Verifique a sintaxe XML
- Verifique se todos os campos referenciados existem no modelo
- Verifique se os atributos estão corretos para a versão do Odoo

### 4. Loop de Instalação ("Cancelar a instalação?")

**Problema:** O módulo entra em um loop de instalação sem mostrar erros específicos.

**Solução:**
- Verifique os logs do servidor Odoo para erros detalhados
- Verifique dependências circulares
- Verifique se todos os arquivos referenciados no `__manifest__.py` existem
- Verifique a ordem de carregamento dos arquivos

## Testes e Depuração

1. **Logs do Servidor:**
   - Verifique os logs do servidor Odoo para erros detalhados
   - Use `_logger.info()` para adicionar mensagens de depuração

2. **Modo Desenvolvedor:**
   - Ative o modo desenvolvedor no Odoo para ver erros detalhados
   - Use as ferramentas de desenvolvedor do navegador para depurar JavaScript

3. **Testes Unitários:**
   - Escreva testes unitários para seus modelos
   - Execute os testes antes de implantar

## Referências Úteis

- [Documentação Oficial do Odoo 18](https://www.odoo.com/documentation/18.0/)
- [Guia de Migração do Odoo 18](https://www.odoo.com/documentation/18.0/developer/reference/upgrade_api.html)
- [Fórum da Comunidade Odoo](https://www.odoo.com/forum/help-1)
- [GitHub do Odoo](https://github.com/odoo/odoo)
