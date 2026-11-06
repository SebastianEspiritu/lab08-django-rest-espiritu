# Tabla de la API — Laboratorio 08

Base local: `http://127.0.0.1:8000`. Enviar `Accept: application/json` y, con
cuerpo, `Content-Type: application/json`. Todas las rutas terminan en `/`.
Permiso actual: `AllowAny`, exclusivamente para desarrollo local.

Los números 100, 200 y 300 de los ejemplos son ilustrativos: reemplazarlos por
IDs obtenidos al crear los recursos. `{id}` en las direcciones es un marcador.
Los ejemplos indican las propiedades esperadas; los IDs reales son asignados
por la base. La colección Postman captura sus propios IDs.

| Recurso | Dirección | Método HTTP | Cuerpo JSON de ejemplo | Código y respuesta esperada |
| --- | --- | --- | --- | --- |
| Raíz | `/api/` | GET | — | 200; objeto con enlaces absolutos `exams`, `questions`, `options` |
| Exam | `/api/exams/` | GET | — | 200; objeto paginado con exámenes `{id,title}` |
| Exam | `/api/exams/{id}/` | GET | — | 200; `{"id":100,"title":"Python"}` si existe |
| Exam | `/api/exams/` | POST | `{"title":"Python"}` | 201; examen creado con `id` y `title` |
| Exam | `/api/exams/{id}/` | PUT | `{"title":"Python completo"}` | 200; examen actualizado |
| Exam | `/api/exams/{id}/` | PATCH | `{"title":"Python actualizado"}` | 200; examen actualizado |
| Exam | `/api/exams/{id}/` | DELETE | — | 204; sin cuerpo; elimina preguntas y opciones en cascada |
| Question | `/api/questions/` | GET | — | 200; objeto paginado con preguntas y opciones anidadas |
| Question | `/api/questions/{id}/` | GET | — | 200; `id`, `exam` numérico, `text`, `options` con `id`, `text`, `is_correct` |
| Question | `/api/questions/` | POST | `{"exam":100,"text":"What is Python?","options":[{"text":"A language","is_correct":true},{"text":"A database","is_correct":false}]}` | 201; pregunta y opciones creadas, con IDs asignados |
| Question | `/api/questions/{id}/` | PUT | `{"exam":100,"text":"Updated question","options":[{"text":"Yes","is_correct":true},{"text":"No","is_correct":false}]}` | 200; reemplaza la lista de opciones, genera nuevos IDs |
| Question | `/api/questions/{id}/` | PATCH | `{"text":"Edited question"}` | 200; conserva opciones existentes si siguen siendo válidas |
| Question | `/api/questions/{id}/` | PATCH | `{"options":[{"text":"First","is_correct":false},{"text":"Second","is_correct":true}]}` | 200; reemplaza lista completa y cambia la correcta atómicamente |
| Question | `/api/questions/{id}/` | DELETE | — | 204; sin cuerpo; elimina sus opciones |
| Option | `/api/options/` | GET | — | 200; objeto paginado con opciones `{id,question,text,is_correct}` |
| Option | `/api/options/{id}/` | GET | — | 200; `{"id":300,"question":200,"text":"No","is_correct":false}` si existe |
| Option | `/api/options/` | POST | `{"question":200,"text":"Other","is_correct":false}` | 201 si la pregunta conserva exactamente una correcta |
| Option | `/api/options/{id}/` | PUT | `{"question":200,"text":"Other edited","is_correct":false}` | 200 si el estado resultante conserva una correcta y no cambia de pregunta |
| Option | `/api/options/{id}/` | PATCH | `{"text":"Edited option"}` | 200; conserva los campos omitidos |
| Option | `/api/options/{id}/` | DELETE | — | 204 si tras borrar queda exactamente una correcta; sin cuerpo |
| Preguntas por examen | `/api/questions/?exam=100` | GET | — | 200; solo preguntas de ese examen; sin coincidencias: `{"count":0,"next":null,"previous":null,"results":[]}` |
| Búsqueda de enunciado | `/api/questions/?search=python` | GET | — | 200; coincidencia parcial en `text`, insensible a mayúsculas para ASCII; sin coincidencias, lista paginada vacía |
| Página de preguntas | `/api/questions/?page=2` | GET | — | 200 si existe; hasta 10 elementos, total en `count`, enlaces en `next` y `previous` |
| Consulta combinada | `/api/questions/?exam=100&search=python&page=2` | GET | — | 200 si existe esa página del resultado filtrado; enlaces conservan filtros |
| Página de exámenes/opciones | `/api/exams/?page=2`, `/api/options/?page=2` | GET | — | 200 si existe; misma paginación de 10 elementos |
| Metadatos | `/api/`, colecciones y detalles anteriores | OPTIONS | — | 200 para rutas existentes; metadatos DRF y encabezado `Allow` |
| Encabezados | `/api/`, colecciones y detalles anteriores | HEAD | — | Mismo estado y encabezados que GET, sin cuerpo |

## Errores y límites verificados

Los mensajes siguientes se observaron en las respuestas JSON, con idioma actual
en inglés. El registro completo está en [HTTP_RESULTS.json](HTTP_RESULTS.json).

| Recurso | Dirección | Método HTTP | Cuerpo JSON de ejemplo | Código y respuesta esperada |
| --- | --- | --- | --- | --- |
| Campo ausente | `/api/exams/` | POST | `{}` | 400; `{"title":["This field is required."]}` |
| Tipo incorrecto | `/api/questions/` | POST | `{"exam":"not-an-id","text":"Python","options":[{"text":"Yes","is_correct":true}]}` | 400; `exam` contiene error de tipo incorrecto para clave primaria |
| Cero correctas | `/api/questions/` | POST | `{"exam":100,"text":"Python","options":[{"text":"No","is_correct":false}]}` | 400; `{"options":["A question must have exactly one correct option."]}` |
| Dos correctas | `/api/questions/` | POST | `{"exam":100,"text":"Python","options":[{"text":"A","is_correct":true},{"text":"B","is_correct":true}]}` | 400; mismo error en `options` |
| Lista vacía | `/api/questions/` | POST | `{"exam":100,"text":"Python","options":[]}` | 400; error de lista vacía en `options` |
| Filtro inválido | `/api/questions/?exam=invalid` | GET | — | 400; `{"exam":"Use a positive integer exam ID (up to 2^63 - 1)."}` |
| Página inexistente | `/api/questions/?exam=100&page=999999` | GET | — | 404; `{"detail":"Invalid page."}` |
| Recurso inexistente | `/api/exams/{id}/`, `/api/questions/{id}/`, `/api/options/{id}/` | GET, PUT, PATCH, DELETE | Según operación | 404 si el objeto no existe; `detail` indica que no hay Exam, Question u Option con ese identificador |
| Segunda correcta | `/api/options/` | POST | `{"question":200,"text":"Bad","is_correct":true}` | 400 si ya existe una correcta; error en `options` |
| Desmarcar única correcta | `/api/options/{id}/` | PATCH | `{"is_correct":false}` | 400; error en `options`, registro intacto |
| Borrar única correcta | `/api/options/{id}/` | DELETE | — | 400; error en `options`, registro intacto |
| Mover opción | `/api/options/{id}/` | PATCH | `{"question":201}` | 400 si 201 existe y es otra pregunta; `{"question":["An option cannot move to another question."]}` |

## Convenciones de respuesta

- Los listados siempre contienen `count`, `next`, `previous`, `results`.
  `count` es el total tras filtrar, no el tamaño de la página.
- Página inicial: `previous:null`; página final: `next:null`.
- `exam` acepta enteros positivos canónicos hasta 2^63−1; vacío, cero, negativo,
  ceros iniciales o formato no numérico dan 400. Un examen válido inexistente
  produce lista vacía. `page` inválido o fuera de rango produce 404.
- `search` vacío no restringe. DRF separa términos: deben coincidir todos.
  SQLite limita la comparación de mayúsculas de caracteres Unicode.
- El filtrado de DRF también se aplica a detalles de preguntas: un objeto
  excluido por parámetros de consulta devuelve 404.
- `id` es de solo lectura. Las opciones anidadas omiten `question`; la pregunta
  padre asigna esa relación. En PATCH, una lista enviada reemplaza todas las
  opciones y requiere `text` en cada elemento; omitir `is_correct` equivale a falso.
- El serializador de Option usa un valor inicial falso para `is_correct`.
  PUT sigue los requisitos de campos de DRF; para conservar una correcta enviar
  explícitamente `is_correct:true`. PATCH conserva los valores omitidos.
- Un ID de relación inexistente da 400 durante validación, no 404 de recurso.
- DELETE JSON devuelve 204. Con `Accept:text/html`, DRF lo convierte en 200
  para mostrar su página navegable. No se personalizó ese comportamiento.
- La raíz `/api/` no admite escrituras. Las colecciones no admiten PUT/PATCH/
  DELETE y los detalles no admiten POST: métodos no permitidos devuelven 405.
- `/admin/` es el sitio administrativo estándar de Django, no un recurso REST
  de esta tabla. No se añadieron endpoints propios adicionales.
