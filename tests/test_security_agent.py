"""Verify the security agent's task contract without external services."""

import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


class SecurityAgentTests(unittest.TestCase):
    def test_security_task_preserves_feature_and_review_requirements(self):
        class FakeAgent:
            def __init__(self, **kwargs):
                self.options = kwargs

        class FakeTask:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)

        crewai = types.ModuleType("crewai")
        crewai.Agent = FakeAgent
        crewai.Task = FakeTask
        llm_config = types.ModuleType("crew.llm_config")
        llm_config.llm = object()
        path = Path(__file__).resolve().parents[1] / "agents" / "security.py"
        spec = importlib.util.spec_from_file_location("security_agent_test", path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"crewai": crewai, "crew.llm_config": llm_config}):
            spec.loader.exec_module(module)

        task = module.build_task({
            "title": "Transferencia",
            "description": "Revisar el acceso a cuentas",
            "acceptance_criteria": ["Rechazar cuentas ajenas"],
        })

        for text in (
            "Transferencia", "Revisar el acceso a cuentas", "Rechazar cuentas ajenas",
            "autenticacion", "autorizacion", "inyeccion", "secretos",
            "evidencia concreta", "correccion propuesta", "comprobacion reproducible",
            "verificaciones realmente ejecutadas", "no ejecutadas",
        ):
            with self.subTest(text=text):
                self.assertIn(text, task.description)
        self.assertEqual(module.SPEC_FILE, "security_report.md")
        self.assertFalse(module.EXTRACT_CODE)
        self.assertIs(task.agent, module.agent)
        self.assertIn(module.SPEC_FILE, task.expected_output)
        self.assertFalse(module.agent.options["allow_delegation"])


if __name__ == "__main__":
    unittest.main()
