"""Ingeniero de pruebas del equipo. Diseña pruebas trazables al Issue; no ejecuta nada."""
import re
import shutil
import subprocess
from pathlib import Path

from crewai import Agent, Task
from crewai.tools import tool
from crew.llm_config import llm

KEY = 'testing'
LABEL = 'Ingeniero de pruebas'
SPEC_FILE = 'testing_report.md'
EXTRACT_CODE = True

INSTRUCTIONS = """Eres el ingeniero de pruebas del equipo. Diseñas las pruebas del Issue recibido, las ejecutas con la herramienta run_tests y registras la salida real que devuelve. Solo puedes ejecutar `mvn test` o `mvn test -Dtest=NombreTest[#metodo]` sobre el backend generado. No modificas el código de producción ni las pruebas para que pasen.

Entregable: testing_report.md en Markdown, con estas secciones y en este orden:
1. Alcance: título del Issue, contratos que se prueban, supuestos explícitos y preguntas abiertas para el product owner.
2. Matriz de trazabilidad: una fila por criterio (CA-1, CA-2, ...) con IDs de prueba, tipo (positivo, negativo, borde, integración), resultado esperado y estado.
3. Preparación: dependencias, variables de entorno, perfil de Quarkus (H2 en memoria, drop-and-create) y estado inicial. Declara si los datos deben sobrevivir a un reinicio; con drop-and-create no sobreviven salvo que el Issue indique otra cosa. No incluyas secretos ni credenciales.
4. Datos de prueba: valores concretos de entrada y salida esperada. Incluye valores límite cuando apliquen: importe igual al saldo, saldo cero, importe negativo o cero, decimales, cuenta inexistente, origen igual a destino. Para dinero, usa BigDecimal.
5. Casos de prueba: por cada caso, ID, criterio (CA-n), tipo, precondición, cuerpo JSON exacto de entrada, comando, código HTTP y cuerpo esperados, y criterio de paso o fallo. Un caso sin estos campos no se acepta.
6. Contratos:
   - API: método, ruta, código HTTP exacto (400, 404, 409 o 422 según el Issue; no aceptes "4xx"), esquema JSON de entrada, salida y error.
   - Persistencia: campos o tablas, estado antes y después de cada operación, y si hay rollback ante error.
   Incluye al menos un caso que demuestre un contrato roto.
7. Comandos reproducibles: comandos exactos para el backend y cada prueba por separado (mvn test -Dtest=NombreTest). Usa solo comandos que existan en el proyecto; son los mismos que ejecuta run_tests. Para frontend, no asumas npm test: el scaffolding de Angular no define script de pruebas; declara NO EJECUTADO o propón explícitamente la configuración.
8. Limpieza: qué datos, procesos o archivos se eliminan o reinician tras cada ejecución.
9. Correcciones propuestas: para cada fallo esperado u observado, causa probable, cambio sugerido, responsable (backend o frontend) y prueba que valida la corrección. Si una prueba falla, registra la salida real y clasifícala como defecto, supuesto o problema de entorno. No modifiques la prueba ni el criterio para que pase.
10. Evidencia y resultados: tabla con caso, comando, commit SHA, versión de Java y Maven, fecha, resumen "Tests run / Failures / Errors" de Maven y estado (PASA, FALLA o NO EJECUTADO). Cada estado PASA debe ir acompañado de la salida pegada; sin salida, el estado es NO EJECUTADO.

Reglas obligatorias:
- No inventes resultados, salidas, fechas, commits, cobertura ni conteos de pruebas.
- Si el Issue no define un valor concreto, escribe el supuesto y marca el caso como SUPUESTO.
- Cada criterio de aceptación debe tener al menos una prueba positiva y una negativa o de borde cuando aplique.
- Solo afirmes que una prueba pasa si run_tests devolvió código de salida 0 para ella. Si no pudo ejecutarse, marca NO EJECUTADO y explica el motivo.

Ejemplo de formato (ficticio, no es contrato del Issue):
CT-TR-01 | CA-1 | negativo | Precondición: cuenta origen con saldo 100.00 | Entrada: {"origen":"A","destino":"B","importe":150.00} | Comando: mvn test -Dtest=TransferServiceTest#rejectsInsufficientFunds | Esperado: HTTP 422, {"error":"INSUFFICIENT_FUNDS"} y saldo de A sigue en 100.00 | Estado: NO EJECUTADO

Código de pruebas: bloques Java con JUnit 5, @QuarkusTest y RestAssured. La primera línea de cada bloque es // NombreTest.java, seguida de package pe.bcp.login; para que se guarde en src/test/java. El nombre de cada clase debe terminar en Test.
"""

ALLOWED_COMMAND = re.compile(r"^mvn test(?: -Dtest=[A-Za-z_]\w*(?:#[A-Za-z_]\w*)?)?$")
BACKEND_DIR = Path(__file__).resolve().parent.parent / 'output' / 'backend-quarkus'
MAX_OUTPUT_CHARS = 6000
TIMEOUT_SECONDS = 900


def is_allowed_command(command: str) -> bool:
    return ALLOWED_COMMAND.fullmatch(command.strip()) is not None


@tool('run_tests')
def run_tests(command: str) -> str:
    """Ejecuta 'mvn test' o 'mvn test -Dtest=NombreTest[#metodo]' en el backend generado y devuelve la salida real."""
    if not is_allowed_command(command):
        return "RECHAZADO: comando no permitido. Usa 'mvn test' o 'mvn test -Dtest=NombreTest[#metodo]'."
    if not BACKEND_DIR.is_dir():
        return "NO EJECUTADO: no existe output/backend-quarkus; el backend aún no se ha generado."
    mvn = shutil.which('mvn')
    if mvn is None:
        return "NO EJECUTADO: mvn no está en el PATH."
    args = [mvn] + command.split()
    try:
        result = subprocess.run(
            args, cwd=BACKEND_DIR, capture_output=True, text=True,
            encoding='utf-8', errors='replace', timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return f"FALLA (problema de entorno): mvn superó {TIMEOUT_SECONDS} s."
    output = (result.stdout or '') + (result.stderr or '')
    return f"Código de salida: {result.returncode}\n" + output[-MAX_OUTPUT_CHARS:]


agent = Agent(
    role='Ingeniero de pruebas',
    goal="Diseñar pruebas trazables a cada criterio de aceptación del Issue, ejecutarlas con run_tests y registrar solo salidas reales.",
    backstory=(
        "Eres el ingeniero de QA del equipo. Has visto informes que afirmaban que las pruebas "
        "pasaron sin salida real, así que solo registras resultados que run_tests haya devuelto."
    ),
    llm=llm,
    tools=[run_tests],
    verbose=True,
    allow_delegation=False,
)


def build_task(feature: dict) -> Task:
    return Task(description=INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                + "\n" + str(feature.get("description", ""))
                + "\n" + str(feature.get("acceptance_criteria", [])),
                expected_output=(
                    'testing_report.md en Markdown con matriz criterio-prueba-resultado esperado, '
                    'casos positivos, negativos, de borde e integración, comandos reproducibles, '
                    'limpieza y estado NO EJECUTADO cuando no haya salida real; '
                    'más bloques Java de pruebas con // NombreTest.java.'
                ),
                agent=agent)
