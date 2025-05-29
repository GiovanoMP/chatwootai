// MCP-MongoDB Server
// Implementação simplificada usando Express.js

const express = require('express');
const cors = require('cors');
const { MongoClient } = require('mongodb');
const dotenv = require('dotenv');

dotenv.config();

// Configurações
const MONGODB_URI = process.env.MONGODB_URI || "mongodb://localhost:27017/config_service";
const PORT = parseInt(process.env.PORT || "8000", 10);
const MULTI_TENANT = process.env.MULTI_TENANT === "true";
const DEFAULT_TENANT = process.env.DEFAULT_TENANT || "account_1";
const MAX_RESULTS = parseInt(process.env.MAX_RESULTS || "100", 10);
const ALLOWED_COLLECTIONS = (process.env.ALLOWED_COLLECTIONS || "company_services,tenants,configurations").split(",");

console.log(`Starting MCP-MongoDB with config:
- Multi-tenant mode: ${MULTI_TENANT}
- Default tenant: ${DEFAULT_TENANT}
- Max results: ${MAX_RESULTS}
- Allowed collections: ${ALLOWED_COLLECTIONS.join(", ")}
- MongoDB URI: ${MONGODB_URI}
`);

// Inicializar Express
const app = express();

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Log de requisições
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
  next();
});

// Cliente MongoDB
let client;
let db;

// Conectar ao MongoDB
async function connectToMongoDB() {
  try {
    console.log(`Connecting to MongoDB: ${MONGODB_URI}`);
    client = new MongoClient(MONGODB_URI);
    await client.connect();
    db = client.db();
    console.log("Connected to MongoDB successfully");
    return true;
  } catch (error) {
    console.error("Failed to connect to MongoDB:", error);
    return false;
  }
}

// Middleware para verificar se a coleção é permitida
function checkAllowedCollection(req, res, next) {
  const collection = req.params.collection;
  if (!ALLOWED_COLLECTIONS.includes(collection)) {
    return res.status(403).json({ error: `Collection '${collection}' is not allowed` });
  }
  next();
}

// Sanitizar documento (remover campos sensíveis)
function sanitizeDocument(doc) {
  if (!doc) return doc;
  
  const sanitized = { ...doc };
  delete sanitized.password;
  delete sanitized.security_token;
  return sanitized;
}

// Endpoints MCP
// 1. Endpoint de saúde
app.get('/health', async (req, res) => {
  try {
    if (!db) {
      return res.status(500).json({ status: 'unhealthy', error: 'MongoDB not connected' });
    }
    
    await db.admin().command({ ping: 1 });
    res.json({ 
      status: 'healthy', 
      mongodb: 'connected',
      multi_tenant: MULTI_TENANT,
      default_tenant: DEFAULT_TENANT
    });
  } catch (error) {
    console.error(`Health check error: ${error}`);
    res.status(500).json({ status: 'unhealthy', error: String(error) });
  }
});

// 2. Listar recursos (coleções)
app.get('/resources', async (req, res) => {
  try {
    const tenant_id = req.query.tenant_id || DEFAULT_TENANT;
    
    const collections = await db.listCollections().toArray();
    const filteredCollections = collections
      .filter(col => ALLOWED_COLLECTIONS.includes(col.name))
      .map(collection => ({
        uri: `mcp-mongodb://${tenant_id}/${collection.name}`,
        name: collection.name,
        description: `MongoDB collection: ${collection.name} (tenant: ${tenant_id})`,
      }));
    
    res.json({ resources: filteredCollections });
  } catch (error) {
    console.error(`Error listing resources: ${error}`);
    res.status(500).json({ error: String(error) });
  }
});

// 3. Obter esquema de coleção
app.get('/resources/:tenant_id/:collection', checkAllowedCollection, async (req, res) => {
  try {
    const { tenant_id, collection } = req.params;
    
    // Aplicar filtro de tenant para multi-tenant
    const filter = MULTI_TENANT ? { tenant_id } : {};
    
    // Obter um documento de amostra
    const sampleDoc = await db.collection(collection).findOne(filter);
    
    if (!sampleDoc) {
      return res.status(404).json({ 
        message: `No documents found for tenant ${tenant_id} in collection ${collection}` 
      });
    }

    // Sanitizar documento
    const sanitizedDoc = sanitizeDocument(sampleDoc);
    
    res.json({
      collection: collection,
      tenant_id: tenant_id,
      sample_document: sanitizedDoc,
      fields: Object.keys(sanitizedDoc).map(key => ({
        name: key,
        type: typeof sanitizedDoc[key],
      })),
    });
  } catch (error) {
    console.error(`Error getting collection schema: ${error}`);
    res.status(500).json({ error: String(error) });
  }
});

// 4. Listar ferramentas disponíveis
app.get('/tools', (req, res) => {
  res.json({
    tools: [
      {
        name: "query",
        description: "Query documents from a MongoDB collection with tenant isolation",
        parameters: {
          collection: {
            type: "string",
            description: "Name of the collection to query",
          },
          tenant_id: {
            type: "string",
            description: "Tenant ID for multi-tenant filtering (default: account_1)",
          },
          filter: {
            type: "object",
            description: "MongoDB query filter",
          },
          projection: {
            type: "object",
            description: "Fields to include or exclude",
          },
          limit: {
            type: "number",
            description: `Maximum number of results to return (max: ${MAX_RESULTS})`,
          },
          skip: {
            type: "number",
            description: "Number of documents to skip",
          },
          sort: {
            type: "object",
            description: "Sort criteria",
          },
        },
      },
      {
        name: "aggregate",
        description: "Run an aggregation pipeline on a MongoDB collection with tenant isolation",
        parameters: {
          collection: {
            type: "string",
            description: "Name of the collection to aggregate",
          },
          tenant_id: {
            type: "string",
            description: "Tenant ID for multi-tenant filtering (default: account_1)",
          },
          pipeline: {
            type: "array",
            description: "MongoDB aggregation pipeline",
          },
        },
      },
      {
        name: "getCompanyConfig",
        description: "Get company configuration for a specific tenant",
        parameters: {
          tenant_id: {
            type: "string",
            description: "Tenant ID to retrieve company configuration",
          },
        },
      },
    ],
  });
});

// 5. Executar ferramenta: query
app.post('/tools/query', async (req, res) => {
  try {
    const { 
      collection, 
      tenant_id = DEFAULT_TENANT, 
      filter = {}, 
      projection = {}, 
      limit = 10, 
      skip = 0, 
      sort = { _id: 1 } 
    } = req.body;

    // Verificar se a coleção é permitida
    if (!ALLOWED_COLLECTIONS.includes(collection)) {
      return res.status(403).json({ error: `Collection '${collection}' is not allowed` });
    }

    // Aplicar limite de segurança
    const safeLimit = Math.min(limit, MAX_RESULTS);
    
    // Aplicar filtro de tenant para multi-tenant
    const tenantFilter = MULTI_TENANT ? 
      { ...filter, tenant_id } : 
      filter;
    
    console.log(`Executing query on ${collection} for tenant ${tenant_id}:`, tenantFilter);
    
    const result = await db
      .collection(collection)
      .find(tenantFilter, { projection })
      .sort(sort)
      .skip(skip)
      .limit(safeLimit)
      .toArray();

    // Sanitizar resultados
    const sanitizedResult = result.map(doc => sanitizeDocument(doc));

    res.json({
      tenant_id,
      collection,
      count: sanitizedResult.length,
      results: sanitizedResult
    });
  } catch (error) {
    console.error(`Error executing query: ${error}`);
    res.status(500).json({ error: String(error) });
  }
});

// 6. Executar ferramenta: aggregate
app.post('/tools/aggregate', async (req, res) => {
  try {
    const { 
      collection, 
      tenant_id = DEFAULT_TENANT, 
      pipeline = []
    } = req.body;

    // Verificar se a coleção é permitida
    if (!ALLOWED_COLLECTIONS.includes(collection)) {
      return res.status(403).json({ error: `Collection '${collection}' is not allowed` });
    }
    
    // Modificar o pipeline para incluir filtro de tenant para multi-tenant
    let safePipeline = [...pipeline];
    
    if (MULTI_TENANT) {
      // Adicionar match por tenant_id no início do pipeline
      safePipeline.unshift({ $match: { tenant_id } });
    }
    
    console.log(`Executing aggregation on ${collection} for tenant ${tenant_id}:`, safePipeline);
    
    const result = await db
      .collection(collection)
      .aggregate(safePipeline, { 
        allowDiskUse: true,
        maxTimeMS: 5000
      })
      .toArray();

    // Sanitizar resultados
    const sanitizedResult = result.map(doc => sanitizeDocument(doc));

    res.json({
      tenant_id,
      collection,
      count: sanitizedResult.length,
      results: sanitizedResult
    });
  } catch (error) {
    console.error(`Error executing aggregation: ${error}`);
    res.status(500).json({ error: String(error) });
  }
});

// 7. Executar ferramenta: getCompanyConfig
app.post('/tools/getCompanyConfig', async (req, res) => {
  try {
    const { tenant_id } = req.body;
    
    if (!tenant_id) {
      return res.status(400).json({ error: "tenant_id is required" });
    }
    
    console.log(`Getting company config for tenant ${tenant_id}`);
    
    // Buscar configuração da empresa na coleção company_services
    const companyConfig = await db
      .collection('company_services')
      .findOne({ account_id: tenant_id });

    if (!companyConfig) {
      return res.status(404).json({ 
        error: `No company configuration found for tenant ${tenant_id}` 
      });
    }

    // Sanitizar configuração
    const sanitizedConfig = sanitizeDocument(companyConfig);
    
    res.json(sanitizedConfig);
  } catch (error) {
    console.error(`Error getting company config: ${error}`);
    res.status(500).json({ error: String(error) });
  }
});

// Iniciar servidor
async function startServer() {
  const connected = await connectToMongoDB();
  
  if (!connected) {
    console.error("Failed to connect to MongoDB. Exiting...");
    process.exit(1);
  }
  
  app.listen(PORT, () => {
    console.log(`MCP-MongoDB server running on port ${PORT}`);
  });
  
  // Lidar com encerramento
  process.on('SIGINT', async () => {
    console.log("Shutting down MongoDB MCP server...");
    if (client) {
      await client.close();
      console.log("MongoDB connection closed");
    }
    process.exit(0);
  });
  
  process.on('SIGTERM', async () => {
    console.log("Shutting down MongoDB MCP server...");
    if (client) {
      await client.close();
      console.log("MongoDB connection closed");
    }
    process.exit(0);
  });
}

startServer().catch(error => {
  console.error("Fatal error:", error);
  process.exit(1);
});
