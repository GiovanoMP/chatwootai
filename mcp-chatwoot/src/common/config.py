from dotenv import load_dotenv
import os

load_dotenv()

# MCP Configuration
MCP_TRANSPORT = os.getenv('MCP_TRANSPORT', 'sse')
MCP_PORT = int(os.getenv('MCP_PORT', 8000))
MCP_HOST = os.getenv('MCP_HOST', '0.0.0.0')

# Chatwoot API Channel Configuration
CHATWOOT_BASE_URL = os.getenv('CHATWOOT_BASE_URL', 'http://localhost:3000')
CHATWOOT_ACCESS_TOKEN = os.getenv('CHATWOOT_ACCESS_TOKEN')
CHATWOOT_HMAC_KEY = os.getenv('CHATWOOT_HMAC_KEY')  # HMAC key from API Channel settings
CHATWOOT_INBOX_IDENTIFIER = os.getenv('CHATWOOT_INBOX_IDENTIFIER')  # API Channel identifier

# MongoDB Configuration - Comentado para remover dependência
# MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
# MONGODB_DB = os.getenv('MONGODB_DB', 'chatwoot_mcp')

# Redis Configuration - Comentado para remover dependência
# REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
# REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
# REDIS_DB = int(os.getenv('REDIS_DB', 0))
# REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')

# MCP-Crew Configuration
MCP_CREW_URL = os.getenv('MCP_CREW_URL', 'http://mcp-crew:8000')
MCP_CREW_TOKEN = os.getenv('MCP_CREW_TOKEN')
