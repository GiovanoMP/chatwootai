FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Criar diretório para arquivos estáticos
RUN mkdir -p static/css

# Gerar CSS para Pygments
RUN pygmentize -S default -f html -a .highlight > static/css/pygments.css

# Definir variáveis de ambiente
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0
ENV SECRET_KEY=change_this_in_production
ENV ADMIN_PASSWORD=Config@Viewer2025!

EXPOSE 8080

CMD ["python", "app.py"]
