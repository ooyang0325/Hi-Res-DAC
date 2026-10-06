"""Run one job of .gitlab-ci.yml (default before_script + its script) with bash -e.

GitHub Actions reuses the GitLab job definitions through this script, so both CIs check the same
things from one file. `sudo ` is dropped because the GitHub job runs as root in the container."""
import os
import subprocess
import sys
from pathlib import Path

import yaml

job = sys.argv[1]
cfg = yaml.safe_load(Path(".gitlab-ci.yml").read_text())
if job not in cfg:
    raise SystemExit(f"unknown job {job!r}; jobs: {[k for k in cfg if isinstance(cfg[k], dict) and 'script' in cfg[k]]}")
lines = cfg["default"].get("before_script", []) + cfg[job]["script"]
script = "set -e\n" + "\n".join(
    f"echo {subprocess.list2cmdline(['$ ' + line])}\n{line.removeprefix('sudo ')}" for line in lines)
env = {**os.environ, "CI_PROJECT_DIR": os.getcwd(), "CI_COMMIT_SHORT_SHA": os.environ.get("GITHUB_SHA", "local")[:8]}
sys.exit(subprocess.run(["bash", "-c", script], env=env).returncode)
