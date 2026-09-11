import { useNavigate } from 'react-router-dom';
import { Shield, Lock, Eye, FileText, CheckCircle2, ArrowLeft } from 'lucide-react';
import { Badge, Button, Card } from '@/components/ui';

const USE_CASES = [
  {
    title: 'Service Provision',
    desc: 'To generate, build, test, and deliver custom website archives and source code.',
  },
  {
    title: 'Security & Integrity',
    desc: 'To prevent fraud, automated abuse, injection attacks, and protect user accounts.',
  },
  {
    title: 'Platform Analytics',
    desc: 'To benchmark performance, optimize token usage, and enhance local template quality.',
  },
  {
    title: 'International Compliance',
    desc: 'To respect localized tax calculation, currency display, and cookie consent preferences.',
  },
];

const USER_RIGHTS = [
  'Right of access to personal data',
  'Right to rectification of inaccurate data',
  'Right to erasure ("Right to be Forgotten")',
  'Right to data portability (export source code/account data)',
  'Right to restrict or object to processing',
  'Right to withdraw consent at any time',
];

export default function PrivacyPolicyPage() {
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
          <Shield className="h-3.5 w-3.5" /> GDPR & CCPA Compliant
        </Badge>
        <h1 className="font-display text-3xl sm:text-4xl font-bold tracking-tight">
          Privacy Policy
        </h1>
        <p className="text-sm text-muted-foreground">
          Last updated: September 2026 · Effective globally across North America, Europe,
          Asia-Pacific & Middle East
        </p>
      </header>

      <div className="prose prose-sm dark:prose-invert max-w-none space-y-6 text-foreground/90">
        <section className="space-y-3">
          <h2 className="text-xl font-bold font-display flex items-center gap-2">
            <Lock className="h-5 w-5 text-primary" /> 1. Information We Collect
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            LumiCorePro ("we", "our", or "us") adheres to international data protection principles
            including the General Data Protection Regulation (GDPR - EU 2016/679) and the California
            Consumer Privacy Act (CCPA). We collect the following categories of information:
          </p>
          <ul className="list-disc pl-5 space-y-1.5 text-sm text-muted-foreground">
            <li>
              <strong>Account Information:</strong> Name, email address, password hash, and
              organization details when registering.
            </li>
            <li>
              <strong>AI Generation Inputs:</strong> Natural language prompts, selected features,
              target industry, and configuration preferences provided to generate websites.
            </li>
            <li>
              <strong>Technical & Usage Data:</strong> IP address, browser type, device information,
              operating system, and session telemetry.
            </li>
            <li>
              <strong>Payment Information:</strong> Processed directly and securely via Stripe /
              PayPal with PCI-DSS Level 1 certification. We do not store raw credit card numbers.
            </li>
          </ul>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold font-display flex items-center gap-2">
            <Eye className="h-5 w-5 text-primary" /> 2. How We Use Your Data
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Your data is processed strictly under lawful bases (Article 6 GDPR):
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
            {USE_CASES.map((item, i) => (
              <Card key={i} className="p-4">
                <h4 className="font-semibold text-sm mb-1">{item.title}</h4>
                <p className="text-xs text-muted-foreground">{item.desc}</p>
              </Card>
            ))}
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold font-display flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" /> 3. International Rights (GDPR & CCPA)
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Regardless of your geographic location, LumiCorePro provides full user rights:
          </p>
          <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
            {USER_RIGHTS.map((right, i) => (
              <li
                key={i}
                className="flex items-center gap-2 p-2.5 rounded-lg border border-border/60 bg-background/50"
              >
                <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                <span>{right}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold font-display">4. Cookie Policy & Tracking</h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            We use essential cookies to maintain your login session and language preference. You can
            manage or revoke marketing and analytical cookies anytime using our interactive Cookie
            Consent banner.
          </p>
        </section>

        <section className="space-y-3 border-t border-border pt-6">
          <h2 className="text-xl font-bold font-display">
            5. Contact Our Data Protection Officer (DPO)
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            If you have questions regarding this Privacy Policy or wish to exercise your data
            rights, contact us at:
            <br />
            <span className="font-mono text-xs text-primary">privacy@lumicorepro.com</span>
          </p>
        </section>
      </div>
    </div>
  );
}
