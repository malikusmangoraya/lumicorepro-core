import React from 'react';
import { ScrollText } from 'lucide-react';
import { cn } from '../../utils';

const LegalDisclaimer = ({
  title = 'Legal disclaimer',
  body = 'This website is provided \u201cas is\u201d without warranties of any kind. Information shown is for general purposes and does not constitute professional advice. Review the full Terms of Service and Privacy Policy for complete details.',
  showIcon = true,
  className = '',
}) => {
  return (
    <section className={cn('rounded-2xl border bg-muted/50 p-6', className)} aria-label={title}>
      <div className="flex gap-3">
        {showIcon && (
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <ScrollText className="h-4 w-4" aria-hidden="true" />
          </span>
        )}
        <div className="space-y-1.5">
          <h3 className="text-sm font-semibold text-foreground">{title}</h3>
          <p className="text-sm leading-relaxed text-muted-foreground">{body}</p>
        </div>
      </div>
    </section>
  );
};

export default LegalDisclaimer;
