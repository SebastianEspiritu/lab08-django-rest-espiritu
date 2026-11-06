# Laboratorio 08: Servicios Web con Django

Curso: Desarrollo de Aplicaciones Empresariales. Etapas 1 y 2: configuración
inicial, modelos y relaciones.

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
Los modelos del dominio ya están definidos. Todavía no hay serializadores,
ViewSets ni endpoints API.
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

En la siguiente etapa, el serializador de pregunta debe recibir las opciones
anidadas y el examen por identificador. Debe validar exactamente una opción
correcta y guardar pregunta y opciones en una transacción atómica. También se
deberá definir el comportamiento de actualizaciones parciales y de las
operaciones directas sobre opciones para conservar esa regla. Por ahora, el ORM
y Admin permiten cero o varias opciones correctas: no se adelantó esa validación.

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
| 3 | ModelSerializer para examen, pregunta y opción; campos y solo lectura | Pendiente |
| 4 | Opciones anidadas en pregunta; examen por identificador | Pendiente |
| 5 | Validar exactamente una opción correcta por pregunta | Pendiente |
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

Las etapas 1 y 2 preparan la base; aún no cumplen los cuatro criterios completos.
El entregable posterior debe registrar nombre del alumno, título, captura del
resultado, código, explicación, casos de prueba y captura de la estructura.
El criterio de desempeño 1.3 no suma puntos adicionales.
