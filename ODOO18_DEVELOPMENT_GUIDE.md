# Odoo 18 Development Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Module Structure](#module-structure)
3. [Key Changes in Odoo 18](#key-changes-in-odoo-18)
4. [Common Issues and Solutions](#common-issues-and-solutions)
5. [Best Practices](#best-practices)
6. [Debugging Techniques](#debugging-techniques)

## Introduction

This guide provides comprehensive information about developing modules for Odoo 18, with a focus on common issues and their solutions. It is particularly useful for developers migrating modules from earlier versions of Odoo.

## Module Structure

A typical Odoo 18 module follows this structure:

```
module_name/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── controllers.py
├── data/
│   └── data.xml
├── models/
│   ├── __init__.py
│   └── models.py
├── security/
│   ├── ir.model.access.csv
│   └── security.xml
├── static/
│   ├── description/
│   │   └── icon.png
│   └── src/
├── views/
│   └── views.xml
└── wizards/
    ├── __init__.py
    └── wizards.xml
```

### Key Files

- `__manifest__.py`: Contains module metadata and dependencies
- `models/`: Contains Python model definitions
- `views/`: Contains XML view definitions
- `security/`: Contains access rights and rules

## Key Changes in Odoo 18

### 1. Stricter View Validation

Odoo 18 has implemented stricter validation for views, particularly for embedded views in one2many and many2many fields. The system now validates that all fields referenced in embedded views must exist in the parent model, even if they are actually fields of the related model.

### 2. XML ID References

In Odoo 18, all XML ID references must include the module name prefix. For example:

```xml
<!-- Incorrect in Odoo 18 -->
<button name="%(action_document_upload_wizard)d" type="action"/>

<!-- Correct in Odoo 18 -->
<button name="%(module_name.action_document_upload_wizard)d" type="action"/>
```

### 3. Field Types Capitalization

All field types in Odoo 18 must start with a capital letter:

```python
# Incorrect in Odoo 18
name = fields.char(string='Name')

# Correct in Odoo 18
name = fields.Char(string='Name')
```

## Common Issues and Solutions

### 1. "Field does not exist in model" Error in Embedded Views

#### Problem

When using embedded views in one2many or many2many fields, Odoo 18 validates that all fields referenced in the embedded view exist in the parent model, not just in the related model.

For example, if you have a model `business.rules` with a one2many field `temporary_rule_ids` pointing to `business.temporary.rule`, and the embedded view references fields like `date_start` that exist in `business.temporary.rule` but not in `business.rules`, you'll get an error.

#### Solution

There are two approaches to solve this issue:

1. **Add dummy fields to the parent model**:

```python
# In the parent model (business.rules)
date_start = fields.Date(string='Data de Início', compute='_compute_dummy_fields')
date_end = fields.Date(string='Data de Término', compute='_compute_dummy_fields')

def _compute_dummy_fields(self):
    """Dummy method for compatibility with embedded views"""
    for record in self:
        record.date_start = fields.Date.today()
        record.date_end = fields.Date.today()
```

2. **Use a separate view for the related model**:

Instead of embedding the view directly, define a separate view for the related model and reference it in the parent view.

### 2. Order of Loading in `__manifest__.py`

#### Problem

The order of loading files in the `__manifest__.py` is crucial in Odoo 18. If a view references an XML ID defined in another file, that file must be loaded first.

#### Solution

Ensure the correct loading order in the `data` section of `__manifest__.py`:

```python
'data': [
    'security/security.xml',
    'security/ir.model.access.csv',
    'wizards/wizard_views.xml',  # Load wizard views before they are referenced
    'views/model_views.xml',
    'data/data.xml',
],
```

### 3. Missing Module Name in XML ID References

#### Problem

In Odoo 18, all XML ID references must include the module name prefix.

#### Solution

Always use the full XML ID with module name:

```xml
<button name="%(module_name.action_wizard)d" type="action"/>
```

## Best Practices

### 1. Field Definitions

- Always use capitalized field types (`fields.Char`, not `fields.char`)
- Add descriptive `string` attributes to all fields
- Use `compute` methods for calculated fields
- Add `store=True` for computed fields that need to be searchable

### 2. View Definitions

- Use proper view inheritance
- Organize views by model
- Use appropriate view types (form, tree, kanban, etc.)
- Add descriptive `string` attributes to all views

### 3. Security

- Define proper access rights in `ir.model.access.csv`
- Use record rules for fine-grained access control
- Group security definitions in `security/` directory

### 4. Embedded Views

- Add dummy fields to parent models for fields referenced in embedded views
- Use clear comments to explain dummy fields
- Consider using separate views instead of embedded views for complex cases

## Debugging Techniques

### 1. Server Logs

Enable debug logging to see detailed error messages:

```bash
--log-handler=odoo.tools.convert:DEBUG
```

### 2. Developer Mode

Enable developer mode in Odoo to access additional debugging tools:

- Technical menu
- View metadata
- Edit view architecture

### 3. Database Inspector

Use the database inspector to examine the database structure:

- Table definitions
- Field definitions
- View definitions

### 4. XML Validation

Use XML validation tools to check XML syntax:

```bash
xmllint --noout file.xml
```

## Conclusion

Developing modules for Odoo 18 requires attention to detail, particularly regarding view definitions and field references. By following the best practices and solutions outlined in this guide, you can avoid common issues and create robust, maintainable modules.
