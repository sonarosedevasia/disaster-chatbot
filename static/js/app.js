/**
 * DisasterSafe Global Client Application Controller
 * Handles:
 * - Dark / Light theme persistence
 * - High-contrast accessibility mode
 * - Font size scaling
 * - Global language switcher
 * - Browser Geolocation SOS generation
 * - Offline detection & PWA Service Worker registration
 */

document.addEventListener('DOMContentLoaded', () => {
  // Theme Management
  const btnThemeToggle = document.getElementById('btnThemeToggle');
  const btnHighContrast = document.getElementById('btnHighContrast');
  const btnFontDec = document.getElementById('btnFontDec');
  const btnFontInc = document.getElementById('btnFontInc');
  const langSelector = document.getElementById('langSelector');
  const offlineNotice = document.getElementById('offlineNotice');
  const btnShareLocation = document.getElementById('btnShareLocation');
  const btnQuickSos = document.getElementById('btnQuickSos');
  const locationStatus = document.getElementById('locationStatus');
  const panelToggleHandle = document.getElementById('panelToggleHandle');
  const floatingPanel = document.getElementById('floatingEmergencyPanel');
  const btnMobileNav = document.getElementById('btnMobileNav');
  const navMenu = document.getElementById('navMenu');

  // Initialize Theme from localStorage
  const savedTheme = localStorage.getItem('ds_theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);

  const savedContrast = localStorage.getItem('ds_contrast') || 'normal';
  if (savedContrast === 'high') {
    document.documentElement.classList.add('high-contrast');
  }

  const savedFont = localStorage.getItem('ds_font_size') || '100';
  document.documentElement.style.fontSize = `${savedFont}%`;

  if (btnThemeToggle) {
    btnThemeToggle.addEventListener('click', () => {
      const curr = document.documentElement.getAttribute('data-theme');
      const next = curr === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('ds_theme', next);
    });
  }

  if (btnHighContrast) {
    btnHighContrast.addEventListener('click', () => {
      const isHigh = document.documentElement.classList.toggle('high-contrast');
      localStorage.setItem('ds_contrast', isHigh ? 'high' : 'normal');
    });
  }

  if (btnFontInc && btnFontDec) {
    btnFontInc.addEventListener('click', () => {
      let current = parseInt(localStorage.getItem('ds_font_size') || '100', 10);
      current = Math.min(current + 10, 140);
      document.documentElement.style.fontSize = `${current}%`;
      localStorage.setItem('ds_font_size', current);
    });

    btnFontDec.addEventListener('click', () => {
      let current = parseInt(localStorage.getItem('ds_font_size') || '100', 10);
      current = Math.max(current - 10, 85);
      document.documentElement.style.fontSize = `${current}%`;
      localStorage.setItem('ds_font_size', current);
    });
  }

  // Language Selector Sync
  if (langSelector) {
    const activeUrlLang = new URLSearchParams(window.location.search).get('lang');
    if (activeUrlLang) {
      localStorage.setItem('ds_lang', activeUrlLang);
    }
    const storedLang = activeUrlLang || localStorage.getItem('ds_lang') || 'en';
    langSelector.value = storedLang;

    langSelector.addEventListener('change', () => {
      const selected = langSelector.value;
      localStorage.setItem('ds_lang', selected);
      const url = new URL(window.location.href);
      url.searchParams.set('lang', selected);
      window.location.href = url.toString();
    });
  }

  // Mobile Navigation Menu Toggle
  if (btnMobileNav && navMenu) {
    btnMobileNav.addEventListener('click', () => {
      navMenu.classList.toggle('open');
    });
  }

  // Floating Emergency Panel Toggle
  if (panelToggleHandle && floatingPanel) {
    panelToggleHandle.addEventListener('click', () => {
      floatingPanel.classList.toggle('expanded');
    });
  }

  // Geolocation SOS Generator
  function triggerGeolocationSos() {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser. Please dial 112 directly.');
      return;
    }

    if (locationStatus) locationStatus.textContent = 'Acquiring high-accuracy GPS coordinates...';

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude.toFixed(6);
        const lon = pos.coords.longitude.toFixed(6);
        const accuracy = Math.round(pos.coords.accuracy);
        const mapsLink = `https://maps.google.com/?q=${lat},${lon}`;
        const sosMessage = encodeURIComponent(
          `EMERGENCY SOS: I need urgent disaster assistance! My GPS location: ${mapsLink} (Accuracy: ~${accuracy}m). Sent via DisasterSafe.`
        );

        if (locationStatus) {
          locationStatus.innerHTML = `
            <strong>GPS Acquired:</strong> ${lat}, ${lon} (&plusmn;${accuracy}m)<br/>
            <a href="https://wa.me/?text=${sosMessage}" target="_blank" class="sos-share-link">Share on WhatsApp &rarr;</a> | 
            <a href="sms:?body=${sosMessage}" class="sos-share-link">Send via SMS &rarr;</a>
          `;
        }

        // Direct WhatsApp trigger
        window.open(`https://wa.me/?text=${sosMessage}`, '_blank');
      },
      (err) => {
        if (locationStatus) {
          locationStatus.textContent = 'Unable to retrieve location. Please convey your nearest landmark when dialing 112.';
        }
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  }

  if (btnShareLocation) btnShareLocation.addEventListener('click', triggerGeolocationSos);
  if (btnQuickSos) btnQuickSos.addEventListener('click', triggerGeolocationSos);

  // Offline / Online Status Indicator
  function updateOnlineStatus() {
    if (offlineNotice) {
      offlineNotice.style.display = navigator.onLine ? 'none' : 'block';
    }
  }

  window.addEventListener('online', updateOnlineStatus);
  window.addEventListener('offline', updateOnlineStatus);
  updateOnlineStatus();

  // PWA Service Worker Registration
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js')
      .then((reg) => console.log('DisasterSafe ServiceWorker registered. Scope:', reg.scope))
      .catch((err) => console.warn('ServiceWorker registration error:', err));
  }
});

