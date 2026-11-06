# Revisión de la rúbrica — 20 puntos

Fuente: cuatro criterios de 5 puntos del documento original. No se asigna una
nota definitiva: la evaluación corresponde al docente. El criterio 1.3 de
acreditación no añade puntos.

| Criterio | Comprobado en implementación/evidencia | Pendiente para la entrega | Situación |
| --- | --- | --- | --- |
| 1. Serializadores y validaciones (5) | Tres ModelSerializer, campos explícitos, IDs de solo lectura, relaciones anidadas, una correcta, atomic, PATCH y pruebas | Capturas C03/C04 y explicación con autor en el informe | Implementación alineada con excelente |
| 2. ViewSets y routers (5) | Tres ModelViewSet registrados en DefaultRouter; raíz, listado y detalle navegables; pruebas HTML y HTTP | Recorrido visual manual y capturas C05–C08 | Implementación alineada con excelente; evidencia visual pendiente |
| 3. Operaciones HTTP externas (5) | 41 solicitudes reales con urllib; cinco operaciones por recurso y códigos correctos, incluidos errores; registro JSON completo | Capturas C09/C11/C12; ejecutar Postman y C10 si se usa como evidencia adicional | Criterio técnico externo comprobado; Postman no ejecutado |
| 4. Repositorio y tabla API (5) | API_TABLE.md completo; colección y documentación preparadas localmente | Commit/push autorizados, C13/C15, informe con datos personales y capturas, carga al campus/C16 | Preparado localmente; entrega pendiente |

## Lista de cierre

- [x] Revisar los 12 pasos del documento y preservar el alcance de cada etapa.
- [x] Implementar pasos 1–6 y 10–11.
- [x] Probar HTML navegable automáticamente y GET HTML por HTTP real (paso 7).
- [ ] Completar recorrido visual manual y capturas de API navegable (paso 7).
- [x] Ejecutar las cinco operaciones por recurso con cliente HTTP externo (8).
- [x] Registrar campo ausente, tipo incorrecto y validación propia (9).
- [x] Preparar colección importable, 41 solicitudes con IDs dinámicos.
- [ ] Importar y ejecutar en Postman; sus scripts JavaScript aún no se ejecutaron.
- [x] Verificar 60 pruebas, check y ausencia de migraciones pendientes.
- [x] Comprobar que las pruebas externas no alteraron datos preexistentes.
- [ ] Completar identidad del estudiante/equipo y responsabilidades reales.
- [ ] Insertar capturas reales C01–C14; incluir tabla API en entrega.
- [ ] Autorizar y realizar commit/push; verificar GitHub y captura C15.
- [ ] Exportar informe y entregarlo al campus; captura C16 (paso 12).

La solución aspira a los 20 puntos por cobertura técnica, pero la entrega no
está concluida mientras falten evidencias, publicación y presentación al campus.
