# Laboratorio 08: Servicios Web con Django

Curso: Desarrollo de Aplicaciones Empresariales. Etapas 1 a 3: configuración
inicial, modelos, relaciones y serializadores.

## Instalación y ejecución en PowerShell

Requisitos: Windows, Python 3.14 y Git. Desde la raíz del repositorio:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Abrir <http://127.0.0.1:8000/> para ver la página inicial de Django.
Detener el servidor con `Ctrl+C`. Estos comandos no requieren activar scripts
ni cambiar la política de ejecución de PowerShell.

El proyecto se llama `config` y la aplicación `quiz`. Las versiones exactas
están fijadas en `requirements.txt`. SQLite crea `db.sqlite3` al migrar.
La base local, `.venv/`, `.env` y los archivos compilados quedan ignorados por
Git. Las migraciones propias que se creen posteriormente sí se versionarán.
Los modelos y serializadores ya están definidos. Todavía no hay ViewSets
ni endpoints API.
La ruta `/admin/` pertenece a Django.

## Modelos y relaciones (Etapa 2)

| Modelo | Campos propios | Relación |
| --- | --- | --- |
| `Exam` | `title`: texto obligatorio de hasta 200 caracteres | `exam.questions.all()` obtiene sus preguntas |
| `Question` | `text`: enunciado obligatorio sin límite fijo de longitud | `exam`: ForeignKey obligatorio a Exam; `question.options.all()` obtiene sus opciones |
| `Option` | `text`: texto obligatorio de hasta 500 caracteres; `is_correct`: booleano, inicialmente falso | `question`: ForeignKey obligatorio a Question |

Todos incluyen un `id` automático de tipo BigAutoField y representación
`__str__` basada en su texto o título. El orden predeterminado por `id` permite
una paginación estable. Los títulos y textos no se restringen a valores únicos.

Las dos relaciones son uno a muchos, con `related_name="questions"` y
`related_name="options"`. Usan `CASCADE`: borrar un examen elimina sus preguntas
y opciones; borrar una pregunta elimina sus opciones. Los otros recursos
permanecen intactos. Los tres modelos están registrados en Admin con búsqueda
y filtros adecuados. Para acceder, crear un usuario administrador local:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

La migración `quiz/migrations/0001_initial.py` crea las tres tablas.
Para comprobar las relaciones y el borrado en cascada sin dejar datos de prueba
en la base local:

```powershell
.\.venv\Scripts\python.exe manage.py test quiz
```

El ORM y Admin permiten cero o varias opciones correctas; la validación de la
Etapa 3 se aplica al utilizar los serializadores, sin modificar los modelos.

## Serializadores y validación (Etapa 3)

Los serializadores usan `ModelSerializer`, campos explícitos e `id` de solo
lectura. Los mensajes de validación del código están en inglés.

| Serializador | Campos expuestos | Representación de relaciones |
| --- | --- | --- |
| `ExamSerializer` | `id`, `title` | Sin preguntas anidadas |
| `QuestionSerializer` | `id`, `exam`, `text`, `options` | Examen por identificador; opciones anidadas |
| `OptionSerializer` | `id`, `question`, `text`, `is_correct` | Pregunta por identificador |

`NestedOptionSerializer` es auxiliar: expone `id` (solo lectura), `text` e
`is_correct` dentro de cada pregunta. La pregunta padre asigna la relación;
el cliente no envía `question` dentro de las opciones anidadas.

La validación exige exactamente un `is_correct=True` en el estado resultante.
Rechaza listas vacías, ausentes al crear, nulas, cero o varias opciones correctas,
y datos incompatibles con los campos. Se conserva la conversión estándar de
tipos de DRF, por ejemplo sus representaciones reconocidas de booleanos.
Los errores usan `serializers.ValidationError`, asociados al campo pertinente.

`create()` guarda la pregunta y sus opciones con `bulk_create()` dentro de
`transaction.atomic()`. `update()` usa la misma transacción y vuelve a validar
antes de escribir. Si falla la escritura anidada, se revierten tanto los cambios
de la pregunta como el borrado o creación de opciones.

Enviar `options` en PUT o PATCH significa **reemplazar la lista completa**:
se eliminan las opciones anteriores y se crean las nuevas, con nuevos IDs.
No se actualizan opciones por ID anidado; los IDs de entrada son de solo lectura.
Cada elemento debe incluir `text`, incluso en PATCH; omitir `is_correct`
equivale a falso. PUT requiere los campos obligatorios, incluidas las opciones.
PATCH sin `options` conserva la lista existente, valida que siga teniendo una
correcta y rechaza la actualización si el estado existente ya era inválido.
Cambiar cuál es la opción correcta se hace enviando la lista completa válida
en una sola actualización de pregunta.

### Operaciones directas sobre opciones en la siguiente etapa

`OptionSerializer` ya comprueba el resultado de crear o actualizar una opción:
no permite agregar una segunda correcta ni desmarcar la única correcta.
Permite editar texto y agregar opciones incorrectas si la pregunta sigue válida.
No permite trasladar una opción a otra pregunta. Revalida al guardar para no
depender únicamente de la consulta realizada en `is_valid()`.

La futura operación DELETE debe implementarse en la vista o un servicio:
abrir una transacción, bloquear la pregunta padre, comprobar que tras eliminar
la opción quede exactamente una correcta y rechazar la operación en caso
contrario. DELETE no pasa por `OptionSerializer`. Todas las escrituras sobre
una misma pregunta deben seguir el mismo protocolo, incluida su actualización
anidada. Eliminar una pregunta o examen completo sigue siendo una cascada válida.

Se usa `select_for_update()` sobre la pregunta en las actualizaciones y en las
escrituras directas de opciones. **SQLite no ofrece ese bloqueo de filas**:
las pruebas no garantizan concurrencia entre escritores. Antes de un despliegue
con escrituras concurrentes se requiere una estrategia de concurrencia probada,
por ejemplo PostgreSQL y transacciones con bloqueo común de la pregunta padre.
La regla tampoco protege escrituras que omitan los serializadores, como Admin,
scripts o SQL directo. No se añadió una restricción de base de datos: un índice
único parcial solo garantizaría como máximo una correcta, no exactamente una.

Para evitar consultas N+1, la futura vista de preguntas debe usar
`prefetch_related("options")`. El examen se representa por su identificador,
sin cargar su objeto para serializar. Una prueba comprueba que serializar dos
preguntas con sus opciones requiere dos consultas en total. La validación de
conteos consulta la base actual deliberadamente para evitar una caché obsoleta.

### Pruebas

```powershell
.\.venv\Scripts\python.exe manage.py test quiz --verbosity 2
.\.venv\Scripts\python.exe manage.py check
```

Se incluyen 20 pruebas nuevas de serializadores y las 3 de relaciones anteriores.
Cubren representaciones, referencias por ID, creación válida, datos inválidos,
PATCH, reemplazo de opciones, operaciones directas, revalidación al guardar,
consultas con precarga y rollback. Los errores de escritura de las pruebas de
rollback se provocan deliberadamente después de modificar la base dentro de la
transacción; así se comprueba la reversión real y no solo el rechazo previo.

## Configuración local

DRF usa `PageNumberPagination`, 10 resultados por página y permisos `AllowAny`.
**Estos permisos y `DEBUG=True` son exclusivamente para desarrollo local.**
Antes de publicar, revisar autenticación, permisos y configuración de despliegue.

La clave se obtiene de la variable de entorno `DJANGO_SECRET_KEY`; si no existe,
se genera una clave efímera por proceso. Las sesiones pueden invalidarse al
reiniciar; para conservarlas, definir una clave local estable en esa variable.
No se escriben credenciales en `settings.py`. Los archivos `.env` se ignoran,
pero no se cargan automáticamente.

## Seguimiento del laboratorio

Fuente principal: `GLAB-S08-MMONTGOMERY-2026-02.docx`, consultado desde la ruta
proporcionada en Descargas, porque `docs/` no existía al iniciar la etapa.
El documento no se modificó ni se copió al repositorio.

| Paso | Requisito | Estado |
| --- | --- | --- |
| 1 | Proyecto, DRF y registro de `quiz` | Completado |
| 2 | Paginación y permisos iniciales | Completado |
| 3 | ModelSerializer para examen, pregunta y opción; campos y solo lectura | Completado |
| 4 | Opciones anidadas en pregunta; examen por identificador | Completado |
| 5 | Validar exactamente una opción correcta por pregunta | Completado |
| 6 | Tres ViewSets, enrutador y rutas en config/urls.py | Pendiente |
| 7 | Listar, detalle, crear, modificar parcialmente y eliminar en API navegable; códigos HTTP | Pendiente |
| 8 | Repetir cinco operaciones con JSON desde cliente HTTP externo | Pendiente |
| 9 | Mensajes y códigos de campo ausente, tipo incorrecto y opción correcta inválida | Pendiente |
| 10 | Filtrar por examen, buscar por enunciado y comprobar varias páginas | Pendiente |
| 11 | Tabla de recurso, dirección, método, cuerpo y respuesta esperada | Pendiente |
| 12 | Repositorio y entregable en campus | Pendiente; commit y push requieren autorización |

Para aspirar a los 20 puntos deben completarse estas evidencias:

| Criterio | Puntos | Requisito para excelente |
| --- | --- | --- |
| Serializadores y validación | 5 | Derivación del modelo, validación propia y relaciones anidadas |
| ViewSets y enrutadores | 5 | Tres recursos enrutados y accesibles en API navegable |
| Operaciones HTTP | 5 | Cinco operaciones desde cliente externo y códigos correctos, incluidos errores |
| Repositorio y tabla API | 5 | Tabla completa que coincida con la API real y entrega del repositorio |

Las etapas 1 a 3 cubren la base y el criterio de serializadores; aún faltan los
otros tres criterios de la rúbrica y sus evidencias HTTP.
El entregable posterior debe registrar nombre del alumno, título, captura del
resultado, código, explicación, casos de prueba y captura de la estructura.
El criterio de desempeño 1.3 no suma puntos adicionales.
