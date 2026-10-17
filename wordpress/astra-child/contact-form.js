(() => {
  'use strict';
  const form = document.querySelector('[data-mt-contact-form]');
  if (!form) return;
  const status = form.querySelector('[data-mt-contact-status]');
  const submit = form.querySelector('[type="submit"]');
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    const config = window.MirrorTalkContact || {};
    if (!config.ajaxUrl) return;
    submit.disabled = true;
    form.setAttribute('aria-busy', 'true');
    status.classList.remove('is-success');
    status.textContent = 'Sending your message…';
    const payload = new FormData(form);
    payload.append('action', 'mirrortalk_contact_submit');
    payload.append('nonce', config.nonce || '');
    payload.append('issued_at', String(config.issuedAt || ''));
    payload.append('proof', config.proof || '');
    try {
      const response = await fetch(config.ajaxUrl, { method: 'POST', body: payload, credentials: 'same-origin' });
      const result = await response.json();
      status.textContent = result?.data?.message || (result?.success ? 'Thank you. Your message has been sent.' : 'Please review your message and try again.');
      status.classList.toggle('is-success', Boolean(result?.success));
      if (result?.success) {
        form.reset();
      }
    } catch (_) {
      status.textContent = 'We could not send your message just now. Please try again.';
    } finally {
      submit.disabled = false;
      form.removeAttribute('aria-busy');
    }
  });
})();
