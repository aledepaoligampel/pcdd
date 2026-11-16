# Roadmap

Estado global de los changes. Las tareas de cada change se mantienen en su documento local, que no se versiona.

| Change | Alcance | Estado |
|---|---|---|
| public-release | Auditoría, repositorio público, PyPI y sitio con instalador en pcdd.dev | En curso; diseño de la landing cerrado y auditoría del historial hecha |
| packaging | `pyproject.toml`, licencia MIT, código en `src/pcdd_toolkit/` e instalación con uv/pipx desde Git | Completado; 57 tests, dos revisiones PASS e instalación desde GitHub verificada con uv y pipx; aceptación delegada autorizada |
| progreso-visible | Tareas nativas sincronizadas cuando estén disponibles y progreso visible en el chat | Completado y aceptado; 53 tests; panel nativo verificado en Claude Code; operaciones largas y bloqueos sin observar |
| v0-1 | Kit local, adaptadores, instalación segura y progreso con tiempo | Completado; 53 tests y pilotos en clientes reales; cierre delegado autorizado por el usuario |
| cli-experience | Interfaz es/en, logo, progreso y JSON explícito | Completado; presentación es/en, PTY y JSON verificados; cierre delegado autorizado |
| instruction-language | Instrucciones internas en inglés y descubrimiento genérico de contexto | Completado; idioma y continuidad entre sesiones verificados; cierre delegado autorizado |
| commit-skills | Skills de commits, atribución e inventario ampliado compatible | Completado; revisión sin escrituras y commit con staging ajeno preservado; cierre delegado autorizado |
| self-hosting | PCDD instalado en su propio repositorio, gate y actualización explícita | Completado y aceptado; 44 tests aprobados; continuación y descubrimiento verificados en sesiones nuevas de Codex y Claude |
| antigravity | Adaptador seleccionable, rutas compartidas y compatibilidad v0.4 | Completado y aceptado; 53 tests y dos revisiones PASS; piloto en Antigravity CLI satisfactorio |
| public-readme | README público en inglés, documentación y nueva publicación privada sin historial anterior | Completado y aceptado; README en inglés, 53 tests y dos revisiones PASS; repositorio privado recreado con un único commit raíz |

El repositorio es público; todavía no hay paquete en un registro. El paquete se instala desde el repositorio Git con uv o pipx.
