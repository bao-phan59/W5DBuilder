import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("contract_cli", ROOT / "contracts/scripts/validate.py")
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


class ScriptDocumentTests(unittest.TestCase):
    def setUp(self):
        self.schema = json.loads(cli.SCHEMA.read_text(encoding="utf-8-sig"))
        self.document = json.loads((ROOT / "contracts/examples/script-document.elephants.json").read_text(encoding="utf-8-sig"))

    def codes(self, document):
        return {error["code"] for error in cli.validate_document(document, self.schema)["errors"]}

    def test_golden_valid_and_input_not_mutated(self):
        original = copy.deepcopy(self.document)
        self.assertEqual(cli.validate_document(self.document, self.schema), {"errors": [], "warnings": [], "infos": []})
        self.assertEqual(original, self.document)

    def test_portable_skill_mirrors_canonical_schema_and_fixture(self):
        self.assertEqual(cli.SCHEMA.read_bytes(), (ROOT / ".agents/skills/w5d-script/schemas/script.schema.json").read_bytes())
        self.assertEqual((ROOT / "contracts/examples/script-document.elephants.json").read_bytes(), (ROOT / ".agents/skills/w5d-script/examples/example_01_elephants.json").read_bytes())

    def test_structurally_invalid_documents_return_report_without_semantic_crash(self):
        malformed = [None, [], {}, {**self.document, "sentences": None},
                     {**self.document, "schemaVersion": "2.0"}, {**self.document, "unexpected": True},
                     {**self.document, "interSentencePauseMs": True}]
        for document in malformed:
            with self.subTest(document_type=type(document).__name__):
                self.assertTrue(self.codes(document))

    def test_duplicate_ids_for_all_collections(self):
        for collection in ("sentences", "entityDefinitions", "entityInstances"):
            with self.subTest(collection=collection):
                document = copy.deepcopy(self.document)
                document[collection][1]["id"] = document[collection][0]["id"]
                self.assertIn("script.duplicate_id", self.codes(document))

    def test_order_matches_array_and_has_no_gaps(self):
        self.document["sentences"][1]["order"] = 3
        self.assertIn("script.order", self.codes(self.document))

    def test_entity_and_instruction_and_target_references(self):
        variants = []
        document = copy.deepcopy(self.document)
        document["entityInstances"][0]["entityId"] = "ent_missing"
        variants.append((document, "script.unknown_entity"))
        document = copy.deepcopy(self.document)
        document["sentences"][0]["entityInstructions"][0]["instanceId"] = "ins_missing"
        variants.append((document, "script.unknown_instance"))
        document = copy.deepcopy(self.document)
        document["sentences"][0]["entityInstructions"][0]["targetInstanceId"] = "ins_missing"
        variants.append((document, "script.unknown_target"))
        for document, code in variants:
            with self.subTest(code=code):
                self.assertIn(code, self.codes(document))

    def test_actions_before_enter_are_invalid(self):
        for action in ("stay", "move", "emphasize", "exit"):
            with self.subTest(action=action):
                document = copy.deepcopy(self.document)
                document["sentences"][0]["entityInstructions"][0]["action"] = action
                self.assertIn("script.inactive_instance", self.codes(document))

    def test_duplicate_enter_while_active(self):
        self.document["sentences"][1]["entityInstructions"][0]["action"] = "enter"
        self.assertIn("script.duplicate_enter", self.codes(self.document))

    def test_action_after_exit_requires_reenter(self):
        self.document["sentences"][3]["entityInstructions"].append({"instanceId": "ins_elephant_1", "action": "move"})
        self.assertIn("script.inactive_instance", self.codes(self.document))
        self.document["sentences"][3]["entityInstructions"][-1]["action"] = "enter"
        self.assertEqual(self.codes(self.document), set())

    def test_ranges_reject_empty_out_of_bounds_wrong_text_and_overlap(self):
        cases = [({"startChar": 21, "endChar": 21, "text": "x"}, "script.range_bounds"),
                 ({"startChar": 0, "endChar": 999, "text": "x"}, "script.range_bounds"),
                 ({"startChar": 21, "endChar": 31, "text": "wrong"}, "script.range_text"),
                 ({"startChar": 21, "endChar": 31, "text": "ba chú voi"}, "script.range_overlap")]
        for emphasis, code in cases:
            with self.subTest(code=code):
                document = copy.deepcopy(self.document)
                document["sentences"][0]["emphasisRanges"].append(emphasis)
                self.assertIn(code, self.codes(document))

    def test_unicode_codepoints_half_open_adjacent_ranges_and_arbitrary_range_order(self):
        sentence = self.document["sentences"][0]
        sentence["narrationText"] = "🐘e\u0301 voi"
        sentence["emphasisRanges"] = [
            {"startChar": 1, "endChar": 3, "text": "e\u0301"},
            {"startChar": 0, "endChar": 1, "text": "🐘"}]
        self.assertEqual(self.codes(self.document), set())

    def test_duration_includes_only_between_sentence_pauses(self):
        self.document["estimatedTotalDurationMs"] += self.document["interSentencePauseMs"]
        self.assertIn("script.duration_total", self.codes(self.document))

    def test_target_tolerance_exact_boundary_and_beyond(self):
        self.document["targetDurationMs"] = 25000  # 30,000 is exactly +20%.
        self.assertEqual(self.codes(self.document), set())
        self.document["targetDurationMs"] = 24999
        self.assertIn("script.duration_target", self.codes(self.document))
        self.document["targetDurationMs"] = 37500  # Exactly -20%.
        self.assertEqual(self.codes(self.document), set())
        self.document["targetDurationMs"] = 37501
        self.assertIn("script.duration_target", self.codes(self.document))

    def test_single_sentence_has_no_trailing_pause(self):
        sentence = copy.deepcopy(self.document["sentences"][0])
        sentence["estimatedDurationMs"] = 8000
        self.document.update(sentences=[sentence], targetDurationMs=10000, estimatedTotalDurationMs=10000)
        # Formula is 8000, not 8300 or 10000; schema minimum doesn't remove the semantic check.
        self.assertIn("script.duration_total", self.codes(self.document))

    def test_cli_runs_from_other_cwd_and_fails_for_bad_json(self):
        with tempfile.TemporaryDirectory() as directory:
            command = [sys.executable, "-B", str(ROOT / "contracts/scripts/validate.py")]
            valid = subprocess.run(command, cwd=directory, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(valid.returncode, 0, valid.stderr)
            self.assertTrue(json.loads(valid.stdout))
            invalid = Path(directory) / "bad.json"
            invalid.write_text("{invalid", encoding="utf-8")
            result = subprocess.run(command + [str(invalid)], cwd=directory, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(json.loads(result.stdout)[str(invalid)]["errors"][0]["code"], "document.invalid_json")

    def test_cli_semantic_failure_has_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            self.document["estimatedTotalDurationMs"] += 1
            invalid = Path(directory) / "invalid.json"
            invalid.write_text(json.dumps(self.document), encoding="utf-8")
            result = subprocess.run([sys.executable, "-B", str(ROOT / "contracts/scripts/validate.py"), str(invalid)], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("script.duration_total", result.stdout)


if __name__ == "__main__":
    unittest.main()
