# Mirror Talk 8.10.1

Corrective release following the live 8.10.0 administrator audit.

- Prevents legacy or malformed saved decision values from crashing an individual Editorial Composer report.
- Whitelists the seven supported Composer decisions instead of rendering unexpected historical keys.
- Normalizes decision state, status, and labels before administrator output.
- Defensively casts generated report values before shortening or escaping them.
- Advances the processing version so saved decision records are normalized during the continuing archive migration.

The public website, original content, URLs, quotations, transcripts, and embeds remain unchanged.
