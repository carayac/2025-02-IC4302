# Documentación de Imágenes y Configuración en `values.yaml`

Este proyecto soporta diferentes imágenes de base de datos y variantes con Memcached o Redis como mecanismos de cache.  
El cambio de imagen se realiza modificando el archivo `values.yaml` en la sección correspondiente al despliegue de la API.

---

## Imágenes Disponibles

###  ChromaDB
- usuario/chroma
- usuario/chroma-memcached
- usuario/chroma-redis

###  Elasticsearch
- usuario/elasticsearch
- usuario/elasticsearch-memcached
- usuario/elasticsearch-redis

### MariaDB
- usuario/mariadb
- usuario/mariadb-memcached
- usuario/mariadb-redis

### PostgreSQL
- usuario/postgresql
- usuario/postgresql-memcached
- usuario/postgresql-redis

> **Nota:** Reemplaza `usuario` por tu nombre de usuario en DockerHub (ejemplo: `mydockeruser/mariadb`).

---

## Configuración en `values.yaml`

En el archivo `values.yaml`, se define la imagen que utilizará el despliegue.  
La sección típica es la siguiente:

```yaml
config:
  flask:
    enabled: true
    name: flasktest
    replicas: 10
    image: usuario/imagen
```

### Ejemplo: Usar ChromaDB con Memcached
```yaml
config:
  flask:
    enabled: true
    name: flasktest
    replicas: 10
    image: usuario/chroma-memcached
```
---

---

## Recomendacion
- Mantener consistencia en los nombres: `servicio-cache` (`-memcached`, `-redis`).