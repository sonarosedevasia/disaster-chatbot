/**
 * DisasterSafe Chat Controller
 * Manages rule-based conversation flow, TTS/STT voice features,
 * undo/back steps, typing delays, and rich summary presentation.
 */

document.addEventListener('DOMContentLoaded', () => {
  const chatThread = document.getElementById('chatThread');
  const typingBox = document.getElementById('typingBox');
  const optionsGrid = document.getElementById('optionsGrid');
  const optionsCaption = document.getElementById('optionsCaption');
  const chatTextInput = document.getElementById('chatTextInput');
  const btnSendChat = document.getElementById('btnSendChat');
  const btnVoiceInput = document.getElementById('btnVoiceInput');
  const btnBackStep = document.getElementById('btnBackStep');
  const btnRestartChat = document.getElementById('btnRestartChat');
  const btnPrintPlan = document.getElementById('btnPrintPlan');
  const chatHazardSelect = document.getElementById('chatHazardSelect');
  const progressBarFill = document.getElementById('progressBarFill');
  const progressText = document.getElementById('progressText');

  // Application State
  const urlLang = new URLSearchParams(window.location.search).get('lang');
  if (urlLang) {
    localStorage.setItem('ds_lang', urlLang);
  }
  const state = {
    session_id: null,
    hazard_id: chatHazardSelect ? chatHazardSelect.value : 'flood',
    lang: urlLang || localStorage.getItem('ds_lang') || 'en',
    current_step_num: 1,
    is_complete: false,
    active_options: []
  };

  // Initialize Chat Session
  initChat();

  // Hazard Switcher Listener
  if (chatHazardSelect) {
    chatHazardSelect.addEventListener('change', () => {
      state.hazard_id = chatHazardSelect.value;
      const url = new URL(window.location.href);
      url.searchParams.set('hazard', state.hazard_id);
      window.history.pushState({}, '', url.toString());
      startSession();
    });
  }

  function initChat() {
    startSession();
    initComposer();
    initSpeechRecognition();
  }

  async function startSession() {
    state.current_step_num = 1;
    state.is_complete = false;
    state.active_options = [];
    chatThread.innerHTML = '';
    optionsGrid.innerHTML = '';
    if (btnPrintPlan) btnPrintPlan.style.display = 'none';
    if (btnBackStep) btnBackStep.disabled = true;
    updateProgress(1, 6);

    showTyping(true);

    try {
      const response = await fetch('/api/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hazard_id: state.hazard_id, lang: state.lang })
      });
      const data = await response.json();

      setTimeout(() => {
        showTyping(false);
        state.session_id = data.session_id;

        // 1. Render Welcome Greeting
        appendBotMessage({
          text: data.welcome_message,
          severity: 'info'
        });

        // 2. Render Initial Question
        setTimeout(() => {
          appendBotMessage({
            text: data.question,
            severity: data.severity || 'info'
          });
          renderOptions(data.options);
        }, 400);

      }, 550);

    } catch (err) {
      showTyping(false);
      appendBotMessage({
        text: 'Unable to connect to local safety server. Please verify the Flask server is running on port 5000.',
        severity: 'critical'
      });
    }
  }

  async function handleSelection(userChoiceText, optId = null) {
    if (!userChoiceText || userChoiceText.trim() === '') return;

    disableOptionButtons();
    appendUserMessage(userChoiceText);
    showTyping(true);

    try {
      const payload = {
        session_id: state.session_id,
        choice: optId || userChoiceText
      };

      const response = await fetch('/api/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await response.json();

      setTimeout(() => {
        showTyping(false);

        if (data.status === 'unmatched') {
          appendBotMessage({
            text: data.message,
            severity: 'warning'
          });
          renderOptions(data.options);
          return;
        }

        if (data.status !== 'success') {
          appendBotMessage({
            text: data.message || 'An error occurred during evaluation.',
            severity: 'critical'
          });
          return;
        }

        // Enable Back button if step history exists
        if (btnBackStep) btnBackStep.disabled = !data.can_go_back;

        // Render Advice chain
        const adviceList = data.advice || [];
        adviceList.forEach(adv => {
          appendBotMessage({
            text: adv.text,
            severity: adv.severity || 'info',
            source_id: adv.source_id
          });
        });

        // Next Question or Final Summary
        if (data.is_complete && data.summary) {
          state.is_complete = true;
          updateProgress(6, 6);
          setTimeout(() => {
            renderFinalSummaryCard(data.summary);
            if (btnPrintPlan) btnPrintPlan.style.display = 'inline-flex';
            renderRestartOptionButton();
          }, 350);
        } else if (data.question) {
          state.current_step_num++;
          updateProgress(state.current_step_num, 6);
          setTimeout(() => {
            appendBotMessage({
              text: data.question,
              severity: data.severity || 'info'
            });
            renderOptions(data.options);
          }, 300);
        }

      }, 600);

    } catch (err) {
      showTyping(false);
      appendBotMessage({
        text: 'Network communication failure. Emergency numbers remain available in the sidebar.',
        severity: 'critical'
      });
    }
  }

  // Back / Undo Action
  if (btnBackStep) {
    btnBackStep.addEventListener('click', async () => {
      showTyping(true);
      try {
        const resp = await fetch('/api/back', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: state.session_id })
        });
        const data = await resp.json();
        showTyping(false);

        if (data.status === 'success') {
          // Remove last user and bot bubble from UI
          removeLastInteraction();
          btnBackStep.disabled = !data.can_go_back;
          state.current_step_num = Math.max(1, state.current_step_num - 1);
          updateProgress(state.current_step_num, 6);
          renderOptions(data.options);
        } else {
          alert(data.message || 'Cannot undo further.');
        }
      } catch (e) {
        showTyping(false);
      }
    });
  }

  if (btnRestartChat) {
    btnRestartChat.addEventListener('click', () => {
      if (confirm('Restart disaster guidance assessment? Current answers will reset.')) {
        startSession();
      }
    });
  }

  if (btnPrintPlan) {
    btnPrintPlan.addEventListener('click', () => {
      window.print();
    });
  }

  // =========================================================================
  // MESSAGE RENDERING
  // =========================================================================
  function appendBotMessage(data) {
    const row = document.createElement('div');
    row.className = 'msg-row bot';

    const avatar = document.createElement('div');
    avatar.className = `msg-avatar sev-${data.severity || 'info'}`;
    avatar.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`;

    const content = document.createElement('div');
    content.className = 'msg-content-wrap';

    const bubble = document.createElement('div');
    bubble.className = `msg-bubble sev-${data.severity || 'info'}`;

    // Tag badge for warnings or danger
    if (data.severity === 'critical') {
      const tag = document.createElement('span');
      tag.className = 'bubble-tag tag-critical';
      tag.innerHTML = '⚠ CRITICAL LIFE-SAFETY ACTION';
      bubble.appendChild(tag);
    } else if (data.severity === 'warning') {
      const tag = document.createElement('span');
      tag.className = 'bubble-tag tag-warning';
      tag.innerHTML = '⚡ ADVISORY PRECAUTION';
      bubble.appendChild(tag);
    }

    const p = document.createElement('p');
    p.textContent = data.text;
    bubble.appendChild(p);

    if (data.source_id) {
      const srcMeta = document.createElement('span');
      srcMeta.className = 'source-badge-micro';
      srcMeta.textContent = `Ref: ${data.source_id.toUpperCase()}`;
      bubble.appendChild(srcMeta);
    }

    // Timestamp & Voice TTS Button
    const metaRow = document.createElement('div');
    metaRow.className = 'msg-meta-row';
    metaRow.innerHTML = `<span class="msg-time">${getFormattedTime()}</span>`;

    // Only render Listen (TTS) when language is English where native speech synthesis works reliably
    const isEnglish = (state.lang === 'en' || !state.lang);
    if (isEnglish && data.text && 'speechSynthesis' in window) {
      const ttsBtn = document.createElement('button');
      ttsBtn.type = 'button';
      ttsBtn.className = 'btn-tts-listen';
      ttsBtn.setAttribute('aria-label', 'Listen to guidance aloud');
      ttsBtn.innerHTML = `
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
        <span>Listen</span>
      `;
      ttsBtn.addEventListener('click', () => speakAloud(data.text, ttsBtn));
      metaRow.appendChild(ttsBtn);
    }

    content.appendChild(bubble);
    content.appendChild(metaRow);
    row.appendChild(avatar);
    row.appendChild(content);

    chatThread.appendChild(row);
    scrollBottom();
  }

  function appendUserMessage(text) {
    const row = document.createElement('div');
    row.className = 'msg-row user';

    const avatar = document.createElement('div');
    avatar.className = 'msg-avatar user-avatar';
    avatar.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`;

    const content = document.createElement('div');
    content.className = 'msg-content-wrap';

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble user-bubble';
    bubble.innerHTML = `<p>${text}</p>`;

    const metaRow = document.createElement('div');
    metaRow.className = 'msg-meta-row user-meta';
    metaRow.innerHTML = `<span class="msg-time">${getFormattedTime()}</span>`;

    content.appendChild(bubble);
    content.appendChild(metaRow);
    row.appendChild(avatar);
    row.appendChild(content);

    chatThread.appendChild(row);
    scrollBottom();
  }

  function removeLastInteraction() {
    const userRows = chatThread.querySelectorAll('.msg-row.user');
    if (userRows.length > 0) {
      const lastUser = userRows[userRows.length - 1];
      let sibling = lastUser.nextElementSibling;
      while (sibling) {
        const next = sibling.nextElementSibling;
        sibling.remove();
        sibling = next;
      }
      lastUser.remove();
    }
  }

  // =========================================================================
  // OPTIONS & CONTROLS
  // =========================================================================
  function renderOptions(options) {
    state.active_options = options || [];
    optionsGrid.innerHTML = '';

    if (!options || options.length === 0) {
      optionsCaption.textContent = 'Assessment complete.';
      return;
    }

    optionsCaption.textContent = 'Select an option to proceed:';

    options.forEach(opt => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn-quick-pill';
      btn.textContent = opt.text;
      btn.addEventListener('click', () => {
        handleSelection(opt.text, opt.id);
      });
      optionsGrid.appendChild(btn);
    });
  }

  function renderRestartOptionButton() {
    optionsGrid.innerHTML = '';
    optionsCaption.textContent = 'Guidance plan generated. You may restart at any time:';

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn-quick-pill selected';
    btn.innerHTML = `
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 0115-6.7L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 01-15 6.7L3 16"/><path d="M3 21v-5h5"/></svg>
      <span>Start New Assessment</span>
    `;
    btn.addEventListener('click', startSession);
    optionsGrid.appendChild(btn);
  }

  function disableOptionButtons() {
    const btns = optionsGrid.querySelectorAll('.btn-quick-pill');
    btns.forEach(b => { b.disabled = true; });
  }

  function showTyping(show) {
    if (typingBox) {
      typingBox.style.display = show ? 'flex' : 'none';
      if (show) scrollBottom();
    }
  }

  function updateProgress(curr, total) {
    const pct = Math.min(Math.round((curr / total) * 100), 100);
    if (progressBarFill) progressBarFill.style.width = `${pct}%`;
    if (progressText) progressText.textContent = `Step ${curr} of ~${total}`;
  }

  function scrollBottom() {
    setTimeout(() => {
      chatThread.scrollTop = chatThread.scrollHeight;
    }, 50);
  }

  function getFormattedTime() {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  // =========================================================================
  // VOICE FEATURES (SPEECH SYNTHESIS FOR ENGLISH & SPEECH RECOGNITION)
  // =========================================================================
  function stopAllSpeech() {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    document.querySelectorAll('.btn-tts-listen.speaking').forEach(b => {
      b.classList.remove('speaking');
      const label = b.querySelector('span');
      if (label) label.textContent = 'Listen';
    });
  }

  function cleanTextForSpeech(raw) {
    if (!raw) return '';
    return raw
      .replace(/<[^>]*>/g, ' ')
      .replace(/&nbsp;/g, ' ')
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/[\r\n]+/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function speakAloud(text, btn) {
    if (!('speechSynthesis' in window)) return;

    // Toggle off if currently playing
    if (btn && btn.classList.contains('speaking')) {
      stopAllSpeech();
      return;
    }

    stopAllSpeech();

    const clean = cleanTextForSpeech(text);
    if (!clean) return;

    const utterance = new SpeechSynthesisUtterance(clean);
    utterance.lang = 'en-US';
    utterance.rate = 0.95;

    // Pick an English voice if available
    const voices = window.speechSynthesis.getVoices() || [];
    const enVoice = voices.find(v => (v.lang || '').toLowerCase().startsWith('en'));
    if (enVoice) {
      utterance.voice = enVoice;
    }

    if (btn) {
      btn.classList.add('speaking');
      const label = btn.querySelector('span');
      if (label) label.textContent = 'Playing...';

      utterance.onend = () => {
        btn.classList.remove('speaking');
        if (label) label.textContent = 'Listen';
      };
      utterance.onerror = () => {
        btn.classList.remove('speaking');
        if (label) label.textContent = 'Listen';
      };
    }

    try {
      window.speechSynthesis.speak(utterance);
    } catch (e) {
      if (btn) {
        btn.classList.remove('speaking');
        const label = btn.querySelector('span');
        if (label) label.textContent = 'Listen';
      }
    }
  }

  function initSpeechRecognition() {
    if (!btnVoiceInput) return;
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      btnVoiceInput.style.display = 'none';
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = state.lang === 'ml' ? 'ml-IN' : (state.lang === 'hi' ? 'hi-IN' : 'en-IN');
    recognition.interimResults = false;

    btnVoiceInput.addEventListener('click', () => {
      btnVoiceInput.classList.add('listening');
      recognition.start();
    });

    recognition.onresult = (event) => {
      btnVoiceInput.classList.remove('listening');
      const spokenText = event.results[0][0].transcript;
      if (chatTextInput) chatTextInput.value = spokenText;
      handleSelection(spokenText);
    };

    recognition.onerror = () => {
      btnVoiceInput.classList.remove('listening');
    };

    recognition.onend = () => {
      btnVoiceInput.classList.remove('listening');
    };
  }

  // =========================================================================
  // COMPOSER TEXT INPUT
  // =========================================================================
  function initComposer() {
    function submitInput() {
      const val = chatTextInput.value.trim();
      if (!val) return;
      chatTextInput.value = '';
      handleSelection(val);
    }

    if (btnSendChat) btnSendChat.addEventListener('click', submitInput);
    if (chatTextInput) {
      chatTextInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          submitInput();
        }
      });
    }
  }

  // =========================================================================
  // FINAL SAFETY SUMMARY CARD RENDERING
  // =========================================================================
  function renderFinalSummaryCard(summary) {
    const card = document.createElement('div');
    card.className = 'final-plan-summary-card';

    const risk = summary.risk_level || 'MODERATE';
    let riskClass = 'mod';
    if (risk.includes('CRITICAL')) riskClass = 'crit';
    else if (risk.includes('HIGH')) riskClass = 'high';

    // Immediate Priority Actions
    let immedHtml = '';
    if (summary.immediate_actions && summary.immediate_actions.length > 0) {
      const items = summary.immediate_actions.map(act => `<li>${act}</li>`).join('');
      immedHtml = `
        <div class="summary-block immed-block">
          <div class="summary-block-title text-crit">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
            Immediate Priority Life-Safety Actions
          </div>
          <ul class="summary-bullet-list">${items}</ul>
        </div>
      `;
    }

    // Next Steps Checklist
    let nextHtml = '';
    if (summary.next_steps && summary.next_steps.length > 0) {
      const items = summary.next_steps.map(s => `<li>${s}</li>`).join('');
      nextHtml = `
        <div class="summary-block">
          <div class="summary-block-title text-safe">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
            Personalized Safety &amp; Evacuation Checklist
          </div>
          <ul class="summary-bullet-list">${items}</ul>
        </div>
      `;
    }

    // Preparation & Packing
    let prepHtml = '';
    if (summary.preparation && summary.preparation.length > 0) {
      const items = summary.preparation.map(p => `<li>${p}</li>`).join('');
      prepHtml = `
        <div class="summary-block">
          <div class="summary-block-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>
            Preparation &amp; Utility Mitigation
          </div>
          <ul class="summary-bullet-list">${items}</ul>
        </div>
      `;
    }

    card.innerHTML = `
      <div class="summary-header">
        <div>
          <h2 class="summary-main-title">Personalized Disaster Safety Plan</h2>
          <span class="summary-subtitle">Generated strictly from NDMA &amp; KSDMA protocols</span>
        </div>
        <span class="risk-pill ${riskClass}">${risk}</span>
      </div>

      ${immedHtml}
      ${nextHtml}
      ${prepHtml}

      <div class="summary-block">
        <div class="summary-block-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z"/></svg>
          Verified Emergency Rescue Contacts (India)
        </div>
        <div class="summary-numbers-row">
          <a href="tel:112" class="num-chip-item priority-chip"><strong>112</strong> National ERSS</a>
          <a href="tel:1070" class="num-chip-item"><strong>1070</strong> SEOC Kerala</a>
          <a href="tel:1077" class="num-chip-item"><strong>1077</strong> DEOC Collectorate</a>
          <a href="tel:108" class="num-chip-item"><strong>108</strong> Ambulance</a>
        </div>
      </div>

      <div class="summary-export-toolbar">
        <button type="button" class="btn-summary-tool" onclick="window.print()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 012-2h16a2 2 0 012 2v5a2 2 0 01-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
          Print / PDF
        </button>
        <a href="/api/export/txt" class="btn-summary-tool" download>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Download TXT
        </a>
        <button type="button" class="btn-summary-tool" id="btnCopyPlan">Copy Plan</button>
        <button type="button" class="btn-summary-tool" id="btnShareWhatsApp">Share on WhatsApp</button>
      </div>

      <div class="summary-disclaimer-note">
        ${summary.disclaimer || ''}
      </div>
    `;

    chatThread.appendChild(card);
    scrollBottom();

    // Attach actions
    const copyBtn = card.querySelector('#btnCopyPlan');
    if (copyBtn) {
      copyBtn.addEventListener('click', () => {
        const textToCopy = `DISASTERSAFE EMERGENCY PLAN:\nStatus: ${risk}\nImmediate Actions:\n` +
          (summary.immediate_actions || []).join('\n') + `\nEmergency Contacts: 112 (ERSS), 1070 (SEOC), 1077 (DEOC)`;
        navigator.clipboard.writeText(textToCopy).then(() => {
          copyBtn.textContent = 'Copied!';
          setTimeout(() => { copyBtn.textContent = 'Copy Plan'; }, 2000);
        });
      });
    }

    const waBtn = card.querySelector('#btnShareWhatsApp');
    if (waBtn) {
      waBtn.addEventListener('click', () => {
        const textToShare = encodeURIComponent(`*DISASTERSAFE EMERGENCY PLAN:*\nStatus: ${risk}\n` +
          `*Immediate Actions:*\n` + (summary.immediate_actions || []).map(a => `• ${a}`).join('\n') +
          `\n\n*Emergency Helplines:* 112 (National ERSS) | 1070 (SEOC Kerala) | 1077 (DEOC)`);
        window.open(`https://wa.me/?text=${textToShare}`, '_blank');
      });
    }
  }
});

