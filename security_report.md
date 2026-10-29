# Informe de seguridad

## 1. Alcance y fecha

**Fecha:** 2026-10-29. Revisión estática del cliente y flujo Python, los agentes,
la configuración versionada y el despliegue MCP local de este repositorio.
Se revisaron autenticación, autorización y separación de recursos, validación de
entradas, inyección, secretos y exposición de datos. No se modificó código de
producto.

El servidor MCP procede de una imagen externa cuya implementación no está en
este repositorio. No se examinó ni ejecutó esa imagen, Copilot, GitHub ni
ninguna aplicación generada. Por tanto, no se puede afirmar que exista o no
un IDOR en el servidor o en las aplicaciones generadas. Los riesgos descritos
se refieren a los límites y comportamientos observables en esta copia.

## 2. Resumen

| Severidad | Hallazgos |
|---|---:|
| Crítica | 0 |
| Alta | 4 |
| Media | 2 |
| Baja | 0 |

Las severidades consideran el uso del flujo para generar artefactos de un
equipo; la exposición efectiva del MCP y el acceso a artefactos locales
dependen también del entorno. Ninguna corrección propuesta se ha implementado
ni verificado.

## 3. Hallazgos y correcciones propuestas

### S1. Publicación de MCP en todas las interfaces con herramientas amplias

- **Severidad:** alta, condicionada a la accesibilidad de red y a los controles
  reales del servidor.
- **Ubicación:** `support/mcp-local/compose.yaml:3-19`;
  `support/mcp-local/Dockerfile:11-13`;
  `support/mcp-local/start-mcp.sh:29-34`.
- **Evidencia:** Compose publica `8083:8080` y `8081:8080` sin limitar la IP
  del host y configura `MCP_TOOL_GROUPS: all`. El arranque entrega al servicio
  el token de GitHub del operador. El Dockerfile arranca `mcp-proxy`, pero esta
  copia no permite comprobar qué autenticación y autorización exige el proxy o
  el servidor ni si restringen cada recurso y operación.
- **Impacto:** si el servicio publicado acepta solicitudes no autorizadas o
  insuficientemente autorizadas, otro equipo de la red podría actuar con los
  privilegios GitHub del operador y consultar o modificar recursos ajenos.
  La publicación no demuestra por sí sola que la autenticación sea vulnerable.
- **Corrección propuesta:** publicar únicamente en loopback por defecto,
  habilitar solo herramientas necesarias, usar credenciales GitHub de mínimo
  privilegio y exigir autenticación y autorización en el servidor para cada
  operación y recurso. Si se requiere acceso remoto, usar TLS y una política
  explícita de red e identidad; no depender solo de la IP de escucha.
- **Comprobación de la corrección:** con un servidor de prueba y dos identidades
  ficticias A y B, verificar que el puerto no es accesible desde otra máquina
  en la configuración local; comprobar rechazo sin credenciales y con
  credenciales inválidas, y que A no puede leer ni modificar un recurso privado
  de B mediante ninguna herramienta expuesta. Verificar que la herramienta no
  necesaria no aparece ni puede invocarse.

### S2. La clave MCP puede enviarse por HTTP sin protección de transporte

- **Severidad:** alta cuando se configura un endpoint no local o se atraviesa
  una red no confiable.
- **Ubicación:** `mcp_projects.py:17-18,34-40,68-76`;
  `.env.example:12-13`; `README.md`, sección «Conectar el backlog».
- **Evidencia:** el cliente construye la cabecera `Authorization: Bearer …`
  a partir de `PROJECTS_MCP_API_KEY` y envía la solicitud a la URL configurada
  sin exigir HTTPS. El ejemplo usa HTTP en localhost y el README también
  contempla un endpoint del taller. La prueba local usó solo una clave ficticia.
- **Impacto:** si se configura HTTP remoto, un observador o intermediario de
  red puede capturar la clave y el backlog o alterar las respuestas.
  El tráfico exclusivamente loopback no implica por sí mismo exposición a la red.
- **Corrección propuesta:** rechazar HTTP para destinos no loopback; mantener
  HTTPS con validación de certificados y nombres, rechazar redirecciones a
  destinos inseguros y permitir HTTP local solo como excepción explícita de
  desarrollo. Documentar la política y proteger también el servidor remoto.
- **Comprobación de la corrección:** con transporte simulado, comprobar que
  una URL HTTP remota y una redirección HTTPS→HTTP se rechazan antes de enviar
  credenciales; que un certificado inválido falla; que HTTPS válido funciona
  y que HTTP loopback funciona únicamente con la excepción de desarrollo.

### S3. La aprobación humana puede producirse sin una decisión válida

- **Severidad:** alta.
- **Ubicación:** `main.py:693-712,784-829,1001-1013`.
- **Evidencia:** `hitl_approve` devuelve `("s", "")` al recibir EOF. También
  acepta cualquier última palabra terminada en `s`, como `datos`. El preview
  muestra por defecto solo las primeras 45 líneas y aun así permite aprobar y
  guardar todo el resultado. En pruebas locales se confirmó cada comportamiento.
- **Impacto:** una entrada cerrada o ambigua puede aprobar código o informes
  sin intervención válida; contenido fuera del preview puede guardarse sin
  haber sido mostrado, debilitando la barrera humana ante código inseguro o
  instrucciones maliciosas.
- **Corrección propuesta:** tratar EOF como rechazo o interrupción, aceptar
  únicamente opciones exactas y permitir revisar el resultado completo antes
  de aprobarlo. Registrar una aprobación explícita por etapa; no sustituir la
  revisión de seguridad por un preview parcial.
- **Comprobación de la corrección:** simular EOF, `datos`, `s` y `n`: solo
  `s` debe aprobar, `datos` debe volver a pedir entrada y EOF debe detener el
  flujo sin escribir un estado aprobado. Con un resultado de 46 líneas,
  verificar que la línea 46 se puede revisar antes de la aprobación y que se
  guarda exactamente el contenido revisado.

### S4. Reanudación mezcla recursos de proyectos con el mismo título

- **Severidad:** alta en entornos compartidos o con distintos backlogs.
- **Ubicación:** `main.py:427-456,920-943,968-974`.
- **Evidencia:** el checkpoint se identifica solo por `feature_title`; si el
  título coincide se reutilizan pasos aprobados y se vuelve a extraer su
  código. En una prueba aislada, el proyecto ficticio B con el mismo título
  reutilizó la salida aprobada del proyecto ficticio A.
- **Impacto:** se pueden incorporar artefactos de otro proyecto o persona,
  revelar su contenido en el contexto de los agentes y tratar como aprobada
  una implementación correspondiente a otro recurso. También sucede si
  cambia el contenido del mismo issue sin cambiar su título. La prueba no
  demuestra un IDOR en el servidor MCP.
- **Corrección propuesta:** vincular el checkpoint y el directorio de salida a
  identificadores estables del servidor, owner, repositorio, proyecto e issue,
  junto con una versión o hash del contenido relevante. Comprobar la identidad
  y permisos actuales antes de reanudar; ante ausencia o discrepancia, rechazar
  la reanudación y solicitar una nueva aprobación. Aislar artefactos por
  ejecución y proteger sus permisos.
- **Comprobación de la corrección:** ejecutar dos proyectos ficticios con el
  mismo título y distintos IDs y salidas: B no debe leer, mostrar ni reescribir
  la salida de A. Repetir con el mismo ID y contenido cambiado y con permisos
  retirados; no deben reutilizarse aprobaciones anteriores.

### S5. Contenido externo se incorpora como instrucciones para el modelo

- **Severidad:** media.
- **Ubicación:** `mcp_projects.py:235-259,399-430`;
  `agents/architect.py:16-20`, `agents/backend.py:16-20`,
  `agents/frontend.py:16-20`; `main.py:945-950,984-1001`;
  `lab_copilot/runtime.py:29-43`.
- **Evidencia:** el título, descripción y criterios del backlog se concatenan
  directamente en las tareas y en el contexto del arquitecto; los outputs
  aprobados se propagan a etapas posteriores. El modelo no dispone de
  herramientas en esta integración, pero su texto se puede guardar como código.
- **Impacto:** quien pueda editar un issue puede intentar que instrucciones
  dentro de su descripción influyan en el código generado o el informe de
  seguridad. No se ha ejecutado un modelo ni demostrado que una carga concreta
  logre modificar su respuesta.
- **Corrección propuesta:** tratar el backlog y los outputs como datos no
  confiables, separarlos y etiquetarlos frente a las instrucciones de sistema,
  aplicar controles deterministas al código generado y exigir revisión completa
  antes de guardarlo o ejecutarlo. La delimitación por sí sola no garantiza
  inmunidad a la inyección de prompts.
- **Comprobación de la corrección:** en un entorno de prueba controlado,
  incorporar a un issue ficticio instrucciones para omitir autorización o
  incluir una cadena marcadora; verificar que no se tratan como mandato, que
  la revisión y las pruebas de autorización se ejecutan y que ninguna salida
  insegura se aprueba automáticamente. Registrar modelo y resultados reales.

### S6. Backlog y resultados sensibles pueden persistir o divulgarse

- **Severidad:** media, dependiendo de la sensibilidad y de los permisos del
  entorno.
- **Ubicación:** `main.py:397-399,435-456,605-609,659-668,939-950`;
  `lab_copilot/runtime.py:29-46`; `.gitignore:1-9`.
- **Evidencia:** el brief del backlog y el contexto se envían a Copilot; los
  resultados completos se guardan en specs y checkpoint mediante `write_text`
  y CrewAI se ejecuta con `verbose=True`. No se establecen permisos restrictivos
  específicos, cifrado, retención ni redacción en estas rutas. `output/` y
  `.env` están ignorados por Git, lo que no restringe el acceso local ni evita
  la transmisión al proveedor.
- **Impacto:** datos privados del backlog, salidas o secretos que el usuario
  incluya pueden quedar en consola, archivos o el servicio de modelo y ser
  accesibles a personas o sistemas con permisos sobre ellos.
- **Corrección propuesta:** clasificar y minimizar datos antes de enviarlos al
  modelo, advertir al usuario del destino, evitar logs verbosos de contenido
  sensible, redactar secretos y crear almacenamiento aislado con permisos
  restrictivos y política de retención. Evaluar las garantías contractuales y
  de configuración del proveedor antes de enviar información sensible.
- **Comprobación de la corrección:** usar un marcador ficticio de secreto en
  un backlog y salida simulados; comprobar que no aparece en logs, prompt
  enviado ni artefactos no autorizados, que otro usuario local no puede leer
  el checkpoint y que la retención elimina los archivos según la política.

## 4. Verificaciones realmente ejecutadas

Todas las pruebas siguientes fueron locales, sin credenciales, llamadas al
modelo, servidor MCP ni acceso a datos de terceros.

| Comando o caso | Resultado real |
|---|---|
| `python tools\verify.py` | **Falló** al importar `main`: `ModuleNotFoundError: No module named 'crewai'`. No se ejecutó el test del flujo. |
| `python -`, cargando mediante AST las funciones originales de aprobación y preview, con `input` simulado y sin importar dependencias | EOF devolvió `("s", "")`; la entrada ficticia `datos` también; el marcador en la línea 46 no apareció en el preview. |
| `python -`, cargando mediante AST `main` original con MCP, checkpoint y escritura simulados | El proyecto ficticio B reutilizó y entregó a extracción la salida aprobada del proyecto ficticio A con el mismo título. |
| `python -`, evaluando mediante AST `_headers` con clave ficticia e inspeccionando `.env.example` y Compose | Se confirmó el envío de la clave ficticia como Bearer, la URL HTTP local de ejemplo, ambas publicaciones sin IP de host y `MCP_TOOL_GROUPS: all`. No se probó la red ni la autenticación del servidor. |
| `python -`, búsqueda en archivos versionados de patrones GitHub token, clave AWS `AKIA` y encabezados de clave privada | 32 archivos comprobados; cero archivos coincidieron. Es una búsqueda limitada, no una certificación de ausencia de secretos. No se muestran valores. |
| `git ls-files -- .env .env.example output` | Solo aparece `.env.example`; no se comprobó el historial Git ni archivos ignorados. |
| Comprobación adicional del criterio del checkpoint mediante `python -c` | **Falló** por un error de comillas (`SyntaxError`); no aporta evidencia. La prueba aislada y la lectura del código sustentan S4. |

Las pruebas con AST ejecutaron las funciones existentes aisladas con sustitutos;
no equivalen a una ejecución integrada con CrewAI. No se instalaron
dependencias ni se inició infraestructura.

## 5. Riesgos residuales y elementos no verificados

- La autenticación, autorización por recurso, protección frente a IDOR y
  disponibilidad de herramientas del servidor MCP real no se han probado.
- No se ha evaluado la seguridad de código Java, Angular o SQL generado: no
  forma parte del código inspeccionado y depende de la respuesta del modelo.
  No se detectó una inyección SQL o de comandos demostrable en las rutas
  Python examinadas; esto no certifica que no existan otras.
- No se han comprobado permisos efectivos de archivos, interceptación de red,
  comportamiento real de redirecciones, configuración del proveedor Copilot,
  historial Git, secretos ignorados ni vulnerabilidades de dependencias.
- Las comprobaciones de corrección de la sección 3 son **propuestas**. Los
  riesgos siguen abiertos; no hay correcciones implementadas ni validadas.

## 6. Hallazgos fuera de alcance

No se registraron hallazgos adicionales fuera del alcance declarado.

## 7. Actualizacion: instrucciones del agente de seguridad

**Alcance de esta actualizacion:** `agents/security.py` y el contrato de la
tarea que construye. Las secciones anteriores conservan los resultados de la
revision anterior; sus hallazgos no se han vuelto a validar en esta
actualizacion.

Antes del cambio, `INSTRUCTIONS` solo indicaba «Realiza la tarea de tu rol»
y la salida esperada era «Un informe de seguridad». Esto no exigia revisar
autenticacion, autorizacion, recursos ajenos, inyeccion o secretos, ni separar
la evidencia de las pruebas propuestas. Es una limitacion de las
instrucciones del agente, no una prueba de vulnerabilidad explotable en la
aplicacion.

Se actualizaron las instrucciones para solicitar esas revisiones, evidencia,
impacto, correcciones y comprobaciones reproducibles, sin inventar resultados
ni revelar valores reales de secretos. Se mantuvieron el nombre del archivo
de salida, la interfaz de `build_task` y la configuracion de delegacion.
Esta actualizacion no corrige ni valida los hallazgos S1-S6.

La revision de seguridad solicitada para esta actualizacion no notifico
vulnerabilidades en los cambios revisados, pero no proporciono ubicaciones,
evidencia ni detalle de las comprobaciones realizadas. Por ello no se puede
acreditar una revision completa del archivo ni concluir que sea seguro.

### Comprobaciones realmente ejecutadas en esta actualizacion

| Comprobacion | Resultado |
|---|---|
| `python -m unittest discover -s tests -p test_security_agent.py -v` | Correcto: una prueba aislada comprueba instrucciones, datos de la feature y contrato mediante objetos simulados. No invoca CrewAI ni un modelo. |
| Pylance: comprobacion de sintaxis de `agents/security.py` | Sin errores de sintaxis. |
| `python tools\verify.py` | Fallo al importar el flujo integrado: falta el modulo `crewai`. La prueba aislada del agente si paso. No se ejecuto el flujo integrado. |

### Comprobaciones propuestas, no ejecutadas

- Con las dependencias instaladas, ejecutar `python tools\verify.py` y
  comprobar que el flujo conserva las seis etapas y guarda el informe.
- Con un entorno controlado y codigo de prueba que incluya acceso no
  autorizado y una entrada de inyeccion, ejecutar el agente y revisar que
  informe archivo, ubicacion, evidencia, impacto, correccion y prueba
  reproducible; verificar que no afirme haber ejecutado pruebas que no ejecuto
  ni muestre valores de un secreto ficticio.
- Probar contenido de feature que intente anular las instrucciones. El texto
  de la instruccion por si solo no garantiza resistencia a inyeccion de
  prompts ni sustituye controles deterministas o revision humana.
