"""Autonomous project stack, test runner, and toolchain detector for Universal Code Runner.
Supports single projects, monorepos, and multi-service repositories (backend/frontend).
No external dependencies; runs on pure standard library Python.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path


def _detect_single_dir(target_dir):
    root = Path(target_dir).resolve()
    info = {
        "path": str(root),
        "name": root.name,
        "languages": [],
        "frameworks": [],
        "package_manager": None,
        "manifests": [],
        "suggested_commands": {
            "test": None,
            "lint": None,
            "typecheck": None,
            "build": None,
        },
        "details": {}
    }

    # 1. Node.js / TypeScript / JavaScript
    pkg_json = root / "package.json"
    if pkg_json.is_file():
        info["languages"].append("javascript")
        info["manifests"].append("package.json")
        try:
            with open(pkg_json, "r", encoding="utf-8") as f:
                pkg_data = json.load(f)
        except Exception:
            pkg_data = {}

        deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}
        scripts = pkg_data.get("scripts", {})

        if (root / "tsconfig.json").is_file() or (root / "tsconfig.app.json").is_file() or "typescript" in deps:
            info["languages"].append("typescript")

        if (root / "pnpm-lock.yaml").is_file():
            info["package_manager"] = "pnpm"
        elif (root / "yarn.lock").is_file():
            info["package_manager"] = "yarn"
        elif (root / "bun.lockb").is_file() or (root / "bun.lock").is_file():
            info["package_manager"] = "bun"
        elif (root / "package-lock.json").is_file():
            info["package_manager"] = "npm"
        elif "packageManager" in pkg_data:
            info["package_manager"] = pkg_data["packageManager"].split("@")[0]
        else:
            info["package_manager"] = "npm"

        pm = info["package_manager"]
        run_prefix = f"{pm} run" if pm in ("npm", "yarn") else pm

        for fw, dep_key in [
            ("react", "react"), ("nextjs", "next"), ("vue", "vue"),
            ("nuxt", "nuxt"), ("svelte", "svelte"), ("express", "express"),
            ("nestjs", "@nestjs/core"), ("fastify", "fastify"), ("astro", "astro"),
            ("tailwindcss", "tailwindcss"), ("vite", "vite"), ("remotion", "remotion")
        ]:
            if dep_key in deps:
                info["frameworks"].append(fw)

        if "test" in scripts:
            info["suggested_commands"]["test"] = f"{pm} test" if pm == "npm" else f"{pm} run test"
        elif "vitest" in deps:
            info["suggested_commands"]["test"] = "npx vitest run"
        elif "jest" in deps:
            info["suggested_commands"]["test"] = "npx jest"

        if "lint" in scripts:
            info["suggested_commands"]["lint"] = f"{run_prefix} lint"
        elif "eslint" in deps:
            info["suggested_commands"]["lint"] = "npx eslint ."
        elif (root / ".oxlintrc.json").is_file() or "oxlint" in deps:
            info["suggested_commands"]["lint"] = "npx oxlint"
        elif "biome" in deps:
            info["suggested_commands"]["lint"] = "npx @biomejs/biome check ."

        if "typecheck" in scripts:
            info["suggested_commands"]["typecheck"] = f"{run_prefix} typecheck"
        elif (root / "tsconfig.json").is_file() or (root / "tsconfig.app.json").is_file():
            info["suggested_commands"]["typecheck"] = "npx tsc --noEmit"

        if "build" in scripts:
            info["suggested_commands"]["build"] = f"{run_prefix} build"

        info["details"]["npm_scripts"] = list(scripts.keys())

    # 2. Python
    pyproject = root / "pyproject.toml"
    req_txt = root / "requirements.txt"
    setup_py = root / "setup.py"
    pipfile = root / "Pipfile"
    py_files = list(root.glob("*.py"))

    if pyproject.is_file() or req_txt.is_file() or setup_py.is_file() or pipfile.is_file() or py_files:
        if "python" not in info["languages"]:
            info["languages"].append("python")

        if pyproject.is_file():
            info["manifests"].append("pyproject.toml")
        if req_txt.is_file():
            info["manifests"].append("requirements.txt")
        if setup_py.is_file():
            info["manifests"].append("setup.py")
        if pipfile.is_file():
            info["manifests"].append("Pipfile")

        py_pm = "pip"
        if (root / "poetry.lock").is_file():
            py_pm = "poetry"
        elif (root / "uv.lock").is_file():
            py_pm = "uv"
        elif (root / "Pipfile.lock").is_file():
            py_pm = "pipenv"
        elif (root / "environment.yml").is_file():
            py_pm = "conda"

        if not info["package_manager"]:
            info["package_manager"] = py_pm

        py_content = ""
        for p in [pyproject, req_txt, setup_py]:
            if p.is_file():
                try:
                    py_content += " " + p.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    pass

        content_lower = py_content.lower()
        for fw, pattern in [
            ("fastapi", r"\bfastapi\b"),
            ("django", r"\bdjango\b"),
            ("flask", r"\bflask\b"),
            ("sqlalchemy", r"\bsqlalchemy\b"),
            ("celery", r"\bcelery\b"),
            ("pydantic", r"\bpydantic\b"),
            ("pytorch", r"\btorch\b"),
        ]:
            if re.search(pattern, content_lower):
                info["frameworks"].append(fw)

        if not info["suggested_commands"]["test"]:
            if py_pm == "poetry":
                info["suggested_commands"]["test"] = "poetry run pytest"
            elif py_pm == "uv":
                info["suggested_commands"]["test"] = "uv run pytest"
            else:
                info["suggested_commands"]["test"] = "pytest"

        if not info["suggested_commands"]["lint"]:
            if re.search(r"\bruff\b", content_lower):
                info["suggested_commands"]["lint"] = "ruff check ."
            elif re.search(r"\bflake8\b", content_lower):
                info["suggested_commands"]["lint"] = "flake8 ."

        if not info["suggested_commands"]["typecheck"]:
            if re.search(r"\bmypy\b", content_lower):
                info["suggested_commands"]["typecheck"] = "mypy ."

    # 3. Rust
    cargo_toml = root / "Cargo.toml"
    if cargo_toml.is_file():
        info["languages"].append("rust")
        info["manifests"].append("Cargo.toml")
        if not info["package_manager"]:
            info["package_manager"] = "cargo"
        if not info["suggested_commands"]["test"]:
            info["suggested_commands"]["test"] = "cargo test"
        if not info["suggested_commands"]["lint"]:
            info["suggested_commands"]["lint"] = "cargo clippy"
        if not info["suggested_commands"]["build"]:
            info["suggested_commands"]["build"] = "cargo build"

    # 4. Go
    go_mod = root / "go.mod"
    if go_mod.is_file():
        info["languages"].append("go")
        info["manifests"].append("go.mod")
        if not info["package_manager"]:
            info["package_manager"] = "go"
        if not info["suggested_commands"]["test"]:
            info["suggested_commands"]["test"] = "go test ./..."
        if not info["suggested_commands"]["lint"]:
            info["suggested_commands"]["lint"] = "golangci-lint run"
        if not info["suggested_commands"]["build"]:
            info["suggested_commands"]["build"] = "go build ./..."

    # 5. Java / Kotlin
    pom_xml = root / "pom.xml"
    build_gradle = root / "build.gradle"
    build_gradle_kts = root / "build.gradle.kts"
    if pom_xml.is_file():
        info["languages"].append("java")
        info["manifests"].append("pom.xml")
        info["package_manager"] = "maven"
        if not info["suggested_commands"]["test"]:
            info["suggested_commands"]["test"] = "mvn test"
        if not info["suggested_commands"]["build"]:
            info["suggested_commands"]["build"] = "mvn package"
    elif build_gradle.is_file() or build_gradle_kts.is_file():
        info["languages"].append("kotlin" if build_gradle_kts.is_file() else "java")
        info["manifests"].append(build_gradle_kts.name if build_gradle_kts.is_file() else "build.gradle")
        info["package_manager"] = "gradle"
        cmd_prefix = "./gradlew" if (root / "gradlew").is_file() or (root / "gradlew.bat").is_file() else "gradle"
        if not info["suggested_commands"]["test"]:
            info["suggested_commands"]["test"] = f"{cmd_prefix} test"
        if not info["suggested_commands"]["build"]:
            info["suggested_commands"]["build"] = f"{cmd_prefix} build"

    # 6. C# / .NET
    sln_files = list(root.glob("*.sln"))
    csproj_files = list(root.glob("*.csproj"))
    if sln_files or csproj_files:
        info["languages"].append("csharp")
        info["package_manager"] = "dotnet"
        info["manifests"].extend([f.name for f in sln_files] + [f.name for f in csproj_files[:2]])
        if not info["suggested_commands"]["test"]:
            info["suggested_commands"]["test"] = "dotnet test"
        if not info["suggested_commands"]["build"]:
            info["suggested_commands"]["build"] = "dotnet build"

    info["languages"] = sorted(list(set(info["languages"])))
    info["frameworks"] = sorted(list(set(info["frameworks"])))
    return info


def detect_stack(root_dir):
    root = Path(root_dir).resolve()
    if not root.is_dir():
        raise ValueError(f"Path does not exist or is not a directory: {root}")

    # Inspect root directory first
    root_info = _detect_single_dir(root)

    submodules = []
    # Search common subdirectories for multi-project / monorepo setups
    common_subdirs = ["backend", "frontend", "server", "client", "api", "web", "ui", "services", "app", "src"]
    for sub in common_subdirs:
        sub_path = root / sub
        if sub_path.is_dir() and not sub_path.name.startswith("."):
            sub_res = _detect_single_dir(sub_path)
            if sub_res["languages"] or sub_res["manifests"]:
                submodules.append(sub_res)

    # Search packages/ and apps/ glob
    for monorepo_folder in ["packages", "apps"]:
        mono_path = root / monorepo_folder
        if mono_path.is_dir():
            for child in mono_path.iterdir():
                if child.is_dir() and not child.name.startswith("."):
                    sub_res = _detect_single_dir(child)
                    if sub_res["languages"] or sub_res["manifests"]:
                        submodules.append(sub_res)

    # Consolidate top-level summary
    all_languages = set(root_info["languages"])
    all_frameworks = set(root_info["frameworks"])
    all_manifests = list(root_info["manifests"])
    all_package_managers = set([root_info["package_manager"]] if root_info["package_manager"] else [])

    for sub in submodules:
        all_languages.update(sub["languages"])
        all_frameworks.update(sub["frameworks"])
        for m in sub["manifests"]:
            all_manifests.append(f"{sub['name']}/{m}")
        if sub["package_manager"]:
            all_package_managers.add(sub["package_manager"])

    doc_candidates = [
        "docs", "doc", "spec", "specs", "specification", "architecture",
        "design", "documentation", "README.md", "README.markdown", "PRD.md"
    ]
    doc_roots = []
    for cand in doc_candidates:
        cand_path = root / cand
        if cand_path.exists():
            doc_roots.append(cand)

    report = {
        "project_root": str(root),
        "is_monorepo": len(submodules) > 0,
        "languages": sorted(list(all_languages)),
        "frameworks": sorted(list(all_frameworks)),
        "package_managers": sorted(list(all_package_managers)),
        "manifests": all_manifests,
        "doc_roots": doc_roots,
        "root_commands": root_info["suggested_commands"],
        "submodules": [
            {
                "name": s["name"],
                "path": str(Path(s["path"]).relative_to(root).as_posix()),
                "languages": s["languages"],
                "frameworks": s["frameworks"],
                "package_manager": s["package_manager"],
                "manifests": s["manifests"],
                "suggested_commands": s["suggested_commands"]
            }
            for s in submodules
        ]
    }
    return report


def format_summary(info):
    lines = [
        "=== Universal Stack Detector Report ===",
        f"Project Root     : {info['project_root']}",
        f"Architecture     : {'Monorepo / Multi-service' if info['is_monorepo'] else 'Standard / Single project'}",
        f"Languages        : {', '.join(info['languages']) or 'Not detected / Polyglot'}",
        f"Frameworks       : {', '.join(info['frameworks']) or 'None detected'}",
        f"Package Managers : {', '.join(info['package_managers']) or 'None detected'}",
        f"Manifests Found  : {', '.join(info['manifests']) or 'None'}",
        f"Doc Roots        : {', '.join(info['doc_roots']) or 'None'}",
    ]
    if info["submodules"]:
        lines.append("\nSub-projects & Services:")
        for s in info["submodules"]:
            lines.append(f"  • {s['name']} ({s['path']}):")
            lines.append(f"      Stack   : {', '.join(s['languages'])} [{', '.join(s['frameworks'])}]")
            lines.append(f"      Commands: Test: {s['suggested_commands']['test']} | Lint: {s['suggested_commands']['lint']} | Typecheck: {s['suggested_commands']['typecheck']}")
    else:
        lines.append("Suggested Commands:")
        lines.append(f"  Test          : {info['root_commands']['test'] or 'None (Manual specification needed)'}")
        lines.append(f"  Lint          : {info['root_commands']['lint'] or 'None'}")
        lines.append(f"  Typecheck     : {info['root_commands']['typecheck'] or 'None'}")
        lines.append(f"  Build         : {info['root_commands']['build'] or 'None'}")
    lines.append("========================================")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Root directory of the project to inspect")
    parser.add_argument("--json", action="store_true", help="Output full JSON report")
    args = parser.parse_args()

    try:
        report = detect_stack(args.root)
    except Exception as exc:
        parser.exit(2, f"stack_detect error: {exc}\n")

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if args.json:
        sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(format_summary(report) + "\n")


if __name__ == "__main__":
    main()
