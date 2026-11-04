import React, { useState } from 'react';
import { Check, Copy, Download, FileCode2 } from 'lucide-react';
import { sanitizeHtml } from './sanitize';

/** One-click copy / .md download / HTML export for a generated article. */
export default function ExportButtons({ markdown, title, onToast }) {
  const [copied, setCopied] = useState(false);

  const slug = String(title || 'article').toLowerCase().replace(/[^\w\s-]/g, '').replace(/\s+/g, '-').slice(0, 50) || 'article';
  const asHtml = () => {
    const md = sanitizeHtml(markdown);
    return [
      '<!DOCTYPE html>', '<html lang="en">', '<head>',
      '<meta charset="utf-8">', '<meta name="viewport" content="width=device-width, initial-scale=1">',
      (title ? `<title>${String(title).replace(/[<>&]/g, (c) => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;' }[c]))}</title>` : ''),
      '<style>body{max-width:44rem;margin:2.5rem auto;padding:0 1.25rem;font:16px/1.75 system-ui,sans-serif;color:#1e293b}h1,h2,h3{line-height:1.25;color:#0f172a}pre{background:#f1f5f9;padding:1rem;border-radius:8px;overflow:auto}img{max-width:100%}</style>',
      '</head><body>', md, '</body></html>', '',
    ].join('\n');
  };

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(markdown || '');
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      onToast?.('Copied to clipboard');
    } catch {
      onToast?.('Clipboard blocked by browser', 'error');
    }
  };

  const download = (content, filename, mime) => {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    onToast?.(`Downloaded ${filename}`);
  };

  return (
    <div className="flex flex-wrap gap-2" data-testid="gen-export">
      <button
        type="button"
        onClick={copy}
        className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold bg-slate-800/70 border border-slate-700 hover:border-indigo-400/60 hover:scale-[1.02] transition-all duration-200"
      >
        {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />} Copy Markdown
      </button>
      <button
        type="button"
        onClick={() => download(markdown || '', `${slug}.md`, 'text/markdown')}
        className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold bg-slate-800/70 border border-slate-700 hover:border-indigo-400/60 hover:scale-[1.02] transition-all duration-200"
      >
        <Download className="w-4 h-4" /> Download .md
      </button>
      <button
        type="button"
        onClick={() => download(asHtml(), `${slug}.html`, 'text/html')}
        className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold bg-slate-800/70 border border-slate-700 hover:border-indigo-400/60 hover:scale-[1.02] transition-all duration-200"
      >
        <FileCode2 className="w-4 h-4" /> Export HTML
      </button>
    </div>
  );
}
