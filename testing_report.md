# Informe de pruebas: agente de pruebas (`agents/testing.py`)

Estado general: NO EJECUTADO. Las pruebas están escritas, pero no hay salida real de ejecución en este informe.

## 1. Alcance

- Issue: NO DISPONIBLE en el repositorio. El Issue real llega por MCP en tiempo de ejecución. Los criterios de la matriz son SUPUESTO y provienen del fixture de `tests/test_workflow.py` (`Transfer funds`).
- Contratos que se prueban:
  - Constantes `KEY`, `LABEL`, `SPEC_FILE`, `EXTRACT_CODE` y firma `build_task(feature)`.
  - Contenido de la tarea (feature y criterios de aceptación).
  - Extracción de artefactos de `main.extract_and_save_code` para bloques Java de prueba.
- Fuera de alcance de este informe: la API Quarkus y la persistencia de la solución generada. Dependen del Issue y del código de backend, aún no entregado.
- Preguntas abiertas para el product owner:
  - ¿Qué código HTTP devuelve la transferencia con fondos insuficientes (422 o 409)?
  - ¿Los datos deben sobrevivir a un reinicio?
  - ¿Qué saldo inicial tiene cada cuenta de prueba?

## 2. Matriz de trazabilidad

| Criterio | Pruebas asociadas | Tipo | Resultado esperado | Estado |
|---|---|---|---|---|
| CA-1 (SUPUESTO): Reject a transfer with insufficient funds | Pendiente: pruebas de backend del Issue real (ver sección 5) | Negativo | HTTP 4xx con mensaje de fondos insuficientes y saldo sin cambios | NO EJECUTADO |
| Contrato del agente (CT-01 a CT-07) | `tests/test_testing_agent.py::TestingContractTests` | Positivo, negativo, borde | Constantes, firma y tarea conservadas; instrucciones con reglas de honestidad | NO EJECUTADO |
| Extracción de artefactos (EX-01 a EX-03) | `tests/test_testing_agent.py::TestingExtractionTests` | Positivo, negativo, borde, integración | El test Java se guarda en `src/test/java/pe/bcp/login/`; sin bloques no se guarda nada | NO EJECUTADO |
| Persistencia del checkpoint y reanudación | `tests/test_workflow.py::WorkflowTests::test_pipeline_saves_all_roles_and_resumes` | Integración | Los seis pasos aprobados se guardan y no se vuelven a llamar al modelo | NO EJECUTADO |

## 3. Preparación

1. Python 3.11 a 3.13. En Windows, el Python del sistema (3.13) no tiene `crewai`; usar el entorno virtual del proyecto.
2. Crear y activar el entorno (PowerShell o Git Bash):
   - `python -m venv .venv`
   - `.venv\Scripts\python.exe -m pip install -r requirements.txt`
3. Comprobación de importación realizada en este workspace: `.venv\Scripts\python.exe -c "import crewai; print(crewai.__version__)"` devolvió `1.15.33` (salida real, código 0). La salida de pip no se capturó, así que la instalación completa no está verificada.
4. No se requiere `.env` ni credenciales para estas pruebas: no llaman al modelo ni a MCP.
5. Perfil de Quarkus: H2 en memoria con `quarkus.hibernate-orm.database.generation=drop-and-create`. Los datos no sobreviven a un reinicio salvo que el Issue indique otra cosa.

## 4. Datos de prueba

| Dato | Valor |
|---|---|
| Feature | `{"title": "Transfer funds", "description": "Transfer funds between accounts", "acceptance_criteria": ["Reject a transfer with insufficient funds"]}` |
| Feature vacío | `{}` |
| Bloque Java de prueba | Primera línea `// TransferServiceTest.java`, clase `TransferServiceTest` |
| Respuesta sin bloques | Texto plano con `NO EJECUTADO` |
| Bloque bash sin nombre | `mvn test` dentro de un bloque `bash` |

## 5. Casos de prueba

Cada caso incluye: ID, criterio (CA-n), tipo, precondición, cuerpo JSON exacto de entrada, comando, código HTTP y cuerpo esperados, y criterio de paso o fallo.

Pruebas de contrato del agente (`tests/test_testing_agent.py`):

- CT-01 (positivo): `KEY == "testing"`, `LABEL == "Ingeniero de pruebas"`, `SPEC_FILE == "testing_report.md"`, `EXTRACT_CODE` verdadero.
- CT-02 (contrato): `build_task` acepta un único parámetro `feature`.
- CT-03 (positivo): la tarea incluye el título, la descripción y cada criterio.
- CT-04 (borde): `build_task({})` no falla y conserva las instrucciones.
- CT-05 (negativo): las instrucciones contienen `NO EJECUTADO` y `No inventes resultados`.
- CT-06 (positivo): las instrucciones exigen trazabilidad `CA-1` y los tipos positivo, negativo, de borde, integración y limpieza.
- CT-07 (contrato): `expected_output` menciona `testing_report.md` y `// NombreTest.java`.

Pruebas de extracción (integración con `main.extract_and_save_code`, con `OUTPUT_DIR` temporal):

- EX-01 (positivo): un bloque `TransferServiceTest.java` se guarda en `backend-quarkus/src/test/java/pe/bcp/login/` y empieza con `package pe.bcp.login;`.
- EX-02 (negativo): un informe sin bloques de código no guarda ningún archivo.
- EX-03 (borde): un bloque `bash` sin nombre de archivo no se guarda como fuente.

Pruebas pendientes del Issue real (CA-1, a completar por el equipo):

- Positivo: transferencia con saldo suficiente devuelve HTTP 200 y actualiza ambos saldos.
- Negativo: transferencia con saldo insuficiente devuelve HTTP 4xx y no cambia saldos.
- Borde: transferencia por el importe exacto del saldo.
- Integración: con drop-and-create, tras reiniciar la aplicación los saldos vuelven al estado inicial de la carga de datos (SUPUESTO hasta confirmar con el Issue).
- Contrato roto (CR-01, SUPUESTO): si la API responde 200 en lugar de 422 ante fondos insuficientes, la prueba negativa debe fallar y registrarse como defecto.

## 6. Comandos reproducibles

El agente de pruebas ejecuta solo `mvn test` y `mvn test -Dtest=NombreTest[#metodo]` mediante la herramienta `run_tests`, dentro de `output/backend-quarkus`. Cualquier otro comando se rechaza. Los comandos de Python se ejecutan manualmente desde la raíz del repositorio con el entorno virtual:

```
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m unittest tests.test_testing_agent -v
.venv\Scripts\python.exe -m unittest tests.test_workflow -v
.venv\Scripts\python.exe tools\verify.py
```

Backend generado (cuando exista el código del Issue):

```
cd output/backend-quarkus
mvn test
mvn test -Dtest=TransferServiceTest
```

## 7. Limpieza

- Las pruebas usan directorios temporales (`tempfile.TemporaryDirectory`) y se borran al terminar.
- Al importar `main`, se crea `output/`. Si no existía antes, eliminarla tras la ejecución: `Remove-Item -Recurse -Force output`.
- Los checkpoints de ejecuciones reales (`output/.checkpoint.json`) no se comparten entre equipos.
- Con drop-and-create, la base H2 en memoria se recrea en cada arranque; no hay datos de prueba persistentes que borrar.

## 8. Correcciones propuestas

Sin fallos observados, porque no hay ejecución real. Propuestas a validar tras ejecutar:

- Si una prueba Java sin `Test` en el nombre contiene `@Test`, se guarda en la carpeta de test. Propuesta: exigir que el nombre termine en `Test.java` en el prompt, y validarlo con EX-01. Responsable: ingeniero de pruebas.
- Si el backend cambia la ruta o el código HTTP de la transferencia, actualizar CA-1 y coordinar con el responsable de backend.
- Regla: si una prueba falla, no se modifica la prueba ni el criterio para que pase; se registra la salida real y se clasifica como defecto, supuesto o problema de entorno.

## 9. Evidencia y resultados

| Caso | Comando | Commit SHA | Java / Maven | Fecha | Resumen Tests run / Failures / Errors | Salida real | Estado |
|---|---|---|---|---|---|---|---|
| CT-01 a CT-07 | `.venv\Scripts\python.exe -m unittest tests.test_testing_agent -v` | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | NO EJECUTADO |
| EX-01 a EX-03 | `.venv\Scripts\python.exe -m unittest tests.test_testing_agent -v` | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | NO EJECUTADO |
| Persistencia y reanudación | `.venv\Scripts\python.exe -m unittest tests.test_workflow -v` | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | NO EJECUTADO |
| Pipeline completo | `.venv\Scripts\python.exe tools\verify.py` | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | NO EJECUTADO |
| CA-1 (backend) | `mvn test` en `output/backend-quarkus` | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | NO EJECUTADO |

Para registrar resultados, pegar aquí la salida real devuelta por `run_tests` (o por el comando manual) y cambiar el estado a PASA o FALLA. PASA exige código de salida 0 y salida pegada; sin ellos, el estado es NO EJECUTADO.
