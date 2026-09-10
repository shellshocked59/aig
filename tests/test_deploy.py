"""Exercise deployment failure boundaries with fake Git/Docker and real files."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


@unittest.skipUnless(os.name == "posix" and shutil.which("bash") and shutil.which("flock"),
                     "Deployment script tests require Linux bash and flock")
class DeploymentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repo = self.root / "server checkout"
        self.repo.mkdir()
        (self.repo / "dist").mkdir()
        (self.repo / "dist/index.html").write_text("old frontend")
        (self.repo / "scripts").mkdir()
        (self.repo / "scripts/production-smoke.py").write_text("print('smoke')")
        (self.repo / ".env.production").write_text("POSTGRES_PASSWORD=keep-existing-password\n")
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.log = self.root / "calls"
        self.revision = "a" * 40
        self.script = Path(__file__).resolve().parents[1] / "scripts/deploy-remote.sh"
        self.write_stub("git", '''#!/usr/bin/env bash
set -eu
printf 'git %s\\n' "$*" >> "$CALL_LOG"
case "$1" in
  rev-parse) pwd ;;
  remote) echo https://github.com/shellshocked59/aig.git ;;
  status) if [[ ${FAKE_DIRTY:-0} == 1 ]]; then echo ' M tracked.py'; fi ;;
  fetch|merge-base|checkout) : ;;
  *) exit 99 ;;
esac
''')
        self.write_stub("docker", '''#!/usr/bin/env bash
set -eu
printf 'docker %s\\n' "$*" >> "$CALL_LOG"
if [[ $1 == info && ${FAKE_NEEDS_SUDO:-0} == 1 && ${FAKE_SUDO:-0} != 1 ]]; then
  exit 1
elif [[ $1 == build ]]; then
  if [[ ${FAKE_BUILD_FAIL:-0} == 1 ]]; then exit 1; fi
  for arg in "$@"; do
    if [[ $arg == type=local,dest=* ]]; then
      printf 'new frontend' > "${arg#type=local,dest=}/index.html"
    fi
  done
elif [[ $1 == inspect ]]; then
  echo "$EXPECTED_REVISION"
elif [[ $1 == compose ]]; then
  if [[ $2 == --env-file ]]; then
    # Like Compose, consume explicit env files even if sudo removed shell env.
    shift
    while [[ $1 == --env-file ]]; do
      set -a
      source "$2"
      set +a
      shift 2
    done
    [[ ${AIG_RELEASE_SHA:-} == "$EXPECTED_REVISION" ]] || exit 98
  fi
  case "$*" in
    *' up -d '*) if [[ ${FAKE_HEALTH_FAIL:-0} == 1 ]]; then exit 1; fi ;;
    *' exec -T api python -') cat >/dev/null ;;
    *' ps -q api') echo test-container ;;
  esac
fi
''')
        self.write_stub("sudo", '''#!/usr/bin/env bash
set -eu
[[ $1 == -n ]]
shift
unset AIG_RELEASE_SHA
export FAKE_SUDO=1
exec "$@"
''')

    def write_stub(self, name, contents):
        path = self.bin / name
        path.write_text(contents)
        path.chmod(0o755)

    def deploy(self, **overrides):
        environment = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ["PATH"],
                           CALL_LOG=str(self.log), EXPECTED_REVISION=self.revision, **overrides)
        return subprocess.run(["bash", str(self.script), str(self.repo), self.revision],
                              env=environment, capture_output=True, text=True, timeout=10)

    def test_deploys_tested_commit_and_preserves_credentials_and_old_frontend(self):
        result = self.deploy()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.repo / "dist").is_symlink())
        self.assertEqual((self.repo / "dist/index.html").read_text(), "new frontend")
        self.assertEqual((self.repo / ".env.production").read_text(), "POSTGRES_PASSWORD=keep-existing-password\n")
        self.assertEqual((self.repo / ".deploy/current-sha").read_text().strip(), self.revision)
        backup = next((self.repo / ".deploy").glob("dist-before-*"))
        self.assertEqual((backup / "index.html").read_text(), "old frontend")
        calls = self.log.read_text()
        self.assertIn("git checkout --detach " + self.revision, calls)
        self.assertNotIn("git pull", calls)
        self.assertNotIn(" down ", calls)

    def test_revision_survives_sudo_environment_reset(self):
        result = self.deploy(FAKE_NEEDS_SUDO="1")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.repo / ".deploy/current-sha").read_text().strip(), self.revision)

    def test_dirty_checkout_is_not_overwritten(self):
        result = self.deploy(FAKE_DIRTY="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("tracked changes", result.stderr)
        self.assertNotIn("git checkout", self.log.read_text())
        self.assertNotIn("docker", self.log.read_text())

    def test_build_or_health_failure_keeps_old_frontend_and_release_marker(self):
        for failure in ("FAKE_BUILD_FAIL", "FAKE_HEALTH_FAIL"):
            with self.subTest(failure=failure):
                result = self.deploy(**{failure: "1"})
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual((self.repo / "dist/index.html").read_text(), "old frontend")
                self.assertFalse((self.repo / ".deploy/current-sha").exists())

    def test_older_workflow_cannot_replace_a_newer_deployment(self):
        (self.repo / ".deploy").mkdir()
        (self.repo / ".deploy/current-sha").write_text("b" * 40)
        result = self.deploy()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("newer deployment", result.stderr)
        self.assertNotIn("git checkout", self.log.read_text())
