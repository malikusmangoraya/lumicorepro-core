/**
 * useInspector — PostMessage bridge for iframe DOM inspection.
 *
 * Injects a highlight overlay + click handler into the preview iframe,
 * captures element metadata (component name, DOM path, source file),
 * and forwards selections to the parent app for AI-driven editing.
 */
import { useState, useEffect, useRef, useCallback } from 'react';

const INSPECTOR_SCRIPT = `
(function() {
  if (window.__LUMI_INSPECTOR__) return;
  window.__LUMI_INSPECTOR__ = true;

  let highlightEl = null;
  let selectedEl = null;
  let inspectMode = false;

  function getComponentName(el) {
    if (!el) return '';
    // React 18+ fiber
    const fiberKey = Object.keys(el).find(k => k.startsWith('__reactFiber$') || k.startsWith('__reactInternalInstance$'));
    if (fiberKey) {
      let fiber = el[fiberKey];
      let depth = 0;
      while (fiber && depth < 20) {
        if (fiber.type && typeof fiber.type === 'function') {
          return fiber.type.displayName || fiber.type.name || 'AnonymousComponent';
        }
        if (fiber.type && typeof fiber.type === 'string') {
          return fiber.type;
        }
        fiber = fiber.return;
        depth++;
      }
    }
    return el.tagName?.toLowerCase() || 'unknown';
  }

  function getDomPath(el) {
    const path = [];
    while (el && el !== document.body) {
      let selector = el.tagName?.toLowerCase() || '';
      if (el.id) selector += '#' + el.id;
      else if (el.className && typeof el.className === 'string') {
        const cls = el.className.split(' ').filter(c => c && !c.startsWith('tw-')).slice(0, 2).join('.');
        if (cls) selector += '.' + cls;
      }
      path.unshift(selector);
      el = el.parentElement;
    }
    return path.join(' > ');
  }

  function getSourceFile(el) {
    const fiberKey = Object.keys(el || {}).find(k => k.startsWith('__reactFiber$'));
    if (!fiberKey) return null;
    let fiber = el[fiberKey];
    let depth = 0;
    while (fiber && depth < 30) {
      if (fiber._debugSource) {
        const src = fiber._debugSource;
        return {
          fileName: src.fileName || '',
          lineNumber: src.lineNumber || 0,
          columnNumber: src.columnNumber || 0,
        };
      }
      fiber = fiber.return;
      depth++;
    }
    return null;
  }

  function showHighlight(el) {
    if (highlightEl) removeHighlight();
    const rect = el.getBoundingClientRect();
    highlightEl = document.createElement('div');
    highlightEl.style.cssText = [
      'position:fixed',
      'pointer-events:none',
      'z-index:2147483640',
      'border:2px solid #6366f1',
      'background:rgba(99,102,241,0.08)',
      'border-radius:4px',
      'transition:all 150ms ease',
    ].join(';');
    highlightEl.style.left = rect.left + 'px';
    highlightEl.style.top = rect.top + 'px';
    highlightEl.style.width = rect.width + 'px';
    highlightEl.style.height = rect.height + 'px';
    document.body.appendChild(highlightEl);

    // Label
    const label = document.createElement('div');
    label.style.cssText = [
      'position:fixed',
      'pointer-events:none',
      'z-index:2147483641',
      'background:#6366f1',
      'color:white',
      'padding:2px 6px',
      'border-radius:3px',
      'font-size:11px',
      'font-family:monospace',
      'white-space:nowrap',
    ].join(';');
    const name = getComponentName(el);
    label.textContent = name;
    label.style.left = rect.left + 'px';
    label.style.top = (rect.top - 20) + 'px';
    document.body.appendChild(label);
    highlightEl.__label = label;
  }

  function removeHighlight() {
    if (highlightEl) {
      highlightEl.__label?.remove();
      highlightEl.remove();
      highlightEl = null;
    }
  }

  document.addEventListener('mouseover', function(e) {
    if (!inspectMode) return;
    const el = e.target;
    if (el && el !== document.body && el !== document.documentElement) {
      showHighlight(el);
    }
  });

  document.addEventListener('mouseout', function() {
    if (!inspectMode) removeHighlight();
  });

  document.addEventListener('click', function(e) {
    if (!inspectMode) return;
    e.preventDefault();
    e.stopPropagation();
    const el = e.target;
    if (!el || el === document.body || el === document.documentElement) return;

    selectedEl = el;
    const component = getComponentName(el);
    const domPath = getDomPath(el);
    const source = getSourceFile(el);
    const rect = el.getBoundingClientRect();

    window.parent.postMessage({
      type: 'LUMI_ELEMENT_SELECTED',
      payload: {
        component,
        domPath,
        sourceFile: source?.fileName || null,
        sourceLine: source?.lineNumber || null,
        rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
        outerHTML: el.outerHTML?.slice(0, 500) || '',
        tag: el.tagName?.toLowerCase(),
        className: typeof el.className === 'string' ? el.className : '',
      }
    }, '*');
  }, true);

  window.addEventListener('message', function(e) {
    if (e.data?.type === 'LUMI_TOGGLE_INSPECT') {
      inspectMode = !inspectMode;
      if (!inspectMode) removeHighlight();
      window.parent.postMessage({ type: 'LUMI_INSPECT_MODE', payload: { active: inspectMode } }, '*');
    }
    if (e.data?.type === 'LUMI_STOP_INSPECT') {
      inspectMode = false;
      removeHighlight();
    }
  });
})();
`;

export default function useInspector(iframeRef) {
  const [inspectMode, setInspectMode] = useState(false);
  const [selectedElement, setSelectedElement] = useState(null);
  const [hoveredElement, setHoveredElement] = useState(null);

  const injectScript = useCallback(() => {
    const iframe = iframeRef?.current;
    if (!iframe?.contentWindow) return;
    try {
      iframe.contentWindow.postMessage({ type: 'LUMI_INJECT_SCRIPT', script: INSPECTOR_SCRIPT }, '*');
      // Also try direct injection
      const doc = iframe.contentDocument || iframe.contentWindow.document;
      if (doc && !doc.getElementById('__lumi_inspector__')) {
        const script = doc.createElement('script');
        script.id = '__lumi_inspector__';
        script.textContent = INSPECTOR_SCRIPT;
        doc.body.appendChild(script);
      }
    } catch {
      // Cross-origin — postMessage only
    }
  }, [iframeRef]);

  useEffect(() => {
    const handler = (e) => {
      const data = e.data;
      if (!data?.type) return;
      if (data.type === 'LUMI_ELEMENT_SELECTED') {
        setSelectedElement(data.payload);
      }
      if (data.type === 'LUMI_INSPECT_MODE') {
        setInspectMode(data.payload.active);
      }
    };
    window.addEventListener('message', handler);
    return () => window.removeEventListener('message', handler);
  }, []);

  useEffect(() => {
    if (inspectMode) {
      injectScript();
      const iframe = iframeRef?.current;
      iframe?.contentWindow?.postMessage({ type: 'LUMI_TOGGLE_INSPECT' }, '*');
    } else {
      const iframe = iframeRef?.current;
      iframe?.contentWindow?.postMessage({ type: 'LUMI_STOP_INSPECT' }, '*');
      setSelectedElement(null);
    }
  }, [inspectMode, injectScript, iframeRef]);

  const toggleInspect = useCallback(() => {
    setInspectMode((prev) => !prev);
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedElement(null);
  }, []);

  return {
    inspectMode,
    selectedElement,
    hoveredElement,
    toggleInspect,
    clearSelection,
    injectScript,
  };
}
