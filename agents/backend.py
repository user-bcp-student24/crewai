"""Agente inicial del taller. Mejora sus instrucciones sin cambiar su contrato."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'backend'
LABEL = 'Desarrollador backend'
SPEC_FILE = 'backend_spec.md'
EXTRACT_CODE = True

INSTRUCTIONS = """Implementa la funcionalidad backend solicitada en la especificación.

Usa el título, la descripción y todos los criterios de aceptación como fuente de
requisitos. Revisa el contexto disponible para seguir las convenciones del
proyecto y entregar una implementación coherente con el servicio backend.
Limita el cambio al alcance solicitado: no inventes requisitos, contratos,
dependencias ni comportamiento. Si falta información que impide implementar un
criterio correctamente, indícalo en lugar de asumirlo.

Entrega el código Java completo en bloques Markdown, uno por archivo. En cada
bloque, la primera línea debe ser un comentario con el nombre del archivo
(por ejemplo, // Nombre.java) y la siguiente línea debe ser:
package pe.bcp.login.service;
No agregues texto antes de esas líneas dentro del bloque de código."""
agent = Agent(role='Desarrollador backend',
              goal="Implementar funcionalidades backend completas y alineadas con los criterios de aceptación.",
              backstory=("Eres un desarrollador backend responsable de traducir "
                         "especificaciones aprobadas en código Java claro, "
                         "coherente con el proyecto y limitado al alcance pedido."),
              llm=llm,
              verbose=True, allow_delegation=False)


def build_task(feature: dict) -> Task:
    return Task(description=INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                + "\n" + str(feature.get("description", ""))
                + "\n" + str(feature.get("acceptance_criteria", [])),
                expected_output=('Código Java completo en bloques Markdown; cada bloque inicia '
                                 'con // Nombre.java y luego package pe.bcp.login.service.'),
                agent=agent)
