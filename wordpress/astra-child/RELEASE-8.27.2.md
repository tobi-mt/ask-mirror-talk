# Mirror Talk 8.27.2

## Legacy Elementor template recovery

- Normalizes obsolete `elementor_*` page-template metadata before WordPress validates a converted post.
- Retains the checksum-protected snapshot before changing that metadata.
- Restores the complete original document automatically if WordPress rejects the commit.
- Allows the existing bounded retry to resume from the verified candidate rather than quarantining an otherwise valid document.

## Production evidence

- 8.27.1 reduced the live queue to 62 pending documents with seven publicly verified migrations.
- Desktop and mobile public verification returned HTTP 200 for completed documents.
- No documents were quarantined and no 504 response was observed.
