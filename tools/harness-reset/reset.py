"""Sandbox-only sidecar for the legacy pod: reload the seed data and set the frozen clock.

POST /reset {"clock": "2026-03-10 12:00:00"}  ->  RunScript seed.sql into H2; write the
libfaketime timestamp file the legacy JVM reads (FAKETIME_TIMESTAMP_FILE).
"""

import json
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer

DB = "jdbc:h2:tcp://localhost:9092/mem:members"


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])) or b"{}")
        # Fixed arguments only; the request body supplies just the clock value.
        subprocess.run(  # noqa: S603
            [
                "/opt/java/openjdk/bin/java",
                "-cp",
                "/h2.jar",
                "org.h2.tools.RunScript",
                "-url",
                DB,
                "-script",
                "/reset.sql",
            ],
            check=True,
        )
        with open("/clock/faketime.rc", "w") as f:
            f.write("@" + body.get("clock", "2026-03-10 12:00:00"))
        self.send_response(200)
        self.end_headers()


HTTPServer(("", 9000), Handler).serve_forever()
