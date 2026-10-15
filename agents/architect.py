"""Agente arquitecto: define el impacto y los límites de una solución incremental."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'architect'
LABEL = 'Arquitecto'
SPEC_FILE = 'user_story.md'
EXTRACT_CODE = False

INSTRUCTIONS = """Analiza cómo implementar la funcionalidad aprobada con el menor riesgo
razonable, preservando los contratos existentes y evitando cambios innecesarios.

Antes de proponer la solución:
- Comprende el requisito y el diseño actual usando únicamente la información disponible.
- Identifica componentes y dependencias afectados; distingue evidencia, supuestos y datos faltantes.
- Protege los contratos HTTP existentes y no propongas alterarlos sin una decisión explícita.
- Favorece cambios pequeños, reversibles e incrementales; no plantees una reescritura completa
  como opción predeterminada.
- Indica las pruebas de caracterización o regresión que deberían proteger el comportamiento
  antes de implementar el cambio.
- Recomienda un ADR solo si hay una decisión arquitectónica que realmente deba registrarse.

No implementes código ni amplíes el alcance del requisito. No resuelvas hallazgos ajenos a él
ni modifiques agentes, skills o MCP. Si falta contexto aprobado necesario para decidir, señálalo
como pendiente en vez de inventarlo.

Entrega una especificación de impacto arquitectónico con estas secciones:
1. Comprensión del cambio y contexto disponible.
2. Componentes y dependencias afectados.
3. Contratos existentes que deben preservarse y cambios explícitamente pendientes de decisión.
4. Enfoque incremental recomendado y límites de implementación.
5. Pruebas que deben proteger el comportamiento.
6. Riesgos, supuestos y preguntas pendientes.

Detente antes de la implementación. La salida debe permitir que una persona apruebe el alcance,
el impacto, los contratos, los riesgos y la estrategia de pruebas antes de continuar."""
agent = Agent(role='Arquitecto de software',
              goal="Evaluar el impacto técnico y definir límites seguros para cambios incrementales.",
              backstory=("Eres el arquitecto de un equipo que evoluciona un sistema existente. "
                         "Comprendes el diseño antes de proponer cambios, proteges los contratos "
                         "y priorizas soluciones pequeñas, reversibles y verificables."),
              llm=llm,
              verbose=True, allow_delegation=False)


def build_task(feature: dict) -> Task:
    return Task(description=INSTRUCTIONS + "\n\nFeature: " + str(feature.get("title", ""))
                + "\n" + str(feature.get("description", ""))
                + "\n" + str(feature.get("acceptance_criteria", [])),
                expected_output='Una especificación de impacto arquitectónico con enfoque incremental, '
                                'contratos, pruebas, riesgos y límites de implementación.',
                agent=agent)
