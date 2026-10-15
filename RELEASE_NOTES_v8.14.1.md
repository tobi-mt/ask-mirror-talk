# Mirror Talk 8.14.1 — Intelligence Admin Navigation Repair

## Fixed

- Restores **Mirror Talk Intelligence → Overview** as the top-level dashboard.
- Gives the top-level Intelligence menu a valid `admin.php?page=mirror-talk-intelligence` destination.
- Prevents **Listening platforms** from being promoted into the parent menu URL.
- Registers Listening Platforms, Editorial Composer and Taxonomy Governance only after the Intelligence parent exists.

## Verification

- Listen Everywhere static suite: 9 tests passed.
- Theme release-quality gate: passed.
- ZIP integrity: passed.
- Packaged theme contains `style.css` at `astra-child/style.css` and reports version 8.14.1.

## Deployment

Upload and activate `wordpress/astra-child-v8.14.1.zip`. Opening **Mirror Talk Intelligence** should load the dashboard; **Listening platforms** should load its dedicated administration table.
