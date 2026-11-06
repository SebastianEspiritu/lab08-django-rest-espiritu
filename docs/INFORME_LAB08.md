# Laboratorio 08: Implementación de Servicios Web con Django

## Portada

**Curso:** Desarrollo de Aplicaciones Empresariales  
**Docente:** Michael Montgomery Rosell  
**Estudiante:** [COMPLETAR NOMBRE Y APELLIDOS]  
**Código:** [COMPLETAR]  
**Sección:** [COMPLETAR]  
**Integrantes y responsabilidades:** [COMPLETAR SEGÚN PARTICIPACIÓN REAL]  
**Fecha de entrega:** [COMPLETAR]  
**Repositorio:** https://github.com/SebastianEspiritu/lab08-django-rest-espiritu

Documento preparado para copiar a Word. Los marcadores de captura deben
reemplazarse por evidencias reales; este informe no contiene imágenes generadas
ni acredita una entrega al campus o un push que no se haya realizado.

## 1. Objetivos

Implementar servicios REST para administrar exámenes, preguntas y opciones con
Django REST Framework. Utilizar serializadores derivados de modelos, validar
los datos de entrada, publicar los tres recursos mediante ViewSets y un router,
y comprobar operaciones HTTP, errores, filtros, búsqueda y paginación.

## 2. Fundamento teórico

REST organiza la interacción en recursos identificados por direcciones y
operaciones HTTP. GET consulta, POST crea, PATCH modifica parcialmente y DELETE
elimina. PUT permite una actualización completa según el contrato de campos.
Los códigos de respuesta permiten diferenciar éxito, validación y ausencia de
recursos. ModelSerializer transforma modelos en datos de intercambio y valida
entradas; ModelViewSet reúne las operaciones del recurso y DefaultRouter genera
las rutas. Las transacciones atómicas evitan persistir cambios incompletos.

La validación entre varias opciones exige examinar el estado de la pregunta
completa: exactamente una opción debe estar marcada como correcta. La
paginación limita el tamaño de cada respuesta y mantiene enlaces de navegación.

Fuente principal de requisitos: `GLAB-S08-MMONTGOMERY-2026-02.docx`, documento
original proporcionado por el estudiante, consultado sin modificarlo desde
Descargas porque inicialmente no existía `docs/`. Referencias técnicas:
documentación de Django 5.2 y documentación de Django REST Framework.

## 3. Herramientas

Windows 11, VS Code, Python 3.14.4, Django 5.2.19, Django REST Framework 3.18.3,
SQLite y Git. Las dependencias exactas están en `requirements.txt`.
Las pruebas automatizadas usan Django TestCase/APITestCase; las externas
confirmadas usan Python estándar `urllib.request`, fuera del proceso servidor.
Se preparó una colección Postman v2.1, pero **Postman no se ejecutó** durante
esta preparación. Node.js y React no son necesarios para esta API.

## 4. Desarrollo de los 12 pasos

### Paso 1. Estructura e instalación

Se creó el entorno `.venv`, el proyecto `config` y la aplicación `quiz`.
`rest_framework` y `quiz` están en INSTALLED_APPS. SQLite es la base local.
`.gitignore` excluye el entorno, cachés, `.env` y `db.sqlite3`. Las migraciones
de esquema sí se versionan.

**[INSERTAR CAPTURA C01 AQUÍ]** Estructura del repositorio en VS Code.

### Paso 2. Configuración REST

Se configuró PageNumberPagination con PAGE_SIZE=10 y permisos iniciales
AllowAny exclusivamente para desarrollo local. No se guardan credenciales en
settings.py. La clave local procede de una variable o se genera por proceso.

**[INSERTAR CAPTURA C02 AQUÍ]** INSTALLED_APPS y REST_FRAMEWORK.

### Paso 3. Modelos y serializadores

Exam tiene `id` y `title` (hasta 200 caracteres). Question tiene `id`, `exam`
y `text`. Option tiene `id`, `question`, `text` (hasta 500 caracteres) e
`is_correct` (falso inicialmente). Exam → Question y Question → Option son
relaciones uno a muchos con ForeignKey, CASCADE y accesos inversos `questions`
y `options`. Todos incluyen representación `__str__` y registro en Admin.

ExamSerializer, QuestionSerializer y OptionSerializer derivan de
ModelSerializer, declaran campos explícitos e `id` de solo lectura.

**[INSERTAR CAPTURA C03 AQUÍ]** Modelos y serializadores.

### Paso 4. Representación de relaciones

Cada pregunta representa `exam` por identificador y expone `options` como una
lista anidada de `id`, `text` e `is_correct`. Las opciones individuales
representan su pregunta por ID. La creación anidada asigna la pregunta padre
sin solicitar esa relación dentro de cada opción.

### Paso 5. Validación personalizada

Se rechaza una pregunta sin exactamente una opción correcta. La creación y el
reemplazo de opciones se realizan dentro de transaction.atomic(). PATCH sin
opciones conserva y valida las existentes; con opciones reemplaza la lista
completa y genera nuevos IDs. Cambiar la correcta se realiza mediante ese
reemplazo atómico, no mediante dos actualizaciones individuales incompatibles.

Las escrituras directas de opciones rechazan una segunda correcta, desmarcar o
eliminar la única correcta y mover una opción a otra pregunta. Se permite
editar textos, agregar opciones incorrectas y eliminarlas si el estado final
es válido. El borrado se protege en OptionViewSet.perform_destroy().

**[INSERTAR CAPTURA C04 AQUÍ]** Validación y protección de DELETE.

### Paso 6. ViewSets y enrutador

Se implementaron ExamViewSet, QuestionViewSet y OptionViewSet como ModelViewSet.
DefaultRouter registra `/api/exams/`, `/api/questions/` y `/api/options/`,
incluidas desde config/urls.py. Los detalles usan el identificador en la ruta.
Question precarga opciones y carga el examen relacionado; Option carga su
pregunta relacionada para evitar consultas N+1.

**[INSERTAR CAPTURA C05 AQUÍ]** ViewSets, router e inclusión de rutas.

### Paso 7. API navegable

La raíz `/api/` muestra los tres recursos. Se comprobó mediante pruebas
automatizadas el HTML de raíz, colecciones y detalles, y las operaciones con
negociación HTML. Se levantó un servidor local y se consultaron por HTTP las
colecciones con respuesta HTML. **El recorrido visual manual y sus capturas
deben completarse por el estudiante**; no se afirma haber operado un navegador.

Para recorrerla, iniciar el servidor, abrir `/api/`, crear un examen propio y
una pregunta con opciones válidas. Consultar listado y detalle, modificar texto
y eliminar solo esos datos. Registrar los códigos mostrados. DELETE con JSON
devuelve 204; la API navegable convierte ese estado a 200 para mostrar HTML.

**[INSERTAR CAPTURA C06 AQUÍ]** Raíz navegable con los tres enlaces.
**[INSERTAR CAPTURA C07 AQUÍ]** Pregunta con opciones anidadas.
**[INSERTAR CAPTURA C08 AQUÍ]** Recorrido visual CRUD y códigos reales.

### Paso 8. Cliente HTTP externo

Se ejecutaron 41 solicitudes reales mediante `scripts/http_lab08.py`, con
urllib.request como cliente separado del servidor. Se verificaron listado,
detalle, creación, PATCH y DELETE para los tres recursos, más filtros,
paginación, errores y restricciones de integridad. Todas devolvieron el código
esperado. Los cuerpos completos están en `docs/HTTP_RESULTS.json`, con fecha
UTC real de ejecución y nombre del cliente. Los IDs del registro son históricos
y fueron eliminados al finalizar.

Se creó un examen exclusivo de la prueba, 11 preguntas y opciones asociadas.
El último DELETE del examen eliminó en cascada las preguntas auxiliares. Se
compararon todos los registros anteriores y posteriores: no cambiaron los
datos existentes ni quedaron registros temporales de la ejecución.

La colección `postman/LAB08.postman_collection.json` contiene las mismas 41
solicitudes en orden y scripts de pruebas. Captura IDs dinámicos y utiliza
`base_url=http://127.0.0.1:8000`. Su JavaScript queda pendiente de ejecutar en
Postman; el cliente Python ejecutó comprobaciones equivalentes, no JavaScript.

**[INSERTAR CAPTURA C09 AQUÍ]** Registro externo y resumen HTTP.
**[INSERTAR CAPTURA C10 AQUÍ, TRAS EJECUTAR POSTMAN]** Collection Runner.

### Paso 9. Errores deliberados

| Caso ejecutado | HTTP | Mensaje observado |
| --- | --- | --- |
| POST examen sin title | 400 | `title: ["This field is required."]` |
| POST pregunta con exam de tipo texto no numérico | 400 | `exam: ["Incorrect type. Expected pk value, received str."]` |
| POST pregunta sin correcta | 400 | `options: ["A question must have exactly one correct option."]` |
| POST pregunta con dos correctas | 400 | Mismo mensaje de validación de opciones |
| GET de recurso recién eliminado | 404 | `No Exam/Question/Option matches the given query.` según el recurso |

También se verificaron 400 al romper integridad por operaciones sobre Option y
404 al solicitar una página fuera de rango. Ver registro completo.

**[INSERTAR CAPTURA C11 AQUÍ]** Tres respuestas de error con solicitud y código.

### Paso 10. Filtrado, búsqueda y paginación

`?exam=<id>` filtra por examen; un identificador mal formado devuelve 400 y uno
válido sin coincidencias da lista vacía. `?search=python` busca subcadenas de
text sin distinguir mayúsculas en los ejemplos ASCII. Ambos se combinan.
`?page=2` usa páginas de 10; `count` indica el total tras filtrar y los enlaces
next/previous conservan los parámetros. La página inexistente devuelve 404.

El flujo externo creó 11 preguntas aisladas con un texto único. La consulta
combinada devolvió count=11 y un resultado en página 2, next=null y un enlace
previous válido. Las opciones anidadas conservaron una única correcta.
El comando `seed_quiz_demo` permite añadir conjuntos demostrativos sin borrar
registros; no se introducen datos mediante migraciones de esquema.

**[INSERTAR CAPTURA C12 AQUÍ]** Filtros combinados, páginas 1 y 2.

### Paso 11. Tabla de la API

La tabla completa está en **docs/API_TABLE.md**. Contiene recurso, dirección,
método HTTP, cuerpo de ejemplo y código/respuesta esperada para todos los
recursos, filtros, paginación y errores. Al copiar este informe a Word, incluir
la tabla como anexo o entregar el archivo junto con el informe.

**[INSERTAR CAPTURA C13 AQUÍ]** Tabla API legible.

### Paso 12. Repositorio y entrega

Los archivos están preparados localmente. **No se hizo commit ni push**, por
instrucción del estudiante. Quedan pendientes autorizar y realizar la
publicación de los cambios, completar datos personales y capturas, exportar el
informe a Word/PDF según Canvas y cargarlo al campus dentro del plazo.
No se afirma que el repositorio remoto ya contenga estas modificaciones.

**[INSERTAR CAPTURA C15 AQUÍ DESPUÉS DE PUBLICAR]** Repositorio remoto.
**[INSERTAR CAPTURA C16 AQUÍ DESPUÉS DE ENTREGAR]** Confirmación del campus.

## 5. Resultados y verificación técnica

Los comandos usan el intérprete del entorno:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Resultado confirmado: 60 pruebas aprobadas; comprobaciones de Django sin
problemas; ningún cambio de modelo pendiente de migración. La salida completa
de esta etapa se conserva en `docs/TECHNICAL_CHECKS.txt`.
Las pruebas externas confirmaron 41 respuestas esperadas, incluidos estados
200, 201, 204, 400 y 404. No se modificaron modelos, serializadores o endpoints
durante esta etapa documental.

**[INSERTAR CAPTURA C14 AQUÍ]** Terminal con las tres verificaciones técnicas.

## 6. Conclusiones

La separación entre modelos, serializadores y ViewSets permite organizar la
persistencia, validación y exposición HTTP. La validación de opciones requiere
evaluar el conjunto de respuestas y proteger tanto la escritura anidada como
las operaciones directas. Las transacciones impiden cambios incompletos y las
pruebas automatizadas comprueban los casos de éxito y rechazo.

El filtrado y la búsqueda reducen los resultados antes de paginar. La precarga
de opciones mantiene un número de consultas constante al listar preguntas.
Las pruebas externas verifican además la integración del servidor y el
contrato JSON real, sin reemplazar las evidencias visuales del entregable.

Limitaciones: AllowAny y DEBUG son locales; SQLite no implementa el bloqueo de
filas solicitado por select_for_update(). No se acredita seguridad concurrente
de producción. Admin, SQL y escrituras ORM que omiten los serializadores pueden
crear estados inválidos. La calificación final corresponde al docente y depende
de completar y entregar las evidencias y el repositorio.

## 7. Guía exacta de capturas pendientes

Cada captura debe ser real, legible y sin credenciales. Para cada desarrollo,
añadir nombre del alumno, título, código o referencia al archivo, explicación
del resultado y caso de prueba, como exige el documento original.

| ID | Pantalla o archivo que capturar | Qué debe verse | Colocación |
| --- | --- | --- | --- |
| C01 | Explorador de VS Code | config, quiz, migraciones, pruebas, docs, postman, scripts y requirements; ocultar contenido de .venv | Paso 1 |
| C02 | config/settings.py, dos capturas si es necesario | INSTALLED_APPS y REST_FRAMEWORK, PAGE_SIZE=10 y AllowAny | Paso 2 |
| C03 | quiz/models.py y quiz/serializers.py | Tres modelos, ForeignKey/related_name; campos y read_only_fields de serializadores | Paso 3 |
| C04 | quiz/serializers.py y quiz/views.py | Conteo de una correcta, atomic y perform_destroy | Paso 5 |
| C05 | quiz/views.py, quiz/urls.py y config/urls.py | Tres ViewSets, registros del router y prefijo api/ | Paso 6 |
| C06 | Navegador en /api/ | Los tres enlaces y respuesta 200 | Paso 7 |
| C07 | Navegador, detalle de pregunta propia válida | exam numérico y options anidadas con exactamente una correcta | Paso 7 |
| C08 | Navegador, secuencia de operaciones sobre datos propios | GET listado y detalle, POST, PATCH y DELETE; método, URL y código de cada operación; incluir los tres recursos | Paso 7; varias imágenes |
| C09 | Terminal al ejecutar scripts/http_lab08.py y docs/HTTP_RESULTS.json | Cliente externo, códigos por solicitud y resumen de resultados; iniciar servidor en otra terminal | Paso 8 |
| C10 | Postman Collection Runner tras importar y ejecutar | Nombre de colección, 41 solicitudes, tests y resumen real sin fallos; añadir detalle de CRUD por recurso | Paso 8; pendiente de ejecutar |
| C11 | Postman o registro HTTP externo | POST sin title, exam incorrecto y pregunta sin correcta; URL, cuerpo, HTTP 400 y mensajes | Paso 9; tres imágenes |
| C12 | Postman o navegador, consulta combinada del examen creado | Parámetros exam/search; páginas 1 y 2, count, next, previous y opciones; usar IDs de la ejecución vigente | Paso 10; dos imágenes |
| C13 | docs/API_TABLE.md renderizado o tabla pegada en Word | Columnas completas y ejemplos de éxito/error legibles | Paso 11 |
| C14 | Terminal desde la raíz | check sin problemas, 60 tests OK y No changes detected | Resultados |
| C15 | GitHub después del push autorizado | URL del repositorio y archivos finales, incluidos docs y postman | Paso 12; pendiente de autorización/publicación |
| C16 | Canvas después de la entrega | Archivo entregado y confirmación/fecha; ocultar datos privados innecesarios | Paso 12; pendiente de entrega |

Las capturas C08 y C10 requieren ejecutar el recorrido indicado; no reutilizar
resultados inexistentes. Para capturar estados intermedios de los datos de
Postman, pausar antes de las eliminaciones finales o ejecutar en orden hasta
esa sección. Luego completar la limpieza de esa misma ejecución.
