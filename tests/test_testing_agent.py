"""Contract checks for agents/testing.py and its artifact extraction, without calling the model."""

import contextlib
import inspect
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import main as app
from agents import testing


FEATURE = {
    "title": "Transfer funds",
    "description": "Transfer funds between accounts",
    "acceptance_criteria": ["Reject a transfer with insufficient funds"],
}


class TestingContractTests(unittest.TestCase):
    def test_keys_and_artifact_are_preserved(self):
        self.assertEqual(testing.KEY, "testing")
        self.assertEqual(testing.LABEL, "Ingeniero de pruebas")
        self.assertEqual(testing.SPEC_FILE, "testing_report.md")
        self.assertTrue(testing.EXTRACT_CODE)

    def test_build_task_signature_is_preserved(self):
        self.assertEqual(list(inspect.signature(testing.build_task).parameters), ["feature"])

    def test_task_contains_feature_and_every_criterion(self):
        task = testing.build_task(FEATURE)
        self.assertIs(task.agent, testing.agent)
        self.assertIn("Transfer funds", task.description)
        self.assertIn(FEATURE["description"], task.description)
        for criterion in FEATURE["acceptance_criteria"]:
            self.assertIn(criterion, task.description)

    def test_task_tolerates_missing_fields(self):
        task = testing.build_task({})
        self.assertIn(testing.INSTRUCTIONS, task.description)

    def test_instructions_forbid_invented_results(self):
        self.assertIn("NO EJECUTADO", testing.INSTRUCTIONS)
        self.assertIn("No inventes resultados", testing.INSTRUCTIONS)

    def test_instructions_require_traceability_and_test_types(self):
        for phrase in ("CA-1", "positivo", "negativo", "de borde", "integración", "Limpieza"):
            self.assertIn(phrase, testing.INSTRUCTIONS)

    def test_expected_output_names_the_report_and_test_block_header(self):
        task = testing.build_task(FEATURE)
        self.assertIn("testing_report.md", task.expected_output)
        self.assertIn("// NombreTest.java", task.expected_output)


class TestingRunTestsTool(unittest.TestCase):
    def test_agent_has_run_tests_tool(self):
        names = [getattr(t, "name", None) for t in testing.agent.tools]
        self.assertIn("run_tests", names)

    def test_allows_only_maven_test_commands(self):
        self.assertTrue(testing.is_allowed_command("mvn test"))
        self.assertTrue(testing.is_allowed_command("mvn test -Dtest=TransferServiceTest"))
        self.assertTrue(testing.is_allowed_command("mvn test -Dtest=TransferServiceTest#rejectsInsufficientFunds"))

    def test_rejects_shell_injection_and_other_commands(self):
        for bad in ("mvn test && del x", "mvn clean install", "rm -rf output", "mvn test -Dtest=A;B", ""):
            self.assertFalse(testing.is_allowed_command(bad), bad)


class TestingExtractionTests(unittest.TestCase):
    def _extract(self, text):
        with tempfile.TemporaryDirectory() as tmp, contextlib.ExitStack() as stack:
            output = Path(tmp)
            stack.enter_context(patch.object(app, "OUTPUT_DIR", output))
            stack.enter_context(patch.object(app, "ensure_scaffolding"))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            saved = app.extract_and_save_code(text)
            contents = {
                rel: (output / rel).read_text(encoding="utf-8") for rel in saved
            }
        return saved, contents

    def test_test_class_is_saved_under_test_tree_with_package(self):
        sample = "```java\n// TransferServiceTest.java\npublic class TransferServiceTest {}\n```"
        saved, contents = self._extract(sample)
        self.assertEqual(
            saved, ["backend-quarkus/src/test/java/pe/bcp/login/TransferServiceTest.java"]
        )
        self.assertTrue(contents[saved[0]].startswith("package pe.bcp.login;"))

    def test_report_without_code_blocks_saves_nothing(self):
        saved, _ = self._extract("testing_report.md\nSolo texto. NO EJECUTADO.")
        self.assertEqual(saved, [])

    def test_unnamed_shell_block_is_not_saved_as_source(self):
        saved, _ = self._extract("```bash\nmvn test\n```")
        self.assertEqual(saved, [])


if __name__ == "__main__":
    unittest.main()
