# Uso local de PCDD v0.4

Requiere Python 3.9 o posterior. Sin dependencias de runtime ni servicios. Este kit no está publicado en un registro de paquetes. Licencia MIT.

## Instalar el comando

Con [uv](https://docs.astral.sh/uv/) (recomendado) o [pipx](https://pipx.pypa.io/), que instalan `pcdd` en un entorno aislado y lo agregan al `PATH`:

```sh
uv tool install pcdd --from git+https://github.com/aledepaoligampel/pcdd
# o
pipx install git+https://github.com/aledepaoligampel/pcdd
```

Mientras el repositorio sea privado se necesita acceso de lectura en GitHub. Desde un checkout local: `uv tool install /path/to/pcdd` o `pipx install /path/to/pcdd`. Para actualizar: `uv tool upgrade pcdd` o `pipx upgrade pcdd`. Después, desde el proyecto: `pcdd init --dry-run`, `pcdd init` y `pcdd doctor`.

## Ejecutar sin instalar

Desde un proyecto existente:

```sh
python3 /path/to/pcdd/pcdd.py init --dry-run
python3 /path/to/pcdd/pcdd.py init
python3 /path/to/pcdd/pcdd.py doctor
```

Para usar `pcdd` durante la sesión de terminal:

```sh
export PATH="/path/to/pcdd/bin:$PATH"
pcdd --version
```

Esto no modifica tu configuración global. Alternativamente usar siempre `python3 /ruta/pcdd.py`. `--project /ruta/destino` va antes del subcomando; por defecto se usa el directorio actual.

## Instalación

`init` instala Codex y Claude por defecto. `init --adapters codex`, `init --adapters claude` o `init --adapters antigravity` elige uno; se pueden combinar con comas, por ejemplo `init --adapters codex,claude,antigravity`. La v0.4 no cambia adaptadores de una instalación existente: una selección distinta se rechaza, incluso si comparte rutas. Elegí Antigravity al instalar en un proyecto nuevo; no borres el manifiesto de un proyecto existente para forzar la selección.

Se crea `.pcdd/core.md`, configuración y manifiesto, skills `pcdd-work`, `pcdd-review`, `pcdd-commit` y `pcdd-commit-review` en `.agents/skills` y/o `.claude/skills`, y una referencia delimitada en `AGENTS.md`. Claude recibe también una referencia en `CLAUDE.md`. El texto fuera de los bloques se conserva, incluso con cambios locales posteriores.

El agente se encarga de encontrar el contexto del proyecto y definir las validaciones durante el desarrollo autorizado. No necesitás indicarle un archivo de handoff ni editar la configuración a mano. Si aún no hay aplicación, las validaciones se incorporan con el primer scaffold y sus tests. Si ya existe, el agente revisa los scripts reales y preserva tu configuración.

También podés personalizar `.pcdd/config.json` manualmente. Ejemplo para un proyecto cuyo gate es `make ready`:

```json
{"schema":1,"gate":["make ready"],"database_gate":[]}
```

El agente ejecuta esos comandos según las autorizaciones de su entorno; el CLI no ejecuta shell procedente de configuración. Las convenciones propias van en `AGENTS.md`, no en archivos administrados.

Codex y Antigravity usan el mismo `AGENTS.md` y los mismos cuatro skills en `.agents/skills/`; se registran por separado en el manifiesto, sin duplicar archivos. Antigravity no requiere crear `GEMINI.md` ni modificar sus reglas globales. Gemini CLI no es un adaptador de esta versión. Abrí una sesión nueva del cliente elegido en el proyecto para comprobar descubrimiento y uso de skills. La validación del instalador no sustituye ese piloto.

## Change y avance

```sh
pcdd new primera-feature
pcdd time start primera-feature
pcdd time status primera-feature
pcdd time pause primera-feature
```

El agente redacta las specs y actualiza `pcdd/changes/primera-feature.md`. Tasks usa líneas `- [ ] T1 (S1) descripción`; `>` en curso, `!` bloqueada, `x` completada. El CLI valida IDs y estados y devuelve JSON con conteo y tiempo para que el agente lo comunique. No infiere aprobación humana del porcentaje. El resumen del agente usa el formato **PCDD · 2/3 tareas completadas · 2 min 48 s**, sin aclaraciones sobre el inicio o la pausa del reloj.

Al empezar o retomar un change y cuando cambia el estado de una tarea, el agente muestra un bloque breve en el chat. Ejemplo ilustrativo:

> **PCDD · 1/3 tareas completadas**
>
> - Completada · T1 · Definir los criterios de aceptación.
> - En curso · T2 · Implementar el cambio.
> - Pendiente · T3 · Ejecutar las verificaciones.
>
> Siguiente paso: verificar el comportamiento implementado.

Los IDs, estados y conteos salen del documento del change mediante el CLI. En listas largas se muestran solo las tareas relevantes, con el conteo total. Durante operaciones largas, el agente explica qué sigue ejecutándose y qué resultado falta; ante un bloqueo, indica qué puede resolverlo. Al cerrar el tramo agrega el tiempo medido. Las tareas completas no sustituyen tu prueba y confirmación del resultado.

Además del bloque en el chat, el agente usa las herramientas de tareas nativas que exponga la sesión para reflejar las tareas del change al empezar o retomar y en cada transición. El documento se actualiza primero; el panel conserva los IDs de PCDD en las etiquetas y no mantiene otro plan. Si el cliente no admite un estado, por ejemplo bloqueada, la etiqueta o descripción lo expresa. Si faltan las herramientas, el agente avisa al inicio que mostrará progreso en texto; si fallan, comunica la limitación y continúa con el documento y el bloque del chat.

En Claude Code se pueden habilitar las herramientas nativas solo para una sesión, sin modificar la configuración global:

```sh
CLAUDE_CODE_ENABLE_TODO_TOOLS=1 claude
```

La [documentación oficial de Claude Code](https://code.claude.com/docs/en/tools-reference.md#task-tool-availability) describe la disponibilidad por modelo y esta opción. La prueba local con Claude Code 2.1.323 verificó llamadas reales a `TaskCreate`, `TaskUpdate` y `TaskList`, con transición pendiente → en curso → completada. Fue una ejecución no interactiva: la visualización del panel requiere comprobarla en el cliente. La disponibilidad en Codex también depende de las herramientas expuestas en esa sesión; instalar PCDD no las habilita.

`start` inicia un intervalo; `pause` y `stop` lo cierran. El tiempo cerrado y el intervalo abierto se muestran separados. Al abandonar un chat con intervalo abierto, usar `pcdd time abandon primera-feature` al retomar: registra incompletitud sin sumar tiempo desconocido. Después `start`. No hay detección automática de cierre del chat ni estimación del tiempo restante.

## Actualizar y recuperar

```sh
pcdd update --dry-run
pcdd update
pcdd rollback
```

`update` sincroniza los assets de la copia local del CLI con ese proyecto. No descarga versiones ni modifica otros repositorios. Para actualizar la herramienta, reemplazá su distribución local y luego previsualizá la actualización por proyecto. No existe un comando `upgrade` en v0.4.

Se rechazan archivos administrados modificados o ausentes, symlinks en rutas administradas y manifiestos incompatibles. Resolvé un conflicto explícitamente guardando tus personalizaciones en instrucciones del proyecto y restaurando la versión administrada original si decidís continuar. No hay `--force` ni merge automático.

`rollback` revierte la última instalación/actualización y se niega si algún archivo afectado recibió modificaciones posteriores. Conserva documentos de changes y tiempos. Las carpetas vacías pueden permanecer. Solo se mantiene una reversión, no un historial ilimitado ni desinstalador completo.

Si un proceso se interrumpe, `doctor` informa la transacción pendiente. Ejecutá `pcdd recover` para restaurar los archivos previos, no para continuar una actualización parcial. Si queda `.pcdd/lock`, verificá que el PID guardado no esté ejecutando una operación PCDD antes de borrar manualmente ese archivo. No borres locks de procesos activos. Archivos temporales `.pcdd-write-*` de procesos muertos pueden quedar; no se consideran archivos del cliente ni bloquean futuras escrituras.

La recuperación cubre interrupciones del proceso. No promete durabilidad frente a pérdida de energía, corrupción de disco o escritores externos simultáneos. Los manifiestos y journals locales no son una frontera de seguridad frente a alguien con escritura en el repositorio.

## Validación

En el repo de PCDD: `make ready`. Tests por CLI, exit code y archivos de proyectos temporales. No requieren base de datos ni acceso a red.

## Idioma y salida (v0.2)

```sh
pcdd init --lang es
pcdd init --lang en
pcdd language es
pcdd language en
pcdd language auto
pcdd language
```

`--lang` vale solo para esa ejecución. `language es/en` guarda una preferencia del usuario en `$XDG_CONFIG_HOME/pcdd/preferences.json` o `~/.config/pcdd/preferences.json`; conserva otras claves. `language auto` vuelve a detección automática. Un lock pendiente de preferencias indica una operación activa o interrumpida: verificá que no haya un proceso PCDD usando ese archivo antes de retirarlo. No se escribe configuración global durante init ni por elegir --lang.

Prioridad: opción explícita, preferencia guardada, LC_ALL, LC_MESSAGES y LANG (primera no vacía). C/POSIX no indican idioma; en macOS se consulta AppleLanguages mediante defaults con timeout. Un idioma no soportado usa español; en otros sistemas sin idioma útil también. Solo es/en están soportados inicialmente.

El idioma afecta mensajes, ayuda y errores del CLI. El núcleo, las skills, los bloques administrados de AGENTS.md/CLAUDE.md y la plantilla fuente se distribuyen siempre en inglés. El agente responde en el idioma del usuario y redacta los documentos en el idioma acordado para el proyecto; si no hay uno, usa el del usuario. Las citas y aprobaciones se conservan textualmente. El logo conserva el nombre completo en inglés; la frase inferior se traduce.

`pcdd new` crea una plantilla en inglés; el agente adapta su contenido al idioma del proyecto. El encabezado `## Tasks`, los IDs y los marcadores de tareas se mantienen porque el CLI los interpreta. La plantilla nueva usa `Continuation`; el agente también reconoce `Continuación` y las convenciones existentes. `update` no traduce ni reemplaza documentos de changes anteriores. El idioma de la conversación no se deduce de `--lang`.

La bienvenida aparece en init/update. El indicador gira solo durante operaciones reales y en terminal interactiva; no hay pausas añadidas. Salida redirigida, TERM=dumb y NO_COLOR desactivan animación. Colores automáticos solo en terminal compatible: logo cian, éxitos verdes, avisos amarillos, errores rojos y textos secundarios atenuados. NO_COLOR, TERM=dumb, salida redirigida y --json los desactivan. Las etiquetas siguen expresando el significado sin depender del color. El símbolo pasa a `>_` si la terminal no admite Unicode.

### Migración de scripts desde v0.1

La salida por defecto ahora es humana. Los scripts y agentes deben agregar `--json`:

```sh
pcdd init --dry-run --json
pcdd --json doctor
pcdd time status primera-feature --json
```

Las claves y mensajes de error de máquina permanecen en inglés e independientes del idioma. Errores JSON se escriben en stdout como un único objeto `error` (code/message), con exit code no cero y sin texto adicional en stderr. Help y version también tienen envoltorio JSON al usar --json; el contenido de help está traducido. `acceptance` en time usa el código `requires_user_confirmation`. Los resultados de init/update se emiten solo cuando terminó la operación; una falla no produce un informe de éxito previo.

Se mantiene el esquema 1. La v0.4.0 reconoce el inventario de dos skills de v0.1.0/v0.2.0 y el de cuatro de v0.3.0; actualiza al inventario vigente de cuatro skills al ejecutar `update` (también al repetir `init`). `pcdd update --dry-run` muestra los archivos nuevos sin escribir. Si ya existe un archivo no administrado en el destino de un skill nuevo, la operación se rechaza sin sobrescribirlo, incluso si su contenido coincide. `rollback` restaura el inventario anterior y retira los skills agregados, siempre que no hayan recibido modificaciones posteriores. No uses un ejecutable anterior sobre la instalación ampliada: para volver, ejecutá primero `rollback` con el CLI nuevo. Actualizar el ejecutable no modifica por sí solo proyectos anteriores.

## Empezar sin un prompt especial

Después de init, abrí una sesión nueva de un cliente compatible en la carpeta y describí tu objetivo, por ejemplo «empecemos con el proyecto» o «continuemos con la búsqueda». El agente recibe las instrucciones mediante AGENTS.md/CLAUDE.md, descubre documentos relevantes y pregunta solo por decisiones faltantes. No ejecuta trabajo automáticamente al instalar: espera tu pedido. La documentación de contexto puede tener cualquier nombre y no hace falta crear un archivo adicional de handoff. La selección y lectura efectiva depende del cliente y sigue pendiente de piloto humano completo.

## Seguir en otra sesión

Pedile al agente **«Guardá el avance para seguir en una sesión nueva»**. Guardará el punto de continuación en el documento del change, con el trabajo pendiente y la evidencia relevante; cerrará el intervalo de tiempo sin hacer un commit automático.

Abrí una sesión nueva en el mismo proyecto y pedile **«Continuá desde donde quedamos»**. Si hay varios changes activos, indicá cuál. El agente debe contrastar la nota con el estado actual y conservar las aprobaciones anteriores. Son instrucciones de conversación, no comandos `pcdd`.

No hace falta esperar al 90 % de contexto ni disponer de un servicio de memoria externa. La skill mantiene puntos de continuación al cerrar unidades de trabajo. Este protocolo orienta al agente; no controla el mecanismo de compactación del cliente ni garantiza que un modelo siempre lo cumpla.


## Commits con el agente

Los skills se invocan en la conversación, no como subcomandos del CLI. Después de instalar o actualizar, abrí una sesión nueva para que el cliente los descubra:

- `pcdd-commit`: «Commiteá los cambios de esta feature». Inspecciona el diff, conserva trabajo y staging ajenos, ejecuta los checks y crea una unidad coherente dentro del alcance autorizado.
- `pcdd-commit-review`: «Organizá estos cambios en commits y crealos». Presenta mensajes y archivos por intención y dependencias, y ejecuta el plan autorizado.
- «Usá pcdd-commit-review solo para proponer un plan, sin modificar Git» permite revisar sin cambiar archivos, índice ni historial.

Invocar explícitamente el skill autoriza su operación salvo que el pedido la limite a revisión. No exige confirmar otra vez lo mismo; el control de alto riesgo sigue requiriendo gate, revisión independiente y aprobación de su resumen antes del commit. `pcdd-review` evalúa corrección y riesgos; `pcdd-commit-review` organiza el historial. Pedir un commit no autoriza push, PR ni publicación.

El núcleo prohíbe agregar `Co-Authored-By`, firmas textuales o atribuciones de IA. Se conserva la identidad Git y se respeta la firma criptográfica configurada, así como los hooks. Si el proyecto no define convención de mensajes, el valor por defecto es Conventional Commits en inglés. No hay dependencia de comandos ni rutas de otros proyectos y los skills existentes `git-commit` / `git-commit-review` no se reemplazan.


## Desarrollar PCDD con PCDD

Este repositorio tiene PCDD instalado para Codex y Claude. Abrí una sesión nueva en su carpeta para que el cliente descubra los skills. `AGENTS.md` conserva las convenciones propias; `.pcdd/core.md` define el flujo compartido y `.pcdd/config.json` configura `make ready` como gate, sin gate de base.

Usá el ejecutable de este checkout para no depender de otra versión en PATH:

```sh
python3 pcdd.py doctor
python3 pcdd.py --json time status self-hosting
```

Las fuentes distribuibles viven en `src/pcdd_toolkit/assets/`; el código del CLI, en `src/pcdd_toolkit/`, y `pcdd.py` es solo el lanzador del checkout. Las copias de `.pcdd/core.md`, `.agents/skills/` y `.claude/skills/` son archivos administrados: no se editan a mano. Durante un cambio de instrucciones se trabaja sobre las fuentes conservando la versión instalada. Después de validar el cambio, actualizar explícitamente esta instalación dentro del alcance autorizado:

```sh
make ready
make package-check   # opcional; construye e instala un wheel en un venv temporal, requiere red
python3 pcdd.py update --dry-run
python3 pcdd.py update
python3 pcdd.py doctor
```

Abrí otra sesión para cargar los skills actualizados. `doctor` comprueba la instalación contra su manifiesto, no que coincida con fuentes todavía en desarrollo; el preview de `update` muestra esa diferencia. No hay autoactualización ni un enlace que cambie silenciosamente las instrucciones mientras se desarrolla.

Los changes existentes conservan sus citas y evidencia. Los intervalos se registran desde que se inicia el reloj, sin reconstruir tiempo anterior; una pausa para esperar al usuario debe cerrar el intervalo. Los locks, journals y temporales de instalación siguen excluidos de Git, mientras que la configuración, manifiesto y snapshots forman parte de la instalación del proyecto. Autoincorporarse no autoriza commits ni publicaciones.

## Probar Antigravity

En una carpeta descartable, ejecutar desde el checkout:

```sh
python3 pcdd.py --project /path/to/test-project init --adapters antigravity --dry-run
python3 pcdd.py --project /path/to/test-project init --adapters antigravity
python3 pcdd.py --project /path/to/test-project doctor
```

La carpeta debe existir. El preview no escribe. Una operación que aplica cambios puede dejar la carpeta `.pcdd/` vacía al adquirir y retirar el lock aunque después rechace un conflicto; eso no implica que se hayan instalado archivos ni se hayan sobrescrito archivos del cliente. Abrir una sesión nueva de Antigravity allí y pedir: «Sin modificar archivos, identificá las instrucciones y skills de este proyecto y explicá cómo retomarías un change y qué necesitás antes de hacer un commit de alto riesgo». Verificar descubrimiento de las cuatro skills, lectura del núcleo y distinción entre tareas completas y aceptación humana. La prueba automática del CLI no garantiza el cumplimiento de instrucciones por el agente. Para un commit de alto riesgo, el entorno debe ofrecer revisor y verificador independientes; de lo contrario, PCDD indica detener ese paso.
