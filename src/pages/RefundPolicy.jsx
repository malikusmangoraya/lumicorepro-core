import { useNavigate } from 'react-router-dom';
import { RefreshCcw, ShieldCheck, Clock, CreditCard, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { Badge, Button, Card } from '@/components/ui';
import PageSEO from '@/components/common/PageSEO';

const REFUND_STEPS = [
  'Log in and open Subject—your account billing section.',
  'Choose "Request Refund" next to the applicable order.',
  'Select a reason and submit — you will get an email confirmation.',
  'Approved refunds are returned to the original payment method within 5-10 business days (Stripe/PayPal) or 14 days (bank transfer where supported).',
];

const NON_REFUNDABLE = [
  'AI generation credits that have already been converted into completed website archives (download or deploy used).',
  'Domain registrations, hosting add-ons, or third-party subscription fees purchased via the platform.',
  'Past-due amounts, fee penalties, or taxes imposed by payment providers.',
  'Digital template license purchases after the download link has been accessed (except legal issues with the file).',
];

export default function RefundPolicyPage() {
  const navigate = useNavigate();

  return (
    <div className="max-w-4xl mx-auto py-12 px-4 space-y-8 animate-page-enter">
      <PageSEO
        title="Refund Policy — LumicorePro"
        description="LumicorePro 14-day refund policy for AI generation credits and unused subscription periods."
        noIndex
      />
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
          <RefreshCcw className="h-3.5 w-3.5" /> 14-Day Refund Window
        </Badge>
        <h1 className="font-display text-3xl sm:text-4xl font-bold tracking-tight">
          Refund Policy
        </h1>
        <p className="text-sm text-muted-foreground">
          Last updated: September 2026 · Applies to plans, credits, and template purchases
        </p>
      </header>

      <div className="prose prose-sm dark:prose-invert max-w-none space-y-6 text-foreground/90">
        <section className="space-y-3">
          <h2 className="text-xl font-bold font-display flex items-center gap-2">
            <Clock className="h-5 w-5 text-primary" /> 1. Our 14-Day Promise
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            If you are not satisfied within <strong>14 days</strong> of purchase, you may request a
            full refund for unused subscription periods and unused AI generation credit packs. This
            is a no-questions-asked window for new customers.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold font-display flex items-center gap-2">
            <CreditCard className="h-5 w-5 text-primary" /> 2. How to Request a Refund
          </h2>
          <ol className="list-decimal pl-5 space-y-2 text-sm text-muted-foreground">
            {REFUND_STEPS.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Alternatively, email <span className="font-mono text-xs text-primary">support@lumicorepro.com</span>{' '}
            with your order ID and reason. We respond within 2 business days.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold font-display">3. What Is Not Refundable</h2>
          <ul className="list-disc pl-5 space-y-1.5 text-sm text-muted-foreground">
            {NON_REFUNDABLE.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold font-display flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-primary" /> 4. Payment Disputes
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            We encourage you to contact us before opening a dispute with Stripe or PayPal — most
            issues are resolved faster by us directly. Refunds initiated through us are processed on
            the original payment method; PayPal balance refunds may appear within 24 hours.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
            <Card className="p-4 text-center">
              <CheckCircle2 className="h-5 w-5 text-emerald-400 mx-auto mb-1" />
              <p className="text-xs text-muted-foreground">5-10 business days (card)</p>
            </Card>
            <Card className="p-4 text-center">
              <CheckCircle2 className="h-5 w-5 text-emerald-400 mx-auto mb-1" />
              <p className="text-xs text-muted-foreground">~24 hours (PayPal balance)</p>
            </Card>
            <Card className="p-4 text-center">
              <CheckCircle2 className="h-5 w-5 text-emerald-400 mx-auto mb-1" />
              <p className="text-xs text-muted-foreground">Account credit (instant)</p>
            </Card>
          </div>
        </section>

        <section className="space-y-3 border-t border-border pt-6">
          <h2 className="text-xl font-bold font-display">5. Dispute & Contact</h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Questions about a charge or refund? Contact{' '}
            <span className="font-mono text-xs text-primary">support@lumicorepro.com</span>. We
            review every request fairly and in accordance with applicable consumer law.
          </p>
        </section>
      </div>
    </div>
  );
}