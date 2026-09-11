import { useNavigate } from 'react-router-dom';
import { Scale, ArrowLeft } from 'lucide-react';
import { Badge, Button } from '@/components/ui';

export default function TermsOfServicePage() {
  const navigate = useNavigate();

  return (
    <div className="max-w-4xl mx-auto py-12 px-4 space-y-8 animate-page-enter">
      <Button
        variant="ghost"
        size="sm"
        leftIcon={ArrowLeft}
        onClick={() => navigate('/')}
        className="-ml-2 px-2 text-muted-foreground hover:text-foreground"
      >
        Back to Home
      </Button>

      <header className="border-b border-border pb-6 space-y-3">
        <Badge variant="default" size="sm">
          <Scale className="h-3.5 w-3.5" /> International Standard Terms
        </Badge>
        <h1 className="font-display text-3xl sm:text-4xl font-bold tracking-tight">
          Terms of Service
        </h1>
        <p className="text-sm text-muted-foreground">
          Last updated: September 2026 · Governing global use of the LumiCorePro software and AI
          agent platform
        </p>
      </header>

      <div className="prose prose-sm dark:prose-invert max-w-none space-y-6 text-foreground/90">
        <section className="space-y-3">
          <h2 className="text-xl font-bold font-display">1. Acceptance of Terms</h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            By accessing or using the LumiCorePro platform, website generator, and backend API
            services, you agree to be bound by these Terms of Service. If you do not agree, you must
            not use our software or generation services.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold font-display">
            2. Intellectual Property & Code Ownership
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            <strong>Your Generated Projects:</strong> You own 100% of the customized code, markup,
            and assets generated specifically for your project upon full payment or under your
            subscription tier. You are granted an irrevocable, royalty-free, perpetual license to
            run, modify, distribute, deploy, and commercialize the generated software.
          </p>
          <p className="text-sm text-muted-foreground leading-relaxed">
            <strong>Platform IP:</strong> The core LumiCorePro platform, orchestrator agents, brand
            assets, proprietary templates, and algorithms remain the exclusive property of
            LumiCorePro Inc.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold font-display">3. Acceptable Use Policy</h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            You agree not to use LumiCorePro to:
          </p>
          <ul className="list-disc pl-5 space-y-1 text-sm text-muted-foreground">
            <li>Generate malicious software, malware, phishing sites, or exploits.</li>
            <li>Infringe upon copyrights, trademarks, or third-party intellectual property.</li>
            <li>Conduct denial-of-service attacks or deliberately degrade API performance.</li>
            <li>Violate international sanctions, export control regulations, or privacy laws.</li>
          </ul>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold font-display">4. Service Availability & SLA</h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            LumiCorePro aims for 99.9% uptime for core API endpoints. Local-first generation allows
            offline assembly of 28 templates even when remote AI models or external cloud providers
            experience downtime.
          </p>
        </section>

        <section className="space-y-3 border-t border-border pt-6">
          <h2 className="text-xl font-bold font-display">5. Limitation of Liability</h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            In no event shall LumiCorePro be liable for indirect, incidental, or consequential
            damages resulting from the deployment or commercial operation of generated code. Users
            are encouraged to run the built-in 6 enterprise quality gates prior to production
            deployment.
          </p>
        </section>
      </div>
    </div>
  );
}
