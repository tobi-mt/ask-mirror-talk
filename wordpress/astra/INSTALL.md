# Astra Upload Instructions

## Files to upload into the Astra theme folder
Upload these files into:
`wp-content/themes/astra/`

- `ask-mirror-talk.php`
- `ask-mirror-talk.js`
- `ask-mirror-talk.css`

## Enable the shortcode
Add this line near the bottom of Astra's `functions.php`:

```php
require_once get_stylesheet_directory() . '/ask-mirror-talk.php';
```

## Add the shortcode to a page
Use this shortcode in your WordPress page:

```
[ask_mirror_talk]
```

## WPGetAPI setup requirement
Make sure WPGetAPI has:
- `api_id`: `mirror_talk_ask`
- `endpoint_id`: `mirror_talk_ask`

The AJAX handler will call:
```
wpgetapi_endpoint('mirror_talk_ask', 'mirror_talk_ask', array('debug' => false, 'body' => array('question' => $question)));
```
