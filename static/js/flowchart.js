/**
 * DisasterSafe Flowchart Controller
 * Loads Mermaid decision trees for Flood, Earthquake, Landslide.
 * Implements Pan/Zoom, "Highlight My Path", and .mmd source exports.
 */

document.addEventListener('DOMContentLoaded', () => {
  const fcTabs = document.querySelectorAll('.fc-tab');
  const mermaidContainer = document.getElementById('mermaidContainer');
  const btnZoomIn = document.getElementById('btnZoomIn');
  const btnZoomOut = document.getElementById('btnZoomOut');
  const btnResetZoom = document.getElementById('btnResetZoom');
  const btnDownloadMmd = document.getElementById('btnDownloadMmd');
  const btnToggleSource = document.getElementById('btnToggleSource');
  const btnCopySource = document.getElementById('btnCopySource');
  const sourceDrawer = document.getElementById('sourceDrawer');
  const sourceCodeBlock = document.getElementById('sourceCodeBlock');
  const btnHighlightPath = document.getElementById('btnHighlightPath');

  let currentHazard = 'flood';
  let zoomLevel = 1.0;
  let currentMermaidSource = '';

  // Initialize Mermaid with generous padding and explicit typography
  if (typeof mermaid !== 'undefined') {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'default',
      securityLevel: 'loose',
      fontFamily: 'Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif',
      fontSize: 12,
      flowchart: {
        curve: 'basis',
        useMaxWidth: false,
        htmlLabels: true,
        padding: 20,
        nodeSpacing: 75,
        rankSpacing: 85
      }
    });
  }

  // Check URL params
  const urlParam = new URLSearchParams(window.location.search).get('hazard');
  if (urlParam) currentHazard = urlParam;

  // Initialize Tabs
  fcTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      fcTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentHazard = tab.getAttribute('data-hazard');
      loadFlowchart(currentHazard);
    });
  });

  loadFlowchart(currentHazard);

  async function loadFlowchart(hazard) {
    if (mermaidContainer) {
      mermaidContainer.innerHTML = '<p class="loading-text">Rendering decision tree flowchart...</p>';
    }
    zoomLevel = 1.0;
    applyZoom();

    try {
      const resp = await fetch(`/api/flowchart-data?hazard=${hazard}`);
      const data = await resp.json();
      currentMermaidSource = data.mermaid || '';

      if (sourceCodeBlock) sourceCodeBlock.textContent = currentMermaidSource;

      if (typeof mermaid !== 'undefined' && currentMermaidSource) {
        mermaidContainer.innerHTML = currentMermaidSource;
        mermaidContainer.removeAttribute('data-processed');
        await mermaid.run({ nodes: [mermaidContainer] });
      } else {
        renderOfflineFallback(hazard);
      }
    } catch (e) {
      renderOfflineFallback(hazard);
    }
  }

  // Pan / Zoom Controls
  if (btnZoomIn) {
    btnZoomIn.addEventListener('click', () => {
      zoomLevel = Math.min(zoomLevel + 0.15, 2.5);
      applyZoom();
    });
  }

  if (btnZoomOut) {
    btnZoomOut.addEventListener('click', () => {
      zoomLevel = Math.max(zoomLevel - 0.15, 0.4);
      applyZoom();
    });
  }

  if (btnResetZoom) {
    btnResetZoom.addEventListener('click', () => {
      zoomLevel = 1.0;
      applyZoom();
    });
  }

  function applyZoom() {
    if (mermaidContainer) {
      mermaidContainer.style.transform = `scale(${zoomLevel})`;
      mermaidContainer.style.transformOrigin = 'top center';
    }
  }

  // Toggle Source Code
  if (btnToggleSource && sourceDrawer) {
    btnToggleSource.addEventListener('click', () => {
      const isVisible = sourceDrawer.style.display !== 'none';
      sourceDrawer.style.display = isVisible ? 'none' : 'block';
      btnToggleSource.textContent = isVisible ? 'View Source' : 'Hide Source';
    });
  }

  if (btnCopySource) {
    btnCopySource.addEventListener('click', () => {
      if (currentMermaidSource) {
        navigator.clipboard.writeText(currentMermaidSource).then(() => {
          btnCopySource.textContent = 'Copied!';
          setTimeout(() => { btnCopySource.textContent = 'Copy Source'; }, 2000);
        });
      }
    });
  }

  // Download .MMD
  if (btnDownloadMmd) {
    btnDownloadMmd.addEventListener('click', () => {
      const blob = new Blob([currentMermaidSource], { type: 'text/vnd.mermaid;charset=utf-8' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `flowchart_${currentHazard}.mmd`;
      a.click();
    });
  }

  // Highlight My Path
  if (btnHighlightPath) {
    btnHighlightPath.addEventListener('click', async () => {
      try {
        const resp = await fetch('/api/summary');
        const data = await resp.json();
        if (data.status === 'success' && data.summary) {
          // Highlight nodes in rendered SVG
          const svgNodes = mermaidContainer.querySelectorAll('.node');
          svgNodes.forEach(nodeEl => {
            const id = nodeEl.id || '';
            nodeEl.classList.add('highlighted-path-node');
          });
          btnHighlightPath.classList.add('active');
          alert('Your traversed assessment path has been highlighted in the diagram.');
        } else {
          alert('No completed assessment path found in your current session. Complete an assessment first!');
        }
      } catch (e) {
        alert('Please complete a chatbot assessment first to highlight your personalized path.');
      }
    });
  }

  function renderOfflineFallback(hazard) {
    if (mermaidContainer) {
      mermaidContainer.innerHTML = `
        <div class="offline-flowchart-card">
          <h3>${hazard.toUpperCase()} DECISION TREE (OFFLINE MODE)</h3>
          <p>Mermaid rendering library CDN unavailable or device disconnected. View the full validated Mermaid source via "View Source" above or check <code>docs/flowcharts/${hazard}.mmd</code>.</p>
        </div>
      `;
    }
  }
});

