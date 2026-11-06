/**
 * DisasterSafe Emergency Kit Checklist Controller
 * Persists checked items in localStorage, calculates readiness percentage,
 * and handles clean print layout.
 */

document.addEventListener('DOMContentLoaded', () => {
  const checkboxes = document.querySelectorAll('.kit-checkbox');
  const kitPercent = document.getElementById('kitPercent');
  const kitFill = document.getElementById('kitFill');
  const btnResetKit = document.getElementById('btnResetKit');
  const btnPrintKit = document.getElementById('btnPrintKit');

  const STORAGE_KEY = 'ds_emergency_kit_checks';

  // Load saved state
  const savedChecks = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');

  checkboxes.forEach(cb => {
    const id = cb.getAttribute('data-id');
    if (savedChecks[id]) {
      cb.checked = true;
    }

    cb.addEventListener('change', () => {
      savedChecks[id] = cb.checked;
      localStorage.setItem(STORAGE_KEY, JSON.stringify(savedChecks));
      updateProgress();
    });
  });

  updateProgress();

  function updateProgress() {
    let checkedCount = 0;
    checkboxes.forEach(cb => {
      if (cb.checked) checkedCount++;
    });

    const total = checkboxes.length || 1;
    const pct = Math.round((checkedCount / total) * 100);

    if (kitPercent) kitPercent.textContent = `${pct}%`;
    if (kitFill) kitFill.style.width = `${pct}%`;
  }

  if (btnResetKit) {
    btnResetKit.addEventListener('click', () => {
      if (confirm('Reset all checklist items?')) {
        checkboxes.forEach(cb => { cb.checked = false; });
        localStorage.removeItem(STORAGE_KEY);
        updateProgress();
      }
    });
  }

  if (btnPrintKit) {
    btnPrintKit.addEventListener('click', () => {
      window.print();
    });
  }
});

