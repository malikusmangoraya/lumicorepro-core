/**
 * VisualCanvas — Click-to-Prompt visual editing interface.
 *
 * Wraps a preview iframe with:
 *  - DOM inspector overlay (hover highlight + click-to-select)
 *  - Element metadata display (component name, source file, DOM path)
 *  - Floating prompt modal for AI-driven editing of selected elements
 */
import { useState, useRef, useCallback } from 'react';
import { Crosshair, MousePointer2, Code2, FileText, Send, X } from 'lucide-react';
import { Card, Badge, Button, IconButton } from '@/components/ui';
import useInspector from '@/hooks/useInspector';
import { cn } from '@/utils';

export default function VisualCanvas({ previewUrl, onPromptSubmit, className }) {
  const iframeRef = useRef(null);
  const { inspectMode, selectedElement, toggleInspect, clearSelection } = useInspector(iframeRef);
  const [prompt, setPrompt] = useState('');

  const handleSubmit = useCallback(() => {
    if (!prompt.trim() || !selectedElement) return;
    onPromptSubmit?.({
      prompt: prompt.trim(),
      element: selectedElement,
    });
    setPrompt('');
  }, [prompt, selectedElement, onPromptSubmit]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit();
    }
    if (e.key === 'Escape') {
      clearSelection();
      setPrompt('');
    }
  }, [handleSubmit, clearSelection]);

  return (
    <div className={cn('relative flex flex-col overflow-hidden rounded-2xl border border-border/70', className)}>
      {/* Toolbar */}
      <div className="flex items-center justify-between border-b border-border/50 bg-card/80 px-4 py-2 backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-foreground">Visual Canvas</span>
          {inspectMode && (
            <Badge variant="success" className="gap-1">
              <Crosshair className="h-3 w-3" />
              Inspecting
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-1">
          <IconButton
            variant={inspectMode ? 'primary' : 'ghost'}
            size="sm"
            onClick={toggleInspect}
            title="Toggle element inspector"
          >
            <MousePointer2 className="h-4 w-4" />
          </IconButton>
        </div>
      </div>

      {/* Preview iframe */}
      <div className="relative flex-1 bg-background">
        {previewUrl ? (
          <iframe
            ref={iframeRef}
            src={previewUrl}
            title="Visual Canvas Preview"
            className="h-full w-full"
            sandbox="allow-same-origin allow-scripts allow-popups"
            loading="lazy"
            onLoad={() => {
              if (inspectMode) {
                setTimeout(() => {
                  const iframe = iframeRef?.current;
                  iframe?.contentWindow?.postMessage({ type: 'LUMI_TOGGLE_INSPECT' }, '*');
                }, 500);
              }
            }}
          />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
            Generate a project to see the live canvas
          </div>
        )}

        {/* Selected element info pill */}
        {selectedElement && (
          <div className="absolute left-3 top-3 z-20">
            <Card className="flex items-center gap-3 bg-card/95 px-3 py-2 backdrop-blur-sm">
              <Code2 className="h-4 w-4 text-primary" />
              <div className="min-w-0">
                <p className="truncate text-xs font-semibold text-foreground">
                  {selectedElement.component}
                </p>
                {selectedElement.sourceFile && (
                  <p className="flex items-center gap-1 truncate text-[10px] text-muted-foreground">
                    <FileText className="h-3 w-3 shrink-0" />
                    {selectedElement.sourceFile.split('/').pop()}
                    {selectedElement.sourceLine ? `:${selectedElement.sourceLine}` : ''}
                  </p>
                )}
              </div>
              <IconButton variant="ghost" size="sm" onClick={clearSelection}>
                <X className="h-3 w-3" />
              </IconButton>
            </Card>
          </div>
        )}
      </div>

      {/* Prompt bar — shown when element is selected */}
      {selectedElement && (
        <div className="border-t border-border/50 bg-card/90 px-4 py-3 backdrop-blur-sm">
          <p className="mb-2 text-[10px] font-semibold uppercase text-muted-foreground">
            Edit selected: {selectedElement.component}
            {selectedElement.sourceFile && (
              <span className="ml-2 normal-case">
                in {selectedElement.sourceFile.split('/').pop()}:{selectedElement.sourceLine}
              </span>
            )}
          </p>
          <div className="flex gap-2">
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="e.g. change the background to dark blue, make it bigger, add an animation..."
              className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/50"
              autoFocus
            />
            <Button
              onClick={handleSubmit}
              disabled={!prompt.trim()}
              leftIcon={Send}
              variant="primary"
              size="sm"
            >
              Send
            </Button>
          </div>
          <p className="mt-1.5 text-[10px] text-muted-foreground">
            Press <kbd className="rounded bg-muted px-1 py-0.5 text-foreground">Enter</kbd> or{' '}
            <kbd className="rounded bg-muted px-1 py-0.5 text-foreground">Ctrl+Enter</kbd> to submit
          </p>
        </div>
      )}
    </div>
  );
}
