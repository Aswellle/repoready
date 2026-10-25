"""Boundary tests: no network modules at import time.

The check is import-time only: it proves the package does not pull
network modules into sys.modules when imported. It does not claim to
prove "no network at runtime"; docs and README must not make that
stronger claim (docs/spec/01-architecture-rules.md §3).
"""

import os
import subprocess
import sys
import unittest
from pathlib import Path

NETWORK_MODULES = (
    "socket",
    "http",
    "http.client",
    "urllib.request",
    "ftplib",
    "smtplib",
    "telnetlib",
    "xmlrpc.client",
)

_IMPORT_CODE = (
    "import sys;"
    "import repoready, repoready.cli, repoready.models, repoready.report_json,"
    " repoready.report_text, repoready.scanner;"
    "net = {'socket','http','http.client','urllib.request','ftplib',"
    "'smtplib','telnetlib','xmlrpc.client'};"
    "bad = sorted(net & set(sys.modules));"
    "print('network modules imported:', bad);"
    "sys.exit(1 if bad else 0)"
)


class NoNetworkImportsTests(unittest.TestCase):
    def test_importing_package_pulls_no_network_modules(self):
        env = dict(os.environ)
        src = str(Path(__file__).resolve().parents[1] / "src")
        env["PYTHONPATH"] = (
            os.pathsep.join([src, env["PYTHONPATH"]])
            if env.get("PYTHONPATH")
            else src
        )
        proc = subprocess.run(
            [sys.executable, "-c", _IMPORT_CODE],
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
        )
        self.assertEqual(
            proc.returncode,
            0,
            f"stdout={proc.stdout}\nstderr={proc.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
