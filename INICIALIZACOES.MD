# Inicialização do Webhook, MongoDB e Mongo Express

cd mongo-config-service
./start-services.sh

Mongo Express acessível em http://localhost:8082
Usuário: admin
Senha: express_password




O webhook está na porta 8003

O MongoDB http://localhost:8081 (verificar)


# A configuração atual já usa Docker Compose com a opção restart: unless-stopped, o que significa que os contêineres serão reiniciados automaticamente se falharem ou se o host for reiniciado, a menos que sejam explicitamente parados.

Para garantir que os serviços sejam iniciados automaticamente quando o servidor for reiniciado, você pode:
sando Docker Swarm (para produção)
Para um ambiente de produção mais robusto, você pode usar Docker Swarm, que já parece estar configurado no seu VPS:



