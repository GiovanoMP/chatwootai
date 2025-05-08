#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Proxy para simulação de WhatsApp.

Este script serve como um proxy entre o simulador de WhatsApp e o sistema.
Ele encaminha as mensagens do simulador para o sistema e captura as respostas
para exibi-las no simulador.
"""

import os
import sys
import json
import time
import logging
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from urllib.parse import parse_qs
import threading
import webbrowser

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configurações padrão
DEFAULT_PROXY_PORT = 8080
DEFAULT_SYSTEM_URL = "http://localhost:8001/webhook"
DEFAULT_CONVERSATION_ID = 4
DEFAULT_CONTACT_ID = 3

# Armazenamento de mensagens
message_store = {
    "last_message_id": 0,
    "messages": []
}

class WhatsAppProxyHandler(BaseHTTPRequestHandler):
    """Handler para o servidor proxy."""

    def _set_headers(self, content_type="application/json"):
        self.send_response(200)
        self.send_header("Content-type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Requested-With")
        self.end_headers()

    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS."""
        self._set_headers()

    def do_GET(self):
        """Handle GET requests."""
        logger.info(f"Recebida requisição GET para: {self.path}")

        if self.path == "/simulator" or self.path == "/":
            # Servir a página do simulador
            self._serve_simulator()
        elif self.path == "/whatsapp_simulator.js":
            # Servir o arquivo JavaScript
            try:
                with open("whatsapp_simulator.js", "r") as f:
                    content = f.read()
                self._set_headers("application/javascript")
                self.wfile.write(content.encode())
            except FileNotFoundError:
                logger.error("Arquivo JavaScript não encontrado")
                self._set_headers("text/html")
                self.wfile.write(b"JavaScript file not found")
        elif self.path.startswith("/messages"):
            # Retornar mensagens armazenadas
            self._get_messages()
        else:
            self._set_headers("text/html")
            self.wfile.write(b"WhatsApp Proxy Server")

    def do_POST(self):
        """Handle POST requests."""
        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)

            logger.info(f"Recebida requisição POST para: {self.path}")

            if self.path.startswith("/webhook"):
                # Encaminhar webhook para o sistema
                logger.info("Encaminhando para o endpoint webhook")
                self._forward_webhook(post_data)
            elif self.path.startswith("/response"):
                # Receber resposta do sistema
                logger.info("Processando resposta do sistema")
                self._receive_response(post_data)
            else:
                logger.warning(f"Endpoint desconhecido: {self.path}")
                self._set_headers()
                self.wfile.write(json.dumps({"status": "error", "message": "Unknown endpoint"}).encode())
        except Exception as e:
            logger.error(f"Erro ao processar requisição POST: {str(e)}")
            self._set_headers()
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())

    def _serve_simulator(self):
        """Serve the simulator HTML page."""
        try:
            with open("whatsapp_simulator.html", "r") as f:
                content = f.read()

            self._set_headers("text/html")
            self.wfile.write(content.encode())
        except FileNotFoundError:
            self._set_headers("text/html")
            self.wfile.write(b"Simulator HTML file not found")

    def _get_messages(self):
        """Return stored messages."""
        self._set_headers()
        self.wfile.write(json.dumps(message_store).encode())

    def _forward_webhook(self, post_data):
        """Forward webhook to the system."""
        try:
            # Parse webhook data
            webhook_data = json.loads(post_data)

            # Log the webhook
            account_id = webhook_data.get("account", {}).get("id", "N/A")
            logger.info(f"Recebido webhook: {webhook_data.get('event')} - Account ID: {account_id} - Mensagem: {webhook_data.get('content')}")

            # Store the message
            message_id = webhook_data.get("id", message_store["last_message_id"] + 1)
            message_store["last_message_id"] = message_id
            message_store["messages"].append({
                "id": message_id,
                "content": webhook_data.get("content"),
                "sender": "user",
                "account_id": account_id,
                "timestamp": time.time()
            })

            # Forward to the system
            system_url = self.server.system_url
            logger.info(f"Encaminhando webhook para: {system_url}")

            response = requests.post(
                system_url,
                headers={"Content-Type": "application/json"},
                data=post_data
            )

            # Return the response
            self._set_headers()
            self.wfile.write(response.content)

            # Start a thread to monitor for responses
            threading.Thread(target=self._monitor_for_responses,
                            args=(webhook_data.get("conversation", {}).get("id"),)).start()

        except Exception as e:
            logger.error(f"Erro ao encaminhar webhook: {str(e)}")
            self._set_headers()
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())

    def _receive_response(self, post_data):
        """Receive response from the system."""
        try:
            # Parse response data
            response_data = json.loads(post_data)

            # Log the response
            logger.info(f"Recebida resposta: {response_data.get('content')}")

            # Store the message
            message_id = message_store["last_message_id"] + 1
            message_store["last_message_id"] = message_id
            message_store["messages"].append({
                "id": message_id,
                "content": response_data.get("content"),
                "sender": "bot",
                "timestamp": time.time()
            })

            # Return success
            self._set_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode())

        except Exception as e:
            logger.error(f"Erro ao receber resposta: {str(e)}")
            self._set_headers()
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())

    def _monitor_for_responses(self, conversation_id):
        """Monitor for responses from the system by checking logs."""
        if not conversation_id:
            logger.warning("ID da conversa não fornecido, não é possível monitorar respostas")
            return

        logger.info(f"Monitorando respostas para a conversa {conversation_id}")

        # Monitorar por até 30 segundos (6 tentativas de 5 segundos)
        for attempt in range(6):
            # Wait a bit for the system to process
            time.sleep(5)
            logger.info(f"Verificando respostas (tentativa {attempt+1}/6)...")

            # Check the logs for responses
            try:
                # Verificar logs do Chatwoot Client
                self._check_chatwoot_client_logs(conversation_id)

                # Verificar logs do servidor
                self._check_server_logs(conversation_id)

            except Exception as e:
                logger.error(f"Erro ao monitorar respostas: {str(e)}")

        logger.info("Monitoramento de respostas concluído após 30 segundos")

    def _check_chatwoot_client_logs(self, conversation_id):
        """Check Chatwoot client logs for responses."""
        log_file = "logs/chatwoot_client.log"
        if not os.path.exists(log_file):
            logger.warning(f"Arquivo de log {log_file} não encontrado")
            return

        with open(log_file, "r") as f:
            # Get the last few lines
            lines = f.readlines()[-100:]  # Aumentado para 100 linhas

            # Look for successful responses
            for line in reversed(lines):
                if "Response status: 200" in line and "Request data" in "".join(lines[-20:]):  # Aumentado para 20 linhas
                    # Find the request data
                    for i in range(20):  # Aumentado para 20 linhas
                        if i >= len(lines):
                            break
                        if "Request data" in lines[-i-1]:
                            try:
                                # Extract the content from the request data
                                data_line = lines[-i-1]
                                data_start = data_line.find("{")
                                if data_start >= 0:
                                    data_str = data_line[data_start:]
                                    data = json.loads(data_str)
                                    content = data.get("content")

                                    if content:
                                        logger.info(f"Encontrada resposta nos logs do Chatwoot Client: {content[:50]}...")

                                        # Add to message store
                                        message_id = message_store["last_message_id"] + 1
                                        message_store["last_message_id"] = message_id
                                        message_store["messages"].append({
                                            "id": message_id,
                                            "content": content,
                                            "sender": "bot",
                                            "timestamp": time.time()
                                        })
                                        return True
                            except Exception as e:
                                logger.error(f"Erro ao extrair conteúdo da resposta: {str(e)}")
                            break

        return False

    def _check_server_logs(self, conversation_id):
        """Check server logs for responses."""
        log_files = ["logs/server.log", "logs/webhook.log"]

        for log_file in log_files:
            if not os.path.exists(log_file):
                logger.warning(f"Arquivo de log {log_file} não encontrado")
                continue

            with open(log_file, "r") as f:
                # Get the last few lines
                lines = f.readlines()[-300:]  # Aumentado para 300 linhas

                # Look for responses in the logs
                for i, line in enumerate(reversed(lines)):
                    # Procurar por padrões que indicam uma resposta
                    if "Resposta enviada para Chatwoot:" in line or "Resposta enviada para conversa" in line or "Enviando resposta" in line or "Mensagem enviada" in line:
                        try:
                            # Extrair o conteúdo da resposta
                            if "Resposta enviada para Chatwoot:" in line:
                                # Formato: "Resposta enviada para Chatwoot: [conteúdo]"
                                content_start = line.find("Resposta enviada para Chatwoot:") + len("Resposta enviada para Chatwoot:")
                                content = line[content_start:].strip()

                                # Se a resposta continua nas próximas linhas
                                next_lines = []
                                for j in range(1, 10):  # Verificar até 10 linhas seguintes
                                    if i+j < len(lines):
                                        next_line = lines[-(i+j+1)].strip()
                                        if next_line.startswith("[WEBHOOK]"):
                                            next_line = next_line[len("[WEBHOOK]"):].strip()
                                        if next_line and not next_line.startswith("2025-") and not "INFO" in next_line:
                                            next_lines.append(next_line)
                                        else:
                                            break

                                if next_lines:
                                    content += "\n" + "\n".join(next_lines)

                                logger.info(f"Encontrada resposta nos logs (Chatwoot): {content[:50]}...")

                                # Add to message store
                                message_id = message_store["last_message_id"] + 1
                                message_store["last_message_id"] = message_id
                                message_store["messages"].append({
                                    "id": message_id,
                                    "content": content,
                                    "sender": "bot",
                                    "timestamp": time.time()
                                })
                                return True

                            # Verificar outros padrões de resposta
                            elif "Resposta enviada para conversa" in line:
                                # Tentar encontrar a resposta nas linhas seguintes
                                for j in range(1, 20):  # Verificar até 20 linhas seguintes
                                    if i+j < len(lines):
                                        next_line = lines[-(i+j+1)]
                                        if "content" in next_line or "mensagem" in next_line.lower():
                                            # Extrair conteúdo
                                            content_start = next_line.find(":") + 1
                                            content = next_line[content_start:].strip()

                                            logger.info(f"Encontrada resposta nos logs (conversa): {content[:50]}...")

                                            # Add to message store
                                            message_id = message_store["last_message_id"] + 1
                                            message_store["last_message_id"] = message_id
                                            message_store["messages"].append({
                                                "id": message_id,
                                                "content": content,
                                                "sender": "bot",
                                                "timestamp": time.time()
                                            })
                                            return True
                        except Exception as e:
                            logger.error(f"Erro ao extrair conteúdo da resposta: {str(e)}")

                    # Procurar por padrões alternativos
                    elif "has_response\": true" in line or "Enviando mensagem para Chatwoot" in line or "message_type\": \"outgoing\"" in line or "\"content\":" in line:
                        try:
                            # Procurar a mensagem nas linhas próximas
                            for j in range(-5, 20):  # Verificar 5 linhas anteriores e 20 seguintes
                                if i+j >= 0 and i+j < len(lines):
                                    check_line = lines[-(i+j+1)]
                                    if "content" in check_line and ":" in check_line:
                                        content_start = check_line.find("content") + 10
                                        content_end = check_line.find("\",", content_start)
                                        if content_end > content_start:
                                            content = check_line[content_start:content_end].strip()

                                            logger.info(f"Encontrada resposta nos logs (content): {content[:50]}...")

                                            # Add to message store
                                            message_id = message_store["last_message_id"] + 1
                                            message_store["last_message_id"] = message_id
                                            message_store["messages"].append({
                                                "id": message_id,
                                                "content": content,
                                                "sender": "bot",
                                                "timestamp": time.time()
                                            })
                                            return True
                        except Exception as e:
                            logger.error(f"Erro ao extrair conteúdo alternativo: {str(e)}")

        # Verificar o arquivo last_webhook_payload.json se existir
        try:
            if os.path.exists('logs/last_webhook_payload.json'):
                with open('logs/last_webhook_payload.json', 'r') as f:
                    data = json.load(f)
                    if data.get('content'):
                        content = data.get('content')
                        logger.info(f"Encontrada resposta no arquivo last_webhook_payload.json: {content[:50]}...")

                        # Add to message store
                        message_id = message_store["last_message_id"] + 1
                        message_store["last_message_id"] = message_id
                        message_store["messages"].append({
                            "id": message_id,
                            "content": content,
                            "sender": "bot",
                            "timestamp": time.time()
                        })
                        return True
        except Exception as e:
            logger.error(f"Erro ao verificar last_webhook_payload.json: {str(e)}")

        return False


def run_server(port=DEFAULT_PROXY_PORT, system_url=DEFAULT_SYSTEM_URL):
    """Run the proxy server."""
    server_address = ("", port)
    httpd = HTTPServer(server_address, WhatsAppProxyHandler)
    httpd.system_url = system_url

    logger.info(f"Iniciando servidor proxy na porta {port}")
    logger.info(f"Encaminhando webhooks para {system_url}")
    logger.info(f"Acesse o simulador em http://localhost:{port}/simulator")

    # Open the simulator in the browser
    webbrowser.open(f"http://localhost:{port}/simulator")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Servidor encerrado")
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Proxy para simulação de WhatsApp")
    parser.add_argument("--port", type=int, default=DEFAULT_PROXY_PORT,
                        help=f"Porta do servidor proxy (default: {DEFAULT_PROXY_PORT})")
    parser.add_argument("--system-url", type=str, default=DEFAULT_SYSTEM_URL,
                        help=f"URL do sistema (default: {DEFAULT_SYSTEM_URL})")

    args = parser.parse_args()

    run_server(args.port, args.system_url)
