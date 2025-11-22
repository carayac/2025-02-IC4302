# IC4302 - Tarea Corta 02

**Curso:** Bases de Datos II (IC4302)  
**Semestre:** Segundo Semestre 2025  
**Institución:** Tecnológico de Costa Rica – Escuela de Ingeniería en Computación  

### VIDEO INFORMATIVO

# Instrucciones de Ejecución
  
<details>
  <summary>Desplegar información</summary>



</details>


# Pruebas Unitarias
  
<details>
  <summary>Desplegar información</summary> 



</details>


# Configuración de componentes 
<details>
  <summary>Desplegar información</summary>  

## Elasticsearch  

<details>
  <summary>Desplegar información</summary>  

Para el desarrollo completo al realizar backups y restauraciones de indices en Elasticsearch se utiliza el servicio de Kibana y utilizando su robusta configuracion de Snapshot y Restore  


### Backup  

### Configuración del snapshot repository  

Para realizar todo el procedimiento es necesario crear un Snapshot Repository, el cual es una ubicación externa donde elasticsearch puede crear y almacenar respaldos de sus indices, para poder crearlo solo debe ingresar al servicio de kibana (implementado en este proyecto) por el cual se puede interactuar con elasticsearch.  En kibana ---> Stack Management ---> Snapshot y Restore ---> Repositories ---> Register repositories .  Este repositorio incluye distintos parametros, para el caso de esta tarea, se deben ingresar los siguientes:

| Parámetro | Valor |
|----------|-------------|
| name | elastic |
| provider | AWS |
| bucketName | ic-tec-dataset |
| base_path | CARPETA_HCDCP_BACKUP/elastic |  

### Configuración de la política  

Una vez creado el repositorio es necesario crear una política que permite ejecutar un snapshot de forma automática cada cierto tiempo y así automatizar los backups, aqui unicamnete debe completar campos del repositorio ya creado.  

| Parámetro | Valor |
|----------|-------------|
| name | elastic |
| snapshotName | elastic |
| repository | elastic (nombre del snapshot repository creado |  

**¿Cómo ejecutar el backup?**  

Para ejecutar el snapshot que generará el backup, puede esperar a que se ejcute segun el horario que fue asignado o bien puede ejecutarlo manualmente en Kibana ---> Stack Management ---> policies y justo en la columna de actions solicita la ejecución forzadaa con el botón de run.  
Una vez ejecutado el policy, el backup empezará y podrá coprobarlo al ver una nueva carpeta dentro del prefijo especificado dentro del bucket, o bien puede ingresar a las Dev Tools de elastic y ejecutar:  

```powershell
GET _snapshot/elastic/_all
```

Donde en el resulatdo se observa cierta data que permite confirmar que el proceso fue exitoso, ya que se puede ver que parte de los indices subidos corresponde a **animals**, dataset utilizado para probar los backups

```json
{
  "snapshots": [
    {
      "snapshot": "elastic-j4wjad6lsh21ww2t5mtktw",
      "repository": "elastic",
      "version_id": 8060199,
      "indices": [
        ".kibana_security_session_1",
        ".security-7",
        ".apm-agent-configuration",
        ".kibana_8.6.1_001",
        ".apm-custom-link",
        ".ds-ilm-history-5-2025.11.21-000001",
        ".geoip_databases",
        "animals",
        ".security-profile-8",
        ".kibana-event-log-8.6.1-000001",
        ".ds-.logs-deprecation.elasticsearch-default-2025.11.21-000001",
        ".kibana_task_manager_8.6.1_001"
      ],
      "metadata": {
        "policy": "elastic"
      },
      "state": "SUCCESS",
```


### Restauración  

Antes de realizar el proceso para hacer la restauración de indices es importante mencionar que Elasticsearch **NO** permite restaurar un índice si este ya existe o está abierto, es por esta razón que para probar la restauración es necesario eliminar el indice `animals` antes de ejecutar el restore, utilizando este comando en la consola de Dev-Tools se puede realizar la eliminación:  

```powershell
DELETE animals
```

Una vez realizado esto puede dirigirse a Stack Management ---> Snapshot y Restore ---> Snapshots y justo en la columna de Actions seleccionar la opción `Restore`.  También es importante mencionar que al eleiminar unicamnete el indice animals, podremos hacer restore de unicamnete ese indice ya que los demás son los creados por el sistema y decidimos mejor no tocarlos, por esta razón, al selección esta opcion de restore, debe ajustar la configuración para que solo se haga restore del indice creado por el usuario, en este caso `animals` de esta manera:  

<img width="922" height="230" alt="Captura de pantalla 2025-11-21 200911" src="https://github.com/user-attachments/assets/fff3c858-49c8-4b89-a1de-2355b59b7fc4" />


Una vez realzado esto puede ejecutar el snapshot completo y verificar que el indice vuelve a ser creado


  </details>


</details>


# Conclusiones
  
<details>
  <summary>Desplegar información</summary> 

1. El proceso de realizar backups y restores con Elasticsearch evidencia que el proceso que tienen de snapshots y restore es bastante robusto y bastante facil de utilizar, es decir no deja de ser seguro para los momentos en los que la disponibilidad de los datos juega un papel critico.
2. 

</details>

# Recomendaciones
  
<details>
  <summary>Desplegar información</summary> 

1. Ya que elasticsearch funciona con índices que cambian de manera dinámica es bastante ventajoso apoyarse de snapshots automáticos mediante politicas que se adecuen a las necesidades del negocio y así evitar fallo o algun borrado accidental.
2. 

</details>

# Referencias
  
<details>
  <summary>Desplegar información</summary> 


</details>

# Tabla de Estado
  
<details>
  <summary>Desplegar información</summary>  


| Componente / Requerimiento | % Evaluación | Estado |
|----------------------------|--------------|--------|
| **MariaDB – Backup/Restore** | 10% | Implementado |
| **PostgreSQL – Backup/Restore** | 10% | Implementado |
| **MongoDB – Backup/Restore** | 10% |Implementado | 
| **Neo4J – Backup/Restore** | 10% | Implementado | 
| **CouchDB – Backup/Restore** | 10% | Implementado | 
| **Elasticsearch – Backup/Restore** | 10% | Implementado | 
| **OpenSearch – Backup/Restore** | 10% | Implementado | 




</details>
