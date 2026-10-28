# Strix Argentina for Home Assistant

Unofficial custom integration for monitoring Strix Argentina GPS-tracked vehicles in Home Assistant.

> [!IMPORTANT]
> This is an independent community project. It is **not affiliated with, endorsed by, or supported by Strix Argentina**. Strix and its associated names and logos are trademarks of their respective owners. References to those marks are for identification only; no trademark rights or official affiliation are claimed.

## Table of contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Manual installation](#manual-installation)
  - [HACS custom repository](#hacs-custom-repository)
- [Authentication](#authentication)
- [Upgrading an existing manual installation](#upgrading-an-existing-manual-installation)
- [Privacy](#privacy)
- [Diagnostics and troubleshooting](#diagnostics-and-troubleshooting)
- [Development and validation](#development-and-validation)
- [License and trademarks](#license-and-trademarks)

## Features

- Vehicle GPS location via a `device_tracker` entity
- Speed, heading, user-declared mileage, reported GPS distance, last GPS update and GPS age
- Ignition, motion, towing and fuel-cutoff binary sensors
- Automatic polling approximately every 120 seconds
- Vehicle metadata from the Strix API
- Automatic discovery of newly added vehicles during polling (no restart required)
- Safe integration diagnostics and English/Spanish configuration translations

**Limitations:** Strix GPS data may be delayed or unavailable. The meaning of the reported GPS distance has not been independently verified. This integration is not an emergency, safety or guaranteed real-time tracking system.

## Requirements

- Home Assistant with custom integration support
- An active Strix Argentina account with access to at least one vehicle
- Strix account username and password
- The OAuth Basic Authorization client value required by the Strix API
- Network access to `https://api.strix.com.ar`

## Installation

### Manual installation

1. Copy `custom_components/strix_argentina` from this repository into the `custom_components` folder in your Home Assistant configuration directory.
2. Restart Home Assistant.
3. Open **Settings → Devices & services → Add integration**.
4. Search for **Strix Argentina** and complete the configuration form.

### HACS custom repository

**The repository must be public for normal HACS custom-repository installation.**

1. Open HACS and add `https://github.com/ImNotThrasher/ha-strix-argentina` as a **custom repository** of type **Integration**.
2. Download the integration.
3. Restart Home Assistant.
4. Add **Strix Argentina** under **Settings → Devices & services**.

HACS downloads the integration into your Home Assistant installation; it does not execute Python code remotely from GitHub.

## Authentication

The configuration form requests:

| Field | Description |
| --- | --- |
| Username | Strix account username |
| Password | Strix account password |
| Client device ID | Optional; leave blank to generate a UUID during initial setup |
| OAuth Basic Authorization | API client authorization value following `Basic ` in the Authorization header (omit the prefix) |

The integration authenticates using the Strix OAuth endpoint and obtains access and refresh tokens. The account credentials and OAuth Basic value are stored in Home Assistant's config-entry storage, **not in this GitHub repository**; access and refresh tokens are held in memory. The OAuth Basic client value is **not** the same thing as your account password.

The integration does not currently provide an automated way to obtain the OAuth Basic client value. The API and its authentication flow are unofficial and may change without notice.

**Never publish credentials, tokens, authorization headers, Home Assistant backups or the `.storage` directory.**

## Upgrading an existing manual installation

The integration intentionally preserves the domain `strix_argentina` and existing entity unique IDs. This helps retain entity registry entries, dashboards, automations and history.

1. Back up your Home Assistant configuration.
2. **Do not delete the Strix Argentina integration** from Devices & services or remove its entities.
3. When HACS installation is available, install the custom repository over the existing component files.
4. Restart Home Assistant and verify entity IDs and dashboard references.
5. Use HACS for future updates instead of manually overwriting the same files.

Always verify your installation before making changes. Existing dashboards depend on your Home Assistant entity registry, not just the repository name.

## Privacy

Vehicle locations, license plates, device identifiers and credentials are sensitive. Limit access to your Home Assistant instance, dashboards, diagnostics and backups.

## Diagnostics and troubleshooting

From **Settings → Devices & services → Strix Argentina**, download integration diagnostics when investigating issues. Diagnostics include the vehicle count, last update status and polling interval. Account credentials are redacted; vehicle identifiers, location coordinates and raw API payloads are intentionally omitted. Do not assume every diagnostic or Home Assistant log is safe to publish without reviewing it.

Transient API outages are reported as update failures. Rejected account credentials are treated as authentication failures and may trigger Home Assistant reauthentication handling. Newly added vehicles are registered after a successful poll; existing entity unique IDs are preserved. Vehicles removed from the account become unavailable rather than having their registry entries deleted.

## Development and validation

This integration is currently at version `0.1.0`. The API is unofficial. Bug reports and contributions are welcome. Hassfest runs on every push and pull request; the HACS validation job runs only when the repository is public. The Python unit suite covers payload helpers, OAuth refresh and error handling, and dynamic vehicle discovery. Run locally with `python -m pip install aiohttp` and `python -m unittest discover -s tests`. These checks validate packaging and selected behavior; they do not guarantee that the external Strix API will remain compatible.

## License and trademarks

The source code is licensed under the **GNU General Public License v3.0 (GPL-3.0)**. See [LICENSE](LICENSE). The Strix name and logo belong to their respective owners; the project's trademark disclaimer does not constitute a license to use third-party assets.
