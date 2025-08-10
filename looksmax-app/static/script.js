const form = document.getElementById('analyze-form');
const statusEl = document.getElementById('status');
const errorEl = document.getElementById('error');
const resultEl = document.getElementById('result');
const submitBtn = document.getElementById('submitBtn');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  errorEl.textContent = '';
  resultEl.style.display = 'none';
  resultEl.textContent = '';

  const fd = new FormData(form);

  if (!fd.get('image')) {
    errorEl.textContent = 'Please select an image.';
    return;
  }

  submitBtn.disabled = true;
  statusEl.textContent = 'Analyzing…';

  try {
    const res = await fetch('/analyze', {
      method: 'POST',
      body: fd
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || `Request failed (${res.status})`);
    }

    const data = await res.json();
    resultEl.textContent = data.text || '';
    resultEl.style.display = 'block';
  } catch (err) {
    errorEl.textContent = err.message || String(err);
  } finally {
    submitBtn.disabled = false;
    statusEl.textContent = '';
  }
});