// Criar usuário para o banco de dados config_service
db = db.getSiblingDB('config_service');

db.createUser({
  user: 'config_user',
  pwd: 'config_password',
  roles: [
    { role: 'readWrite', db: 'config_service' }
  ]
});

// Criar coleções
db.createCollection('tenants');
db.createCollection('configurations');

// Criar índices
db.tenants.createIndex({ "account_id": 1 }, { unique: true });
db.configurations.createIndex({ "account_id": 1 });
db.configurations.createIndex({ "account_id": 1, "version": 1 });

// Inserir um documento de exemplo para teste
db.tenants.insertOne({
  account_id: "account_1",
  name: "Empresa Exemplo",
  created_at: new Date(),
  updated_at: new Date(),
  enabled_modules: ["company_info", "service_settings", "enabled_services", "mcp", "channels"]
});

// Inserir uma configuração de exemplo
db.configurations.insertOne({
  account_id: "account_1",
  security_token: "abc123",
  name: "Empresa Exemplo",
  description: "Descrição da empresa exemplo",
  version: 1,
  updated_at: new Date(),
  enabled_modules: ["company_info", "service_settings", "enabled_services", "mcp", "channels"],
  modules: {
    company_info: {
      name: "Empresa Exemplo",
      description: "Descrição da empresa exemplo",
      address: {
        street: "Rua Exemplo, 123",
        street2: "Sala 456",
        city: "Cidade Exemplo",
        state: "Estado Exemplo",
        zip: "12345-678",
        country: "Brasil",
        share_with_customers: true
      }
    },
    service_settings: {
      business_hours: {
        days: {
          monday: { open: true, start: "08:00", end: "18:00" },
          tuesday: { open: true, start: "08:00", end: "18:00" },
          wednesday: { open: true, start: "08:00", end: "18:00" },
          thursday: { open: true, start: "08:00", end: "18:00" },
          friday: { open: true, start: "08:00", end: "18:00" },
          saturday: { open: true, start: "09:00", end: "13:00" },
          sunday: { open: false }
        },
        lunch_break: {
          enabled: true,
          start: "12:00",
          end: "13:00"
        }
      },
      greeting_message: "Olá! Como posso ajudar você hoje?",
      farewell_message: "Obrigado por entrar em contato. Tenha um ótimo dia!",
      allow_mention_website: true,
      request_rating: true,
      rating_message: "Como você avaliaria nosso atendimento hoje?"
    },
    enabled_services: {
      collections: ["products_informations", "scheduling_rules", "support_documents"],
      services: {
        sales: {
          enabled: true,
          promotions: {
            inform_at_start: true
          }
        },
        scheduling: {
          enabled: true
        },
        delivery: {
          enabled: false
        },
        support: {
          enabled: true
        }
      }
    },
    mcp: {
      type: "odoo",
      version: "14.0",
      connection: {
        url: "http://localhost:8069",
        database: "account_1",
        username: "admin",
        password_ref: "account_1_db_pwd",
        access_level: "read"
      }
    },
    channels: {
      whatsapp: {
        enabled: true,
        services: ["sales", "scheduling", "support"]
      }
    }
  }
});
