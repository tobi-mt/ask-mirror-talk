(() => {
  'use strict';
  const input = document.querySelector('[data-mti-filter]');
  if (!input) return;
  input.addEventListener('input', () => {
    const query = input.value.trim().toLowerCase();
    document.querySelectorAll('.mti-filterable tbody tr').forEach((row) => {
      row.hidden = Boolean(query && !row.textContent.toLowerCase().includes(query));
    });
  });
})();
