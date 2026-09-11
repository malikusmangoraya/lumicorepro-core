import { useState, useEffect, useRef, useCallback } from 'react';
import { Terminal as TerminalIcon, Play, Square, ChevronRight, ChevronDown, Loader2 } from 'lucide-react';
import { Card, Badge, Button, IconButton } from '@/components/ui';
import { cn } from '@/utils';
import { loadProjectToSandbox, stopSandbox } from '@/services/sandbox';

export default function SandboxPreview({ runId, onClose }) {
  const [status, setStatus] = useState('idle');
  const [sandboxUrl, setSandboxUrl] = useState('');
  const [terminalLines, setTerminalLines] = useState([]);
  const [files, setFiles] = useState([]);
  const [expandedDirs, setExpandedDirs] = useState(new Set(['src']));
  const [selectedFile, setSelectedFile] = useState(null);
  const terminalRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!runId) return;
    setStatus('loading');
    setTerminalLines([]);

    loadProjectToSandbox(runId, {
      onTerminal: (line) => {
        setTerminalLines((prev) => [...prev.slice(-300), line]);
      },
      onReady: (info) => {
        setStatus('running');
        setSandboxUrl(info.container?.url || info.url || '');
      },
      onError: (err) => {
        setStatus('error');
        setTerminalLines((prev) => [...prev, `\x1b[31m${err}\x1b[0m`]);
      },
    });

    return () => {
      stopSandbox();
    };
  }, [runId]);

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [terminalLines]);

  const toggleDir = useCallback((dir) => {
    setExpandedDirs((prev) => {
      const next = new Set(prev);
      if (next.has(dir)) next.delete(dir);
      else next.add(dir);
      return next;
    });
  }, []);

  return (
    <Card className="flex h-[600px] flex-col overflow-hidden border-border/70">
      {/* Toolbar */}
      <div className="flex items-center justify-between border-b border-border/50 bg-card/50 px-4 py-2">
        <div className="flex items-center gap-2">
          <TerminalIcon className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium">Live Sandbox</span>
          <Badge variant={status === 'running' ? 'success' : status === 'error' ? 'danger' : 'secondary'}>
            {status}
          </Badge>
        </div>
        <div className="flex items-center gap-1">
          {status === 'running' && sandboxUrl && (
            <a
              href={sandboxUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg bg-primary/10 px-3 py-1 text-xs font-medium text-primary hover:bg-primary/20"
            >
              Open in new tab
            </a>
          )}
          <Button variant="ghost" size="sm" onClick={onClose}>
            <Square className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* File Tree */}
        <div className="w-48 shrink-0 overflow-y-auto border-r border-border/50 bg-background/50 p-2">
          <p className="mb-1.5 text-[10px] font-semibold uppercase text-muted-foreground">Files</p>
          <FileTree files={files} expandedDirs={expandedDirs} onToggleDir={toggleDir} onSelectFile={setSelectedFile} />
        </div>

        {/* Main area: Terminal + Preview */}
        <div className="flex flex-1 flex-col overflow-hidden">
          {/* Preview iframe */}
          {sandboxUrl && (
            <div className="relative h-1/2 border-b border-border/50">
              <iframe
                src={sandboxUrl}
                title="Sandbox preview"
                className="h-full w-full bg-background"
                sandbox="allow-same-origin allow-scripts allow-popups"
                loading="lazy"
              />
            </div>
          )}

          {/* Terminal */}
          <div
            ref={terminalRef}
            className={cn(
              'flex-1 overflow-y-auto bg-black/80 p-3 font-mono text-xs',
              !sandboxUrl && 'h-full'
            )}
          >
            {status === 'loading' && (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                <span>Installing dependencies &amp; starting dev server...</span>
              </div>
            )}
            {terminalLines.map((line, i) => (
              <div key={i} className="whitespace-pre-wrap break-all text-emerald-400/80">
                {line}
              </div>
            ))}
            {status === 'running' && (
              <div className="mt-1 flex items-center gap-1 text-primary">
                <ChevronRight className="h-3 w-3" />
                <span className="animate-pulse">_</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}

function FileTree({ files, expandedDirs, onToggleDir, onSelectFile }) {
  if (!files || files.length === 0) {
    return <p className="text-[10px] text-muted-foreground">No files loaded</p>;
  }

  return (
    <div className="space-y-0.5">
      {files.map((f) => {
        if (f.type === 'directory') {
          const isExpanded = expandedDirs.has(f.path);
          return (
            <button
              key={f.path}
              type="button"
              onClick={() => onToggleDir(f.path)}
              className="flex w-full items-center gap-1 rounded px-1 py-0.5 text-left text-xs text-foreground hover:bg-primary/10"
            >
              {isExpanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
              {f.path.split('/').pop()}
            </button>
          );
        }
        const depth = f.path.split('/').length - 1;
        const parentDir = f.path.split('/').slice(0, -1).join('/');
        if (depth > 0 && !expandedDirs.has(parentDir)) return null;
        return (
          <button
            key={f.path}
            type="button"
            onClick={() => onSelectFile?.(f)}
            className="flex w-full items-center gap-1 rounded px-1 py-0.5 text-left text-xs text-muted-foreground hover:bg-primary/10 hover:text-foreground"
            style={{ paddingLeft: `${depth * 12 + 4}px` }}
          >
            {f.path.split('/').pop()}
          </button>
        );
      })}
    </div>
  );
}
