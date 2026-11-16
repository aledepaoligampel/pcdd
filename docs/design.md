# Diseño inicial

## Distribución

Repositorio independiente en `/path/to/pcdd`. El CLI administra instrucciones versionadas; los agentes interpretan el flujo. Sin dependencia obligatoria de MCP, memoria externa, nube o editor.

## Propiedad de archivos instalados

- `AGENTS.md` pertenece al cliente. `init` agrega un bloque delimitado que remite al núcleo; conserva los bytes fuera de su bloque. Si el archivo no existe, crea uno mínimo. Reinstalar no duplica el bloque.
- `.pcdd/core.md` y las skills distribuidas pertenecen al instalador. El núcleo es breve; la referencia obliga a consultarlo, no garantiza una importación automática de archivos arbitrarios.
- `.pcdd/config.json` contiene configuración del cliente: comandos, rutas y adaptadores. Se preserva al actualizar.
- `.pcdd/installation.json` registra versión y huellas de archivos administrados. Se detectan modificaciones antes de reemplazar.
- Los documentos de changes y sus registros pertenecen al proyecto. Una actualización no los reemplaza por plantillas.
- Adaptadores de Codex, Claude Code y Antigravity exponen las mismas instrucciones fuente en las ubicaciones requeridas. No pisan skills o configuración ajenas.

`update --dry-run` muestra el plan sin escribir. `update` valida todos los conflictos antes de aplicar. Un archivo administrado modificado requiere resolución explícita; sin fusiones automáticas silenciosas. La reversión solo restaura archivos administrados cuando hacerlo no borra cambios posteriores del cliente.

Actualizar el ejecutable no actualiza por sí solo los repositorios. Cada proyecto fija su versión. El ejecutable se distribuye como paquete Python (`pyproject.toml`, nombre `pcdd`, código en `src/pcdd_toolkit/` con assets y locales como datos del paquete) y se publica en PyPI; se instala con `uv tool install pcdd`, `pipx install pcdd` o el instalador de pcdd.dev (que instala uv si falta). El paquete npm `pcdd` (`npm/`) es solo un lanzador: `npx pcdd …` ejecuta `uv tool run pcdd@<versión> …`, fijado a la release de PyPI con la misma versión que el paquete npm (cada release publica en ambos), con los mismos argumentos y código de salida; sigue requiriendo uv y Python, y no duplica el código del CLI. El paquete importable no se llama `pcdd` porque `pcdd/changes/` ocupa ese nombre en la raíz de los proyectos, incluido este checkout, donde es local y no se versiona. `pcdd.py` queda como lanzador del checkout.

## Flujo y contexto

Las instrucciones para agentes, las plantillas fuente y los bloques administrados se mantienen en inglés como versión única. La salida del CLI se traduce según su preferencia de idioma; esa preferencia no decide el idioma de la conversación ni de los documentos. El agente responde en el idioma del usuario y redacta documentos en el idioma acordado por el proyecto (o el del usuario si no hay acuerdo). Las citas de pedidos y aprobaciones se conservan textualmente.

La plantilla nueva usa `Continuation`. Los documentos existentes conservan sus encabezados, incluyendo `Continuación`; el agente reconoce su función sin migrarlos. `## Tasks` y la sintaxis de tareas permanecen estables porque el CLI los interpreta. El descubrimiento inicial busca documentación pertinente por su contenido y función, sin requerir un nombre de archivo de handoff ni crear documentos solo para cumplir un nombre.

Cuatro skills: trabajo sustancial (`pcdd-work`), revisión independiente (`pcdd-review`), commit coherente (`pcdd-commit`) y organización de commits (`pcdd-commit-review`). No equivalen a subagentes ni se cargan por rutina. El contexto de continuación contiene próximo paso, bloqueo y evidencia vigente; no duplica todo el Log.

Specs: cita original y criterio verificable, distinguiendo requisitos del usuario de propuestas del agente. Las reglas heredadas no se adoptan automáticamente.

Roadmap: estado de la feature. Documento: estado de tareas (pendiente, en curso, bloqueada, completada). La aceptación humana es distinta de completar implementación.

## Progreso y tiempo

Al iniciar o retomar un change y al cambiar el estado de sus tareas, el agente muestra un bloque breve con el conteo, las tareas completadas relevantes, la tarea activa y el próximo paso o bloqueo. Cada línea identifica la tarea y su estado. Para listas largas muestra un subconjunto pertinente; el conteo del CLI incluye todas las tareas. El documento del change es la única fuente de tareas y estados; el chat y las herramientas del cliente no mantienen otro plan independiente. Si no hay tarea activa, indica qué queda pendiente, incluida la aceptación humana cuando corresponda.

Durante operaciones largas comunica qué tarea sigue ejecutándose y qué resultado falta conocer, sin porcentajes inventados, éxitos anticipados ni un bloque por comando. La presentación funciona mediante mensajes del agente, sin depender de una interfaz específica del cliente.

Cuando la sesión expone herramientas de tareas nativas, el agente las usa como vista derivada del change al empezar o retomar y después de cada transición. Actualiza primero el documento, conserva IDs de PCDD en etiquetas, reconcilia entradas existentes y preserva tareas ajenas. Un estado sin equivalente nativo queda explícito en la etiqueta o descripción. Si las herramientas faltan o fallan, comunica la limitación y conserva el documento y el bloque en texto. No altera ajustes del cliente ni crea objetivos o sesiones como sustituto. Verificar llamadas nativas no acredita el renderizado visual del panel.

Al cerrar un tramo añade la duración medida al encabezado, por ejemplo: «PCDD · 4/6 tareas completadas · 18 min», sin estado del reloj ni detalles del registro. Usa el total cerrado confirmado por el CLI. Si hay tiempo incompleto que afecte la interpretación, lo explica por separado. El cociente cuenta tareas; no mide esfuerzo ni predice tiempo restante.

El reloj y los intervalos se registran de forma determinista. Tests cuentan; esperas de aprobación se separan. Sesiones sin cierre quedan incompletas y no se suman como si se conociera su duración. El total es tiempo transcurrido registrado, no tiempo de CPU ni horas humanas. No se prometen detección perfecta de inactividad ni instrumentación idéntica de clientes.

## Límites del piloto

Sin dashboard ni `status --watch` en v0.1. Se prioriza el reporte del agente. Se prueba instalación nueva, repo existente, reinstalación, actualización, conflictos y reversión; además, cambio pequeño, feature retomada y cambio riesgoso. Medir contexto inicial, tiempo, intervenciones y tokens cuando estén disponibles; no inventar porcentajes de ahorro.

## Continuación entre sesiones

Frases de referencia: «guardar el avance» y «continuar desde donde quedamos». Se mantienen en la skill de trabajo, con una referencia breve desde el núcleo. El punto de continuación vive en el documento del change; no se agrega una segunda base de estado ni dependencia de un servicio de memoria externa. Contiene estado operativo, referencias a specs/aprobaciones, evidencia y siguiente acción. Al retomar se contrasta con el trabajo actual; el tiempo desconocido queda incompleto y no se commitea automáticamente.

Este ajuste es de instrucciones y documentación. La adopción y efectividad entre sesiones requiere piloto humano, además de validar que el instalador distribuye las skills actualizadas.


## Inventario ampliado y commits (v0.3)

El manifiesto conserva esquema 1 y valida un inventario exacto según la versión: v0.1.0/v0.2.0 incluyen los dos skills originales, v0.3.0 incluye cuatro. Un manifiesto actual incompleto no se acepta como instalación anterior. Una versión desconocida se rechaza sin escribir. La lista compartida de skills gobierna instalación, validación y rutas permitidas en recuperación.

Actualizar desde el inventario anterior verifica sus archivos y preflight de los destinos nuevos antes de escribir. Un archivo preexistente no administrado en un destino nuevo es un conflicto, aun con bytes idénticos; el instalador no adquiere su propiedad implícitamente. Los journals conservan el estado anterior y `rollback`/`recover` pueden restaurar el inventario y retirar archivos nuevos. La configuración del proyecto y sus documentos permanecen propios. El ejecutable anterior se vuelve a usar solo después de revertir con el nuevo.

El núcleo contiene la política de atribución para cualquier commit; los skills de Git conservan identidad, firma criptográfica, hooks y trabajo ajeno. Las convenciones del proyecto prevalecen sobre el valor por defecto de Conventional Commits en inglés. La invocación autoriza la operación indicada salvo revisión sola; no elimina el control de alto riesgo ni autoriza publicación. Organizar commits no sustituye revisión de código y verificación independiente. No se imponen PRs, ramas ni delegación rutinaria.


## Uso de PCDD dentro de PCDD

El repositorio instala los mismos assets que distribuye a otros proyectos, mediante el CLI normal, para ambos adaptadores. Su configuración define `make ready` y ningún gate de base. `AGENTS.md` conserva únicamente las convenciones del proyecto y el bloque administrado de entrada; `CLAUDE.md` remite a esas instrucciones y al núcleo.

Las fuentes en `src/pcdd_toolkit/assets/` y los snapshots instalados son archivos distintos. Se modifican las fuentes durante el desarrollo; los snapshots permanecen fijos hasta validar y ejecutar una actualización explícita. Esta separación permite desarrollar una regla sin cambiar inmediatamente el flujo que guía ese mismo trabajo. No hay enlaces simbólicos ni sincronización automática. La instalación propia complementa los tests en proyectos temporales; no los sustituye.

Se conservan los requisitos y las aprobaciones históricas. Por decisión explícita del usuario, la documentación distribuida omite citas de procedencia, identificando como resúmenes el alcance conservado. Los registros de tiempo nuevos empiezan en intervalos explícitos, sin estimar trabajo anterior. Las autorizaciones de commit y publicación del repositorio se conservan.

## Antigravity y rutas compartidas (v0.4)

Antigravity es una selección explícita de instalación. Usa `AGENTS.md` como entrada y `.agents/skills/<name>/SKILL.md`, las mismas rutas de Codex. El inventario es la unión de rutas de los adaptadores seleccionados: una selección Codex + Antigravity conserva una sola copia de cada archivo. Claude mantiene `CLAUDE.md` y `.claude/skills/`. No se modifica la configuración global ni se agrega soporte de Gemini CLI.

La selección por defecto sigue siendo Codex + Claude. El manifiesto conserva esquema 1: v0.4.0 permite Antigravity y versiones v0.1–v0.3 solo permiten sus adaptadores originales. Se rechazan adaptadores repetidos y listas de archivos con estructura inválida. `update` verifica y conserva la selección; no se agrega un adaptador por compartir rutas. Cambiar la selección de una instalación existente sigue requiriendo otro plan.

La actualización desde versiones anteriores sigue siendo explícita y reversible con el CLI nuevo. Las instrucciones fuente no cambian por este adaptador; los snapshots del propio repositorio permanecen fijos. La compatibilidad de ubicación y las pruebas del instalador no equivalen a aceptación del comportamiento en una sesión real.
