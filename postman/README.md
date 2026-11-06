# Colección del Laboratorio 08

Archivo importable: `LAB08.postman_collection.json` (formato Collection v2.1).
Contiene 41 solicitudes ordenadas, con pruebas JavaScript y captura de IDs.

1. Iniciar Django desde la raíz: `.\.venv\Scripts\python.exe manage.py runserver`.
2. En Postman, importar el JSON y abrir Collection Runner.
3. Usar la variable de colección `base_url=http://127.0.0.1:8000`.
4. No definir variables de entorno con los mismos nombres: podrían ocultar las
   variables de colección `exam_id`, `question_id`, `option_id`, `correct_id`
   y `run_tag`.
5. Ejecutar toda la colección en orden, una iteración. No ejecutar solicitudes
   destructivas aisladas ni sustituir IDs por los exámenes de demostración.
6. Revisar todos los tests, registrar el resumen y capturar respuestas conforme
   a `docs/INFORME_LAB08.md`.

La primera solicitud crea un identificador aleatorio de ejecución y un examen.
Se crean 11 preguntas válidas para garantizar dos páginas incluso sin datos
previos. Los scripts capturan IDs de las respuestas. Se verifican CRUD de los
tres recursos, filtros, búsqueda, paginación, errores e integridad. Las últimas
solicitudes eliminan solo los datos creados por esta ejecución; la eliminación
del examen elimina las preguntas auxiliares en cascada. Las consultas de listado
global pueden mostrar datos previos, pero ninguna escritura los utiliza.

Si se interrumpe la ejecución, pueden quedar datos propios de esa ejecución.
Conservar el ID capturado y verificar el título con su `run_tag` antes de
completar la limpieza. No borrar registros por coincidencia genérica con “Demo”.

No se ejecutó Postman durante la preparación. Se ejecutó el flujo equivalente
por HTTP real con Python estándar, desde un proceso cliente separado de Django:

```powershell
.\.venv\Scripts\python.exe scripts/http_lab08.py
```

El script necesita el servidor activo, crea datos nuevos, verifica las respuestas
y guarda `docs/HTTP_RESULTS.json`. No ejecuta el JavaScript de Postman: las
aserciones equivalentes se ejecutan en Python. Si encuentra datos existentes
inválidos, sus comprobaciones de integridad de listados pueden fallar.

Para regenerar la colección a partir de la misma definición de solicitudes:

```powershell
.\.venv\Scripts\python.exe scripts/http_lab08.py --export
```

La ejecución confirmada registró 41 respuestas esperadas, incluidos 400 y 404;
los datos existentes se compararon antes y después y permanecieron intactos.
Los IDs numéricos del registro histórico ya se eliminaron y no deben reutilizarse.
