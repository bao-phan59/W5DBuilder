"""Unit tests for the autonomous stack detection tool."""
import json
import tempfile
import unittest
from pathlib import Path

from stack_detect import detect_stack


class StackDetectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_node_typescript_react_detection(self):
        pkg_json = self.root / "package.json"
        pkg_json.write_text(json.dumps({
            "name": "my-web-app",
            "dependencies": {"react": "^18.2.0"},
            "devDependencies": {"typescript": "^5.0.0", "vitest": "^1.0.0"},
            "scripts": {"test": "vitest run", "lint": "eslint ."}
        }), encoding="utf-8")
        (self.root / "pnpm-lock.yaml").write_text("", encoding="utf-8")
        (self.root / "tsconfig.json").write_text("{}", encoding="utf-8")
        (self.root / "docs").mkdir()

        res = detect_stack(self.root)
        self.assertIn("javascript", res["languages"])
        self.assertIn("typescript", res["languages"])
        self.assertIn("react", res["frameworks"])
        self.assertIn("pnpm", res["package_managers"])
        self.assertEqual(res["root_commands"]["test"], "pnpm run test")
        self.assertEqual(res["root_commands"]["lint"], "pnpm lint")
        self.assertEqual(res["root_commands"]["typecheck"], "npx tsc --noEmit")
        self.assertIn("docs", res["doc_roots"])

    def test_python_fastapi_detection(self):
        pyproject = self.root / "pyproject.toml"
        pyproject.write_text("""
[tool.poetry]
name = "api-service"
[tool.poetry.dependencies]
fastapi = "^0.110.0"
pydantic = "^2.0.0"
""", encoding="utf-8")
        (self.root / "poetry.lock").write_text("", encoding="utf-8")
        (self.root / "README.md").write_text("# API Service", encoding="utf-8")

        res = detect_stack(self.root)
        self.assertIn("python", res["languages"])
        self.assertIn("fastapi", res["frameworks"])
        self.assertIn("pydantic", res["frameworks"])
        self.assertIn("poetry", res["package_managers"])
        self.assertEqual(res["root_commands"]["test"], "poetry run pytest")
        self.assertIn("README.md", res["doc_roots"])

    def test_monorepo_backend_frontend_detection(self):
        backend = self.root / "backend"
        backend.mkdir()
        (backend / "requirements.txt").write_text("fastapi==0.110.0\npytest==8.0.0\n", encoding="utf-8")

        frontend = self.root / "frontend"
        frontend.mkdir()
        (frontend / "package.json").write_text(json.dumps({
            "name": "client",
            "dependencies": {"vue": "^3.4.0"},
            "scripts": {"test": "vitest"}
        }), encoding="utf-8")

        res = detect_stack(self.root)
        self.assertTrue(res["is_monorepo"])
        self.assertIn("python", res["languages"])
        self.assertIn("javascript", res["languages"])
        self.assertIn("fastapi", res["frameworks"])
        self.assertIn("vue", res["frameworks"])
        self.assertEqual(len(res["submodules"]), 2)

    def test_rust_detection(self):
        cargo = self.root / "Cargo.toml"
        cargo.write_text("""
[package]
name = "my-cli"
version = "0.1.0"
""", encoding="utf-8")

        res = detect_stack(self.root)
        self.assertIn("rust", res["languages"])
        self.assertIn("cargo", res["package_managers"])
        self.assertEqual(res["root_commands"]["test"], "cargo test")
        self.assertEqual(res["root_commands"]["build"], "cargo build")


if __name__ == "__main__":
    unittest.main()
