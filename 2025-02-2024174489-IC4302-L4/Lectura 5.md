# Observabilidad

## 1. Identifique y comente 5 factores que afectan el rendimineto de la base de datos

### **Query Optimization:**
El rendimiento depende de cómo el motor genera el execution plan. Si las estadísticas no están bien o se eligen estrategias de acceso ineficientes, la consulta será más lenta.

### **Query Execution:**
El uso de locks para garantizar la atomicidad puede bloquear otras consultas, especialmente si hay malas prácticas en el manejo de transacciones, lo que afecta el rendimiento.

### **Execution Plans:**
Analizar los execution plans permite detectar índices faltantes, estadísticas inconsistentes o patrones ineficientes. Ignorar estos planes puede llevar a bajo rendimiento.

### **Server Resources:**
Las bases de datos gestionan intensivamente la memoria y los cachés para reducir I/O. Si no hay suficiente memoria o la gestión es ineficiente, el rendimiento baja.

### **Storage Utilization:**
La velocidad de la memoria y el almacenamiento, especialmente en la escritura del transaction log, es un factor crítico. Un almacenamiento lento limita directamente la capacidad de respuesta del sistema

## 2. Considera que afectan de igual forma las bases de datos NoSQL y SQL?

No todos los factores afectan igual a SQL y NoSQL, aunque ambos dependen de recursos como memoria, CPU y almacenamiento, se diferencian por los siguientes:

- Optimización de consultas: en SQL el rendimiento depende mucho del execution plan y del uso de índices; en NoSQL, las consultas suelen ser más simples, pero la forma en que se modelan los documentos o claves también afecta la eficiencia.

- Uso de memoria y cachés: tanto SQL como NoSQL dependen de la memoria para reducir I/O, pero en NoSQL esto suele ser aún más relevante porque buscan servir datos rápidamente desde caché sin procesos complejos de optimización.

- Planes de ejecución y tuning: los SQL dependen fuertemente de ellos mientras que en NoSQL no hay planes tan detallados

 <br>

## 3. Explique en que consiste un anti-pattern en bases de datos

Un anti-pattern en bases de datos es un enfoque ineficaz para resolver problemas que termina afectando el rendimiento. Algunos ejemplos son:

- Procesar filas una por una en grandes volúmenes de datos: esto funciona con pequeños arreglos en código, pero en tablas con miles o millones de filas reduce drásticamente la eficiencia.

- Usar tipos de datos inconsistentes entre la aplicación y la base de datos: esto obliga a conversiones de datos (CAST, CONVERT) que consumen recursos.

- Utilizar SELECT * en lugar de columnas específicas: genera más I/O, puede traer datos innecesarios y ocasionar errores si la tabla cambia.

Se recomiendan seguir estas prácticas para evitarlos:

- Preferir operaciones en conjunto en lugar de fila por fila.

- Consultar solo las columnas necesarias.

- Mantener actualizadas las estadísticas de columnas e índices.

- Minimizar conversiones de tipos de datos.

- Aprender a interpretar el plan de ejecución del motor de base de datos.
