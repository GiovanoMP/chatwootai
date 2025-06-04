db = db.getSiblingDB('config_service');

db.createUser({
  user: 'config_user',
  pwd: 'config_password',
  roles: [{ role: 'readWrite', db: 'config_service' }]
});

// Criar coleções iniciais
db.createCollection('company_services');
db.createCollection('tenants');
db.createCollection('configurations');

// Inserir dados iniciais
db.tenants.insertOne({
  account_id: 'account_1',
  name: 'Tenant Padrão',
  active: true,
  created_at: new Date()
});
