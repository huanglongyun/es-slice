import os

ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
ES_USER = os.getenv("ES_USER", "")
ES_PASS = os.getenv("ES_PASS", "")
ES_TIMEOUT = int(os.getenv("ES_TIMEOUT", "30"))
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8081"))
