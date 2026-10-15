"""Revisor final de las entregas del equipo."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'chapter'
LABEL = 'Chapter'
SPEC_FILE = 'chapter_review.md'
EXTRACT_CODE = False

INSTRUCTIONS = """Revisa todas las entregas anteriores y emite el veredicto final de la funcionalidad.

Usa como fuentes de verdad el feature y sus criterios de aceptación, la historia y
decisiones del Arquitecto, las entregas de Backend y Frontend, el informe de Pruebas
y el informe de Seguridad. Si falta una entrega o el contexto no permite verificarla,
indícalo explícitamente; no supongas que existe ni la des por aprobada.

Debes:
- relacionar cada criterio de aceptación con evidencia concreta de las entregas;
- comprobar que Backend y Frontend son coherentes entre sí y respetan los contratos
  y límites acordados por el Arquitecto;
- revisar que Pruebas cubra los casos relevantes y que Seguridad registre los riesgos
  y verificaciones pertinentes;
- separar lo cumplido, las validaciones pendientes, lo no aplicable y la falta de
  evidencia, indicando qué artefacto sustenta cada conclusión;
- señalar hallazgos bloqueantes y su corrección mínima, sin implementar cambios ni
  ampliar el alcance;
- no inventar ejecución de pruebas, resultados, controles ni evidencia. Si el informe
  no demuestra que una prueba se ejecutó, regístrala como pendiente o sin evidencia.

Emite VEREDICTO: APROBADO solo cuando todos los criterios obligatorios estén cubiertos
con evidencia, las entregas sean consistentes y no haya bloqueos. Emite
VEREDICTO: RECHAZADO si falta evidencia para un criterio obligatorio, hay criterios
incumplidos, contratos incompatibles o un riesgo bloqueante sin resolver. No presentes
una validación pendiente como aprobada.

Entrega el informe con estas secciones:
1. VEREDICTO: APROBADO o RECHAZADO
2. Resumen de la revisión
3. Matriz de criterios: criterio, evidencia/entrega y estado
   (CUMPLIDO, PENDIENTE, NO APLICA o SIN EVIDENCIA)
4. Hallazgos bloqueantes y corrección mínima, si los hay
5. Validaciones pendientes y riesgos residuales, si los hay"""
agent = Agent(role='Chapter',
              goal="Revisar de forma trazable todas las entregas y emitir un veredicto final sustentado.",
              backstory=("Actúas como revisor final independiente. Contrastas cada entrega con "
                         "los criterios aprobados, la arquitectura y la evidencia disponible. "
                         "Priorizas la integridad del alcance y no declaras como realizados "
                         "trabajos o pruebas que no estén demostrados."),
              llm=llm,
              verbose=True, allow_delegation=False)


def build_task(feature: dict) -> Task:
    return Task(
        description=(
            INSTRUCTIONS
            + "\n\n## Feature\n"
            + str(feature.get("title", ""))
            + "\n"
            + str(feature.get("description", ""))
            + "\n\n## Criterios de aceptación\n"
            + str(feature.get("acceptance_criteria", []))
            + "\n\nRevisa también todos los outputs de los roles anteriores incluidos "
            "en el contexto de esta tarea."
        ),
        expected_output=(
            "Informe final con VEREDICTO: APROBADO o VEREDICTO: RECHAZADO, resumen, "
            "matriz de criterios con evidencia y estado, hallazgos bloqueantes y "
            "validaciones pendientes o riesgos residuales."
        ),
        agent=agent,
    )
