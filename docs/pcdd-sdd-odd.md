# PCDD: idea y comparación con SDD y ODD

PCDD organiza el trabajo entre una persona y un agente de programación alrededor de cambios verificables. Define qué contexto necesita el agente, cuándo conservar especificaciones y tareas, cómo retomar una sesión y qué evidencia reunir antes de considerar terminado el trabajo.

**Progressive Change-Driven Development** significa avanzar por pasos verificables e incorporar definición, contexto y controles a medida que el cambio los necesita. El criterio considera comprensión, riesgo y continuidad. Una modificación breve en permisos puede requerir más revisión que una pantalla entera.

## Tres formas de organizar el trabajo

La comparación es conceptual: SDD y ODD no implican una configuración universal ni una cantidad fija de documentos o agentes.

| Enfoque | Idea organizadora | Énfasis práctico |
|---|---|---|
| SDD — Spec-Driven Development | La especificación orienta implementación y verificación | Definir el comportamiento esperado y mantener su relación con planes, código y pruebas |
| ODD — Organic Driven Development | El flujo se adapta al pedido y al contexto disponible | Ejecutar trabajo entendido directamente y conservar contexto para trabajo sustancial |
| PCDD — Progressive Change-Driven Development | El cambio recibe definición y controles según su necesidad | Specs aprobadas para trabajo sustancial, revisión independiente para alto riesgo y registros locales de continuación y aceptación |

Los enfoques pueden compartir requisitos, pruebas, tareas y revisión humana. La diferencia práctica depende de los mecanismos y reglas de cada implementación. PCDD concreta sus decisiones en un CLI local, documentos Markdown, gates propios del proyecto y skills para el agente. No requiere memoria externa ni un stack de aplicación determinado.

## Aplicación en PCDD

- Trabajo pequeño, entendido y acotado: ejecución directa, evaluando su riesgo.
- Trabajo sustancial: especificaciones verificables aprobadas, tareas y evidencia en un documento de change.
- Trabajo de alto riesgo: gate, revisión de código, verificación independiente y aprobación humana antes del commit.
- Continuación: recuperar contexto relevante, comparar con el estado real y mantener el próximo paso.
- Cierre: prueba y aceptación del usuario; completar tareas no equivale por sí solo a aceptar el resultado.

## Capacidades y límites

El CLI instala y actualiza instrucciones, valida archivos, cuenta tareas y registra intervalos explícitos de trabajo. Las instrucciones guían decisiones del agente. No son una barrera técnica que garantice obediencia de cualquier modelo ni ejecutan por sí solas todas las revisiones.

El conteo de tareas no mide esfuerzo y el reloj no reconstruye tiempo sin registrar. No se ha demostrado una ventaja comparativa en tokens, velocidad o calidad frente a otras configuraciones de SDD u ODD. El valor propuesto es conservar suficiente estructura para entender, retomar y verificar cada cambio.
