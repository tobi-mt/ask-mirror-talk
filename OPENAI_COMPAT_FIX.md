# OpenAI API Compatibility Fix

## Issue

The application was encountering `BadRequestError` from OpenAI API with the error:

```
Unsupported parameter: 'max_tokens' is not supported with this model. 
Use 'max_completion_tokens' instead.
```

This was happening for newer models like `gpt-5.2`, `gpt-5-mini`, and `gpt-4o-mini` which require the `max_completion_tokens` parameter instead of the legacy `max_tokens` parameter.

## Root Cause

While the code had model detection logic to determine which parameter to use, the error handling wasn't properly catching and retrying when the OpenAI API rejected the wrong parameter. The existing exception handler was checking for a specific error message format that didn't match what OpenAI's `BadRequestError` actually returned.

## Solution

Enhanced the error handling in `app/core/openai_compat.py`:

1. **Improved Error Detection**: Updated the error message checking to handle the actual format of OpenAI's error messages, including "unsupported parameter" errors.

2. **Robust Retry Logic**: When the API rejects a parameter (either `max_tokens` or `max_completion_tokens`), the code now:
   - Catches the error
   - Swaps to the alternative parameter name
   - Retries the request automatically

3. **Added Logging**: Added informational logging when parameter retries occur, making it easier to track and debug these compatibility issues.

4. **Comprehensive Testing**: Added tests to verify the retry logic works in both directions:
   - Retry from `max_tokens` to `max_completion_tokens`
   - Retry from `max_completion_tokens` to `max_tokens`

## What Models Are Affected

Models using `max_completion_tokens`:
- GPT-5 series: `gpt-5`, `gpt-5.2`, `gpt-5-mini`, etc.
- O-series: `o1`, `o3`, `o4`
- Newer GPT-4 variants: `gpt-4o`, `gpt-4o-mini`, `gpt-4.1`, `gpt-4-2024-*`, `gpt-4-turbo-2024-*`

Models still using `max_tokens`:
- Standard GPT-4: `gpt-4`, `gpt-4-turbo`
- GPT-3.5: `gpt-3.5-turbo`
- Older models

## Testing

All tests pass:
```bash
pytest tests/test_openai_compat.py -v
```

## Deployment

This fix is backward compatible and doesn't require any configuration changes. It will automatically handle both old and new OpenAI API requirements.
