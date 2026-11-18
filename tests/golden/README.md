# Golden traffic (differential testing, MOD-10)

`membership-golden.jsonl` is a sample of real requests to the legacy service and its
responses, recorded during discovery and scrubbed of personal data (names and phones
replaced, IDs mapped to the seed members). `tools/compare_legacy.py` replays every request to
the legacy and the new service and compares the normalised responses.

A difference is allowed only if it is listed in `allowed_differences.yaml`, and every entry
there must name an approved deviation in a to-be spec. Anything else is an unexplained
difference and fails the check.
