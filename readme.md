# Products Search V2

Repositorio del Proyecto 02 de Bases de Datos II. El objetivo es construir un motor de búsqueda de productos sobre datos obtenidos de un ecommerce, integrando scraping, pipelines de procesamiento distribuido, microservicios y despliegue automatizado en Kubernetes.

## Índice rápido
- [Products Search V2](#products-search-v2)
  - [Índice rápido](#índice-rápido)
    - [Flujo general](#flujo-general)
    - [Componentes](#componentes)
    - [Pruebas unitarias](#pruebas-unitarias)
    - [Recomendaciones](#recomendaciones)
    - [Conclusiones](#conclusiones)


<details>
<summary id="datos-generales">Datos Generales del Proyecto</summary>

- **Nombre:** Products Search V2
- **Valor:** 20 % de la nota del curso
- **Modalidad:** Trabajo en equipo (máx. 5 integrantes)
- **Entrega:** Viernes 07 de noviembre 2025, 11:59 p. m.
- **Requerimientos clave:** automatización completa, documentación en Markdown, pruebas unitarias visibles, envío en repositorio + artefacto `.tar.gz`.
- **Política anti-plagio:** cualquier copia implica nota 0 y acciones disciplinarias.

</details>

<details>
<summary id="descripción-detallada">Descripción Detallada y Componentes</summary>

### Flujo general
1. Un web scraper obtiene HTML de productos desde un ecommerce y los sube a `s3://ic-tec-dataset/<grupo>/`.
2. El Controller (CronJob) monitorea el bucket, registra archivos en MongoDB (`ingestion`) y encola tareas en RabbitMQ.
3. El BeautifulSoup Parser (Deployment) procesa cada archivo, genera JSON normalizado en `raw/` y avisa a RabbitMQ.
4. El spaCy Entity Extractor (Deployment) agrega entidades NER y guarda resultados en `augmented/`.
5. El Spark Processor Job (CronJob) normaliza texto/fechas, genera descripciones cortas, relaciones entre productos y persiste en `documents` (MongoDB Atlas).
6. Atlas Search aplica un índice con facets y highlighting sobre `documents`.
7. Una REST API (Node.js en Vercel) expone endpoints hacia la UI consumiendo Atlas Search y Firestore.
8. La UI (React + Vite + Tailwind en Vercel) permite autenticación, filtrado por facets, búsqueda y navegación.

### Componentes

Cada componente se documenta con su organización en el repositorio, estructura interna principal y el flujo de ejecución.

<details>
<summary>Web Scraper (Selenium)</summary>

</details>

<details>
<summary>Controller (Kubernetes CronJob)</summary>



</details>

<details>
<summary>BeautifulSoup Parser (Deployment)</summary>


</details>

<details>
<summary>spaCy Entity Extractor (Deployment)</summary>


</details>

<details open>
<summary>Spark Processor Job (Kubernetes CronJob)</summary>

</details>

<details>
<summary>Atlas Search</summary>


</details>

<details>
<summary>REST API (Node.js en Vercel)</summary>



</details>

<details>
<summary>UI (React + Vite + Tailwind + Firestore)</summary>

</details>

</details>

<details>
<summary id="arquitectura-y-automatización">Arquitectura y Automatización</summary>

- **Infraestructura principal:** Kubernetes (Docker Desktop/Minikube), RabbitMQ, MongoDB Atlas, Firestore, Vercel.
- **Automatización:**
	- Dockerfiles para cada microservicio en `Services/docker/*`.
	- Scripts `build.ps1`, `install.ps1`, `uninstall.ps1` para orquestar imágenes y Helm Charts.
	- Helm Charts organizados en `Services/charts` para desplegar Controller, Parser, spaCy, Spark Job y dependencias.
	- Pipelines de CI/CD (configuración sugerida con GitHub Actions) para validar linting y pruebas.
- **Almacenamiento compartido:** PVC RWX montado en pods que comparten `raw/` y `augmented/`.
- **Buckets S3:** cada grupo cuenta con carpeta propia (`s3://ic-tec-dataset/<grupo>/`).
- **Servicios gestionados:**
	- MongoDB Atlas (colecciones `ingestion`, `documents`).
	- Firestore (usuarios, favoritos, sesiones).
	- RabbitMQ (colas para procesamiento y NER).

</details>

<details>
<summary id="ejecución-paso-a-paso">Ejecución Paso a Paso</summary>

1. **Preparación del scraper**
	 - Configurar variables de entorno (S3, credenciales).
	 - Ejecutar Selenium para generar HTML de productos.
	 - Sincronizar a S3: `aws s3 sync ./data s3://ic-tec-dataset/<grupo>/`.
2. **Construcción de imágenes Docker**
	 - `cd Services/docker`
	 - `./build.ps1 <dockerhub-user>` o `./build.sh <dockerhub-user>`
3. **Despliegue con Helm**
	 - `cd Services/charts`
	 - `./install.ps1` (o `./install.sh`) para instalar todos los charts.
	 - Verificar pods: `kubectl get pods`.
4. **Ejecución de pipelines**
	 - Esperar CronJobs (Controller, Spark); revisar `kubectl get jobs`.
	 - Confirmar JSON en PVC y registros en MongoDB (`ingestion`, `documents`).
5. **Atlas Search**
	 - Crear índice `default` vía Atlas (mapping personalizado  y facets/highlight).
	 - Validar búsqueda con `$search` (ver [Pruebas](#pruebas-y-validación)).
6. **REST API y UI**
	 - Deploy automático en Vercel (configurar variables de entorno: Mongo URI, Firestore, API keys).
	 - Validar endpoints (`/search`, `/auth`, `/favorites`).
	 - Acceder a la UI y probar flujo completo de búsqueda.

</details>

<details>
<summary id="pruebas-y-validación">Pruebas y Validación</summary>

### Pruebas unitarias

</details>

<details>
<summary id="estado-de-la-implementación">Estado de la Implementación</summary>

| Componente | Estado | Observaciones |
| --- | --- | --- |
| Web Scraper (Selenium) | En progreso | Definir sitio objetivo, automatizar subida a S3. |
| Controller (CronJob) | En progreso | Falta finalizar reconciliación MD5 y colas. |
| BeautifulSoup Parser | En progreso | Pipeline de parseo funcional, requiere pruebas masivas. |
| spaCy Entity Extractor | En progreso | Configurar modelo spaCy y pruebas sobre batch. |
| Spark Processor Job | Implementado parcialmente | Normalización avanzada en `Services/docker/SparkProcessorJob/app/functions.py`. |
| Atlas Search | Configurado | Índice `default` con facets/highlight pendientes de validación automática. |
| REST API (Node.js) | Pendiente | Definir endpoints y seguridad. |
| UI (React/Vite) | Pendiente | Montar diseño e integración con API. |
| Automatización Helm/Vercel | En progreso | Scripts disponibles, falta documentar pipeline CI/CD. |
| Pruebas unitarias | En progreso | Pytest para Spark, pendientes suites API/UI. |

</details>

<details>
<summary id="recomendaciones-y-conclusiones">Recomendaciones y Conclusiones</summary>

### Recomendaciones
1. Documentar y versionar los valores de Helm (`values.yaml`) junto con ejemplos de secretos dummy; esto facilita reproducir despliegues y reduce errores al incorporar nuevos miembros al equipo.
2. Incorporar un pipeline de CI que ejecute `pytest` de los componentes y validaciones de formato antes de permitir merges en `main`, garantizando calidad continua. La salida de esta tarea son las pruebas unitarias.

### Conclusiones
1. La orquestación con CronJobs y Deployments permitió desacoplar cada fase del pipeline, haciendo posible escalar módulos críticos (parser, extractor) sin impactar al resto.
2. Al centralizar la lógica de normalización en Spark y exponer los datos mediante Atlas Search, el proyecto consiguió una experiencia de búsqueda rica (facets + highlighting) sin necesidad de motores adicionales.

</details>

<details>
<summary id="referencias">Referencias</summary>

- Documentación Selenium WebDriver: https://www.selenium.dev/documentation/
- AWS CLI & S3 Sync: https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html
- Apache Spark SQL: https://spark.apache.org/sql/
- spaCy NER: https://spacy.io/usage/linguistic-features#named-entities
- MongoDB Atlas Search: https://www.mongodb.com/docs/atlas/atlas-search/
- RabbitMQ Tutorials: https://www.rabbitmq.com/getstarted.html
- Vercel Docs: https://vercel.com/docs
- TailwindCSS: https://tailwindcss.com/docs

</details>
