/**
 * FloodSafe - Intelligent Flood Safety Guidance Chatbot
 * Client-Side Application Logic & State Controller
 *
 * Implements:
 * - Rule-based decision-tree interaction via Flask API
 * - Animated typing indicator and message rendering
 * - Clickable option pills & keyboard text input support
 * - Final personalized safety checklist card
 * - Mermaid.js interactive flowchart pan/zoom controls
 * - View switching & offline fallback handling
 */

document.addEventListener('DOMContentLoaded', () => {
  // Application State
  const state = {
    current_step: 'START',
    user_data: {},
    is_complete: false,
    zoom_level: 1.0,
    chat_history: []
  };

  // DOM Elements - Navigation & Views
  const navTabs = document.querySelectorAll('.nav-tab');
  const tabViews = document.querySelectorAll('.tab-view');
  const btnRestartChat = document.getElementById('btnRestartChat');
  const btnPrintChat = document.getElementById('btnPrintChat');

  // DOM Elements - Chat Workspace
  const chatMessages = document.getElementById('chatMessages');
  const typingIndicator = document.getElementById('typingIndicator');
  const optionsGrid = document.getElementById('optionsGrid');
  const optionsInstruction = document.getElementById('optionsInstruction');
  const userTextInput = document.getElementById('userTextInput');
  const btnSendText = document.getElementById('btnSendText');

  // DOM Elements - Flowchart Controls
  const btnZoomIn = document.getElementById('btnZoomIn');
  const btnZoomOut = document.getElementById('btnZoomOut');
  const btnResetZoom = document.getElementById('btnResetZoom');
  const btnToggleSource = document.getElementById('btnToggleSource');
  const sourceCodePanel = document.getElementById('sourceCodePanel');
  const sourceCodeText = document.getElementById('sourceCodeText');
  const btnCopyCode = document.getElementById('btnCopyCode');
  const mermaidDiagram = document.getElementById('mermaidDiagram');

  // Active current options cache
  let currentOptions = [];

  // =========================================================================
  // INITIALIZATION
  // =========================================================================
  initMermaid();
  initTabNavigation();
  initFlowchartControls();
  initChatInput();
  startNewAssessment();

  // Check if server indicated initial view (e.g. /flowchart route)
  const initialView = document.body.getAttribute('data-initial-view');
  if (initialView === 'flowchart') {
    switchTab('flowchartSection');
  }

  // =========================================================================
  // TAB NAVIGATION
  // =========================================================================
  function initTabNavigation() {
    navTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const targetId = tab.getAttribute('data-target');
        switchTab(targetId);
      });
    });
  }

  function switchTab(targetId) {
    navTabs.forEach(t => {
      const match = t.getAttribute('data-target') === targetId;
      t.classList.toggle('active', match);
    });

    tabViews.forEach(v => {
      const match = v.id === targetId;
      v.classList.toggle('active', match);
    });

    if (targetId === 'flowchartSection') {
      renderFlowchart();
    }
  }

  // =========================================================================
  // CHATBOT ENGINE & API INTEGRATION
  // =========================================================================

  async function startNewAssessment() {
    // Reset state
    state.current_step = 'START';
    state.user_data = {};
    state.is_complete = false;
    currentOptions = [];
    chatMessages.innerHTML = '';
    optionsGrid.innerHTML = '';
    if (btnPrintChat) btnPrintChat.style.display = 'none';

    showTyping(true);

    try {
      const response = await fetch('/api/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();

      setTimeout(() => {
        showTyping(false);

        // 1. Render Welcome Greeting
        appendBotMessage({
          text: data.welcome_message,
          alert_level: 'info'
        });

        // 2. Render Initial Question (Q1)
        setTimeout(() => {
          appendBotMessage({
            text: data.question,
            alert_level: 'info'
          });

          state.current_step = data.next_step;
          renderOptionButtons(data.options);
        }, 400);

      }, 600);

    } catch (err) {
      showTyping(false);
      console.error('Error starting assessment:', err);
      appendBotMessage({
        text: 'Unable to connect to FloodSafe server. Please check your local server connection and try again.',
        alert_level: 'danger'
      });
    }
  }

  async function handleUserChoice(choiceText) {
    if (!choiceText || choiceText.trim() === '') return;

    // Disable active buttons to prevent multi-clicking
    disableActiveOptionButtons();

    // Append user selection to chat
    appendUserMessage(choiceText);

    // Show bot thinking indicator
    showTyping(true);

    try {
      const payload = {
        current_step: state.current_step,
        choice: choiceText,
        user_data: state.user_data
      };

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      setTimeout(() => {
        showTyping(false);

        if (data.status !== 'success') {
          appendBotMessage({
            text: data.message || 'An error occurred during evaluation.',
            alert_level: 'danger'
          });
          return;
        }

        // Update local state with latest user data and step
        state.user_data = data.user_data || state.user_data;
        state.current_step = data.next_step;
        state.is_complete = data.is_complete;

        // Render Guidance Bullet Points
        if (data.guidance && data.guidance.length > 0) {
          appendBotMessage({
            guidance: data.guidance,
            alert_level: data.alert_level || 'info'
          });
        }

        // Check if next question exists
        if (data.next_question && !data.is_complete) {
          setTimeout(() => {
            appendBotMessage({
              text: data.next_question,
              alert_level: 'info'
            });
            renderOptionButtons(data.next_options);
          }, 350);
        }

        // If completed, render final summary card
        if (data.is_complete && data.summary) {
          setTimeout(() => {
            renderFinalSummaryCard(data.summary);
            if (btnPrintChat) btnPrintChat.style.display = 'inline-flex';
            renderRestartOptionButton();
          }, 450);
        }

      }, 650);

    } catch (err) {
      showTyping(false);
      console.error('Error in chat step:', err);
      appendBotMessage({
        text: 'Network communication error. Please verify the Flask server is running on port 5000.',
        alert_level: 'danger'
      });
    }
  }

  // =========================================================================
  // MESSAGE RENDERING HELPERS
  // =========================================================================

  function appendBotMessage(data) {
    const row = document.createElement('div');
    row.className = 'message-row bot';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`;

    const content = document.createElement('div');
    content.className = 'message-content';

    const bubble = document.createElement('div');
    bubble.className = `message-bubble alert-${data.alert_level || 'info'}`;

    // Tag badge for warnings or danger
    if (data.alert_level === 'danger') {
      const tag = document.createElement('span');
      tag.className = 'bubble-tag tag-danger';
      tag.innerHTML = '⚠ Critical Emergency Safety Action';
      bubble.appendChild(tag);
    } else if (data.alert_level === 'warning') {
      const tag = document.createElement('span');
      tag.className = 'bubble-tag tag-warning';
      tag.innerHTML = '⚡ Advisory & Precaution';
      bubble.appendChild(tag);
    }

    // Text content
    if (data.text) {
      const p = document.createElement('p');
      p.textContent = data.text;
      bubble.appendChild(p);
    }

    // Guidance bullet points
    if (data.guidance && data.guidance.length > 0) {
      const ul = document.createElement('ul');
      ul.className = 'guidance-list';
      data.guidance.forEach(item => {
        const li = document.createElement('li');
        li.textContent = item;
        ul.appendChild(li);
      });
      bubble.appendChild(ul);
    }

    // Speech text assembly
    let speechText = '';
    if (data.text) speechText += data.text + '. ';
    if (data.guidance && data.guidance.length > 0) {
      speechText += data.guidance.join('. ');
    }

    // Timestamp & Speech Listen Button
    const timeSpan = document.createElement('span');
    timeSpan.className = 'message-timestamp';
    timeSpan.textContent = getFormattedTime();

    if ('speechSynthesis' in window && speechText.trim().length > 0) {
      const speakBtn = document.createElement('button');
      speakBtn.type = 'button';
      speakBtn.className = 'btn-speak';
      speakBtn.title = 'Listen to safety instructions';
      speakBtn.innerHTML = `
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
        <span>Listen</span>
      `;
      speakBtn.addEventListener('click', () => {
        speakSafetyGuidance(speechText, speakBtn);
      });
      timeSpan.appendChild(speakBtn);
    }

    content.appendChild(bubble);
    content.appendChild(timeSpan);
    row.appendChild(avatar);
    row.appendChild(content);

    chatMessages.appendChild(row);
    scrollChatToBottom();
  }

  function speakSafetyGuidance(text, btn) {
    if (!('speechSynthesis' in window)) return;
    if (window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
      if (btn) btn.classList.remove('speaking');
      return;
    }
    const cleanText = text.replace(/<[^>]*>/g, '');
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 0.95;
    if (btn) {
      btn.classList.add('speaking');
      utterance.onend = () => btn.classList.remove('speaking');
      utterance.onerror = () => btn.classList.remove('speaking');
    }
    window.speechSynthesis.speak(utterance);
  }

  function appendUserMessage(text) {
    const row = document.createElement('div');
    row.className = 'message-row user';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`;

    const content = document.createElement('div');
    content.className = 'message-content';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    const p = document.createElement('p');
    p.textContent = text;
    bubble.appendChild(p);

    const timeSpan = document.createElement('span');
    timeSpan.className = 'message-timestamp';
    timeSpan.textContent = getFormattedTime();

    content.appendChild(bubble);
    content.appendChild(timeSpan);
    row.appendChild(avatar);
    row.appendChild(content);

    chatMessages.appendChild(row);
    scrollChatToBottom();
  }

  function renderOptionButtons(options) {
    currentOptions = options || [];
    optionsGrid.innerHTML = '';

    if (!options || options.length === 0) {
      optionsInstruction.textContent = 'Assessment complete';
      return;
    }

    optionsInstruction.textContent = 'Choose an option below to proceed:';

    options.forEach(optText => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn-option-pill';
      btn.innerHTML = `<span>${optText}</span>`;
      btn.addEventListener('click', () => {
        handleUserChoice(optText);
      });
      optionsGrid.appendChild(btn);
    });
  }

  function renderRestartOptionButton() {
    optionsGrid.innerHTML = '';
    optionsInstruction.textContent = 'Assessment completed. You may restart at any time:';

    const restartBtn = document.createElement('button');
    restartBtn.type = 'button';
    restartBtn.className = 'btn-option-pill selected';
    restartBtn.innerHTML = `
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 0115-6.7L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 01-15 6.7L3 16"/><path d="M3 21v-5h5"/></svg>
      <span>Start New Assessment</span>
    `;
    restartBtn.addEventListener('click', () => {
      startNewAssessment();
    });
    optionsGrid.appendChild(restartBtn);
  }

  function disableActiveOptionButtons() {
    const btns = optionsGrid.querySelectorAll('.btn-option-pill');
    btns.forEach(b => {
      b.disabled = true;
    });
  }

  function showTyping(show) {
    if (typingIndicator) {
      typingIndicator.style.display = show ? 'flex' : 'none';
      if (show) scrollChatToBottom();
    }
  }

  function scrollChatToBottom() {
    setTimeout(() => {
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 40);
  }

  function getFormattedTime() {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  // =========================================================================
  // FINAL SAFETY SUMMARY RENDERING
  // =========================================================================
  function renderFinalSummaryCard(summary) {
    const card = document.createElement('div');
    card.className = 'final-summary-card';

    // Risk badge class
    let badgeClass = 'moderate';
    if (summary.risk_level === 'CRITICAL EMERGENCY') badgeClass = 'critical';
    else if (summary.risk_level === 'HIGH RISK') badgeClass = 'high';

    // Immediate Actions list
    let immediateActionsHtml = '';
    if (summary.immediate_actions && summary.immediate_actions.length > 0) {
      const items = summary.immediate_actions.map(act => `<li>${act}</li>`).join('');
      immediateActionsHtml = `
        <div>
          <div class="summary-section-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            Immediate Priority Safety Actions
          </div>
          <ul class="immediate-actions-list">
            ${items}
          </ul>
        </div>
      `;
    }

    // Personalized Checklist
    let checklistHtml = '';
    if (summary.checklist && summary.checklist.length > 0) {
      const items = summary.checklist.map(item => `<li>${item}</li>`).join('');
      checklistHtml = `
        <div>
          <div class="summary-section-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#16A34A" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
            Personalized Safety & Evacuation Checklist
          </div>
          <ul class="checklist-items">
            ${items}
          </ul>
        </div>
      `;
    }

    card.innerHTML = `
      <div class="summary-header-row">
        <div class="summary-title">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#0284C7" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          Personalized Flood Safety Plan
        </div>
        <span class="risk-badge ${badgeClass}">${summary.risk_level}</span>
      </div>

      ${immediateActionsHtml}
      ${checklistHtml}

      <div>
        <div class="summary-section-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0284C7" stroke-width="2.2"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z"/></svg>
          Emergency Rescue Contacts (India)
        </div>
        <div class="summary-contacts-grid">
          <div class="summary-contact-chip">
            <span class="summary-contact-num">112</span>
            <span class="summary-contact-label">National ERSS (All Emergencies)</span>
          </div>
          <div class="summary-contact-chip">
            <span class="summary-contact-num">1070</span>
            <span class="summary-contact-label">State Disaster Control (SEOC)</span>
          </div>
          <div class="summary-contact-chip">
            <span class="summary-contact-num">1077</span>
            <span class="summary-contact-label">District Control Room (DEOC)</span>
          </div>
        </div>
      </div>

      <div class="summary-disclaimer">
        ${summary.disclaimer}
      </div>
    `;

    chatMessages.appendChild(card);
    scrollChatToBottom();
  }

  // =========================================================================
  // ALTERNATIVE TEXT INPUT & SMART MATCHING
  // =========================================================================
  function initChatInput() {
    function submitFromInput() {
      const val = userTextInput.value.trim();
      if (!val) return;

      // Smart match against current options (case-insensitive fuzzy match)
      let matchedOption = val;
      const lower = val.toLowerCase();

      for (const opt of currentOptions) {
        const optLower = opt.toLowerCase();
        if (optLower === lower || optLower.startsWith(lower) || lower.includes(optLower)) {
          matchedOption = opt;
          break;
        }
      }

      userTextInput.value = '';
      handleUserChoice(matchedOption);
    }

    btnSendText.addEventListener('click', submitFromInput);
    userTextInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        submitFromInput();
      }
    });

    btnRestartChat.addEventListener('click', () => {
      if (confirm('Restart the FloodSafe assessment? All current progress will reset.')) {
        startNewAssessment();
      }
    });

    if (btnPrintChat) {
      btnPrintChat.addEventListener('click', () => {
        window.print();
      });
    }
  }

  // =========================================================================
  // MERMAID FLOWCHART & ZOOM CONTROLS
  // =========================================================================
  function initMermaid() {
    if (typeof mermaid !== 'undefined') {
      try {
        mermaid.initialize({
          startOnLoad: true,
          theme: 'default',
          securityLevel: 'loose',
          flowchart: {
            curve: 'basis',
            useMaxWidth: false,
            htmlLabels: true
          }
        });
      } catch (e) {
        console.warn('Mermaid initialization error:', e);
      }
    }
  }

  function renderFlowchart() {
    if (typeof mermaid !== 'undefined') {
      try {
        mermaid.contentLoaded();
      } catch (e) {
        console.log('Mermaid render trigger:', e);
      }
    }
  }

  function initFlowchartControls() {
    btnZoomIn.addEventListener('click', () => {
      state.zoom_level = Math.min(state.zoom_level + 0.15, 2.5);
      applyZoom();
    });

    btnZoomOut.addEventListener('click', () => {
      state.zoom_level = Math.max(state.zoom_level - 0.15, 0.4);
      applyZoom();
    });

    btnResetZoom.addEventListener('click', () => {
      state.zoom_level = 1.0;
      applyZoom();
    });

    function applyZoom() {
      if (mermaidDiagram) {
        mermaidDiagram.style.transform = `scale(${state.zoom_level})`;
      }
    }

    // Toggle source code view
    btnToggleSource.addEventListener('click', async () => {
      const isVisible = sourceCodePanel.style.display !== 'none';
      if (isVisible) {
        sourceCodePanel.style.display = 'none';
        btnToggleSource.textContent = 'View Source';
      } else {
        sourceCodePanel.style.display = 'block';
        btnToggleSource.textContent = 'Hide Source';
        if (!sourceCodeText.textContent) {
          try {
            const res = await fetch('/api/flowchart-data');
            const data = await res.json();
            sourceCodeText.textContent = data.mermaid || 'Unable to load flowchart source.';
          } catch (e) {
            sourceCodeText.textContent = 'Failed to fetch flowchart.mmd source.';
          }
        }
      }
    });

    btnCopyCode.addEventListener('click', () => {
      if (sourceCodeText.textContent) {
        navigator.clipboard.writeText(sourceCodeText.textContent).then(() => {
          btnCopyCode.textContent = 'Copied!';
          setTimeout(() => { btnCopyCode.textContent = 'Copy Source'; }, 2000);
        });
      }
    });
  }
});

