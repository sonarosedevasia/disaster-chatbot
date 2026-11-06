/**
 * DisasterSafe Family Emergency Plan Builder Controller
 * Synchronizes inputs to live preview, auto-saves to localStorage,
 * and handles PDF/Print rendering.
 */

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('familyPlanForm');
  const btnPrint = document.getElementById('btnPrintFamilyPlan');
  const btnClear = document.getElementById('btnClearPlan');

  const fields = {
    headName: { input: document.getElementById('headName'), prev: document.getElementById('prevHead') },
    headPhone: { input: document.getElementById('headPhone'), prev: null },
    memberDetails: { input: document.getElementById('memberDetails'), prev: document.getElementById('prevMembers') },
    primaryMeeting: { input: document.getElementById('primaryMeeting'), prev: document.getElementById('prevMeet1') },
    secondaryMeeting: { input: document.getElementById('secondaryMeeting'), prev: document.getElementById('prevMeet2') },
    outContactName: { input: document.getElementById('outContactName'), prev: document.getElementById('prevOut') },
    outContactPhone: { input: document.getElementById('outContactPhone'), prev: null },
    nearestCamp: { input: document.getElementById('nearestCamp'), prev: document.getElementById('prevCamp') },
    medicalNotes: { input: document.getElementById('medicalNotes'), prev: document.getElementById('prevMed') }
  };

  const STORAGE_KEY = 'ds_family_plan_data';

  // Load saved data
  const savedData = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
  for (const [key, fieldObj] of Object.entries(fields)) {
    if (fieldObj.input && savedData[key]) {
      fieldObj.input.value = savedData[key];
    }
  }
  updatePreview();

  // Listeners on inputs
  for (const [key, fieldObj] of Object.entries(fields)) {
    if (fieldObj.input) {
      fieldObj.input.addEventListener('input', () => {
        saveData();
        updatePreview();
      });
    }
  }

  function saveData() {
    const dataToSave = {};
    for (const [key, fieldObj] of Object.entries(fields)) {
      if (fieldObj.input) dataToSave[key] = fieldObj.input.value;
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(dataToSave));
  }

  function updatePreview() {
    const leadVal = fields.headName.input.value.trim();
    const phoneVal = fields.headPhone.input.value.trim();
    if (fields.headName.prev) {
      fields.headName.prev.textContent = leadVal ? `${leadVal} (${phoneVal || 'No phone'})` : 'Not yet entered';
    }

    if (fields.memberDetails.prev) {
      fields.memberDetails.prev.textContent = fields.memberDetails.input.value.trim() || 'Not yet entered';
    }

    if (fields.primaryMeeting.prev) {
      fields.primaryMeeting.prev.textContent = fields.primaryMeeting.input.value.trim() || 'Not yet entered';
    }

    if (fields.secondaryMeeting.prev) {
      fields.secondaryMeeting.prev.textContent = fields.secondaryMeeting.input.value.trim() || 'Not yet entered';
    }

    const outName = fields.outContactName.input.value.trim();
    const outPhone = fields.outContactPhone.input.value.trim();
    if (fields.outContactName.prev) {
      fields.outContactName.prev.textContent = outName ? `${outName} (${outPhone || 'No phone'})` : 'Not yet entered';
    }

    if (fields.nearestCamp.prev) {
      fields.nearestCamp.prev.textContent = fields.nearestCamp.input.value.trim() || 'Not yet entered';
    }

    if (fields.medicalNotes.prev) {
      fields.medicalNotes.prev.textContent = fields.medicalNotes.input.value.trim() || 'None entered';
    }
  }

  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      saveData();
      alert('Family disaster plan saved successfully in browser memory!');
    });
  }

  if (btnPrint) {
    btnPrint.addEventListener('click', () => {
      window.print();
    });
  }

  if (btnClear) {
    btnClear.addEventListener('click', () => {
      if (confirm('Clear the entire family plan?')) {
        for (const [key, fieldObj] of Object.entries(fields)) {
          if (fieldObj.input) fieldObj.input.value = '';
        }
        localStorage.removeItem(STORAGE_KEY);
        updatePreview();
      }
    });
  }
});

