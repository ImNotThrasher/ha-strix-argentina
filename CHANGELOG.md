# Changelog

## 0.2.2 — HACS catalog readiness and screenshots

- Declare Argentina (`AR`) as the integration's supported service country in HACS metadata; this does not geographically block installation.
- Add real Home Assistant dashboard and vehicle entity screenshots to the README.
- Remove the abandoned historical v0.1.0 release workflow and outdated private-repository note.
- No runtime, API, authentication, vehicle entity or device-control changes.

## 0.2.1 — HACS packaging and documentation

- Place integration icon assets under `custom_components/strix_argentina/brand/` so HACS brand validation succeeds.
- Improve README with HACS installation buttons, latest-release links and dynamic GitHub badges.
- Validate HACS, Hassfest, unit tests, lint and isolated Home Assistant multi-vehicle runtime tests in CI.
- No changes to Strix API requests, authentication, entity IDs or vehicle-control behavior.


## 0.2.0 — Release candidate

- Dynamic discovery of additional Strix vehicles without restarting Home Assistant.
- Home Assistant reauthentication flow for changed account passwords.
- Dedicated API connectivity binary sensor and last successful API poll timestamp.
- Optional GPS data stale binary sensor (15-minute threshold), separate from cloud API health.
- Validation of GPS coordinates, OAuth tokens and malformed vehicle responses.
- OAuth concurrency tests, API error tests and simulated second-vehicle discovery tests.
- Sanitized diagnostics and Spanish configuration translations.
- Ruff, unit tests and Hassfest CI checks.
- README documentation of historical LoJack Argentina branding and independent project status.

### Upgrade notes

- Existing vehicle unique IDs and integration domain remain unchanged.
- The old optional `sensor.*_gps_stale` (boolean represented as a sensor) is replaced by a new `binary_sensor.*_gps_data_stale` entity. If you enabled the old optional sensor, update your dashboards or automations manually.
- Validate the release candidate on Home Assistant before creating a public GitHub release. HACS validation requires a public repository.
