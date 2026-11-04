// Allow-list HTML sanitizer based on DOMParser. Safe by construction: parsing
// into a detached document never executes scripts, and only a fixed set of
// tags/attributes survives, so LLM output can never smuggle markup into the
// preview or the downloaded HTML file.

const ALLOWED_TAGS = new Set([
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'br', 'hr',
  'ul', 'ol', 'li', 'strong', 'em', 'b', 'i', 'u', 's', 'code', 'pre',
  'blockquote', 'a', 'img', 'figure', 'figcaption',
  'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td', 'caption',
  'span', 'div', 'small', 'sub', 'sup', 'mark',
]);

const ALLOWED_ATTRS = new Set(['href', 'src', 'alt', 'title', 'colspan', 'rowspan', 'width', 'height']);

function isSafeUrl(value) {
  const v = String(value || '').trim();
  if (!v) return false;
  if (/^(https?:\/\/|mailto:)/i.test(v)) return true;
  if (v.startsWith('#') || v.startsWith('/')) return true;
  // Relative paths without a scheme are fine; anything with a scheme not
  // listed above (javascript:, data:, vbscript:, ...) is rejected.
  return !/^[a-z][a-z0-9+.-]*:/i.test(v);
}

function legacyStrip(html) {
  // No DOM available (old test envs): conservative regex fallback.
  return String(html || '')
    .replace(/<\s*script[\s\S]*?<\s*\/\s*script\s*>/gi, '')
    .replace(/<\s*\/*\s*(iframe|object|embed|form|style)[^>]*>/gi, '')
    .replace(/\son\w+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)/gi, '')
    .replace(/javascript:/gi, '');
}

export function sanitizeHtml(html) {
  const input = String(html || '');
  if (typeof window === 'undefined' || typeof window.DOMParser !== 'function') {
    return legacyStrip(input);
  }

  const doc = new window.DOMParser().parseFromString(input, 'text/html');
  const body = doc.body;
  if (!body) return legacyStrip(input);

  const process = (node) => {
    for (const child of Array.from(node.childNodes)) {
      if (child.nodeType === (window.Node ? window.Node.TEXT_NODE : 3)) continue;
      if (child.nodeType !== (window.Node ? window.Node.ELEMENT_NODE : 1)) {
        child.remove();
        continue;
      }
      const tag = child.tagName.toLowerCase();
      if (!ALLOWED_TAGS.has(tag)) {
        // Unknown but harmless containers get unwrapped; dangerous ones
        // (script, style, iframe, ...) are dropped with their contents.
        if (child.childNodes.length && !/^(script|style|iframe|object|embed|svg|math|form|link|meta)$/i.test(tag)) {
          const parent = node;
          const children = Array.from(child.childNodes);
          children.forEach((c) => parent.insertBefore(c, child));
        }
        child.remove();
        process(node);
        return;
      }
      for (const attr of Array.from(child.attributes || [])) {
        const name = attr.name.toLowerCase();
        if (name.startsWith('on') || !ALLOWED_ATTRS.has(name)) {
          child.removeAttribute(attr.name);
        }
      }
      if (child.hasAttribute('href') && !isSafeUrl(child.getAttribute('href'))) {
        child.removeAttribute('href');
      }
      if (child.hasAttribute('src') && !isSafeUrl(child.getAttribute('src'))) {
        child.removeAttribute('src');
      }
      process(child);
    }
  };

  process(body);
  return body.innerHTML;
}
