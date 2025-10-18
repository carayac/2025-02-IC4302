# backend/app/metrics.py
from prometheus_client import Counter, Histogram, CollectorRegistry

# Registry global
REGISTRY = CollectorRegistry()

# Contadores y histogramas usando el registry global
tiempo_procesamiento_api = Histogram(
    "api_tiempo_procesamiento_segundos",
    "Tiempo de procesamiento de requests en API", 
    ["componente", "endpoint"],
    registry=REGISTRY  # << importante
)

peticiones_endpoint_api = Counter(
    "api_total_peticiones_endpoint",
    "Total de peticiones por endpoint en API",
    ["componente", "endpoint"],
    registry=REGISTRY  # << importante
)

# CONSTANTES
COMPONENT = "api"