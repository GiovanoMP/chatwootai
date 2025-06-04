// Criar usuário para o banco de dados
db.createUser({
  user: 'mcp_user',
  pwd: 'mcp_password',
  roles: [
    { role: 'readWrite', db: 'mcp_database' }
  ]
});

// Criar banco de dados e coleções iniciais
db = db.getSiblingDB('mcp_database');
db.createCollection('tenants');
db.createCollection('crews');
db.createCollection('agents');
db.createCollection('contexts');
