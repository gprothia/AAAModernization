# Characterisation harness

Behaviour tests extracted from the legacy service (`/extract-harness`). The same test runs
against **both** systems (standards/modernization.md, MOD-7):

```
TARGET=legacy  BASE_URL=http://legacy-membership:8080  pytest tests/harness   # must be 100% green first (MOD-6)
TARGET=modern  BASE_URL=http://membership:8080         pytest tests/harness   # the new service, same tests
```

- `adapters.py` hides the difference in URLs, sign-in and formats: each test asks the
  service to *look up*, *renew* or *cancel*, and gets back a normalised `Outcome`.
- Each test is tagged with the legacy behaviour it pins (`@pytest.mark.behaviour("MEM-003-B1")`)
  and the to-be criterion it proves (`@pytest.mark.ac("MEM-003-AC1")`).
- A test that expects a different result per target is an **approved deviation** and must say
  which: `@pytest.mark.deviation("DEV-003-04")`. `scripts/check_traceability.py` rejects a
  deviation ID that is not in the to-be spec's "Approved deviations" table.
- Data and clock: both systems start from the same seed and a frozen clock (2026-03-10 12:00
  UTC). In the GKE sandbox the legacy service's clock is set with libfaketime and its data is
  reloaded by a sandbox-only reset sidecar; the new service uses its `/test/...` hooks, which
  exist only in sandboxes (SEC-2).
