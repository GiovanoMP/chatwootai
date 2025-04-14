from setuptools import setup, find_packages

setup(
    name="odoo_api",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "httpx",
        "pydantic",
        "redis",
        "qdrant-client",
        "openai",
        "python-dotenv",
        "tenacity",
        "PyYAML"
    ],
)
