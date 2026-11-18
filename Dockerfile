# The harness image: characterisation tests, control tests, compare tool and load generator.
# Built by scripts/sandbox.sh and run as a pod inside the sandbox namespace.
FROM python:3.12-slim
WORKDIR /work
RUN pip install --no-cache-dir pytest==8.3.4 httpx==0.28.1 pyyaml==6.0.2
COPY tests ./tests
COPY tools ./tools
COPY pytest.ini .
