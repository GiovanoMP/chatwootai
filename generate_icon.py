#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
import os

# Verificar se o diretório existe
icon_dir = "addons/company_services/static/description"
if not os.path.exists(icon_dir):
    os.makedirs(icon_dir)

# Criar uma imagem 128x128 com fundo verde
img = Image.new('RGB', (128, 128), color=(46, 125, 50))
d = ImageDraw.Draw(img)

# Desenhar um círculo branco no centro
d.ellipse((24, 24, 104, 104), fill=(255, 255, 255))

# Desenhar as iniciais "ES" (Empresa e Serviços) no centro
try:
    # Tentar usar uma fonte do sistema
    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 40)
except IOError:
    # Fallback para a fonte padrão
    font = ImageFont.load_default()

d.text((40, 40), "ES", fill=(46, 125, 50), font=font)

# Salvar a imagem
img.save(f"{icon_dir}/icon.png")

print(f"Ícone gerado em {icon_dir}/icon.png")
