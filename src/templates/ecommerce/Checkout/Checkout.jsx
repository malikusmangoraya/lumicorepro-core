import { useState } from 'react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Button, Input, Progress } from '@/components/ui';
import { steps } from './data/mockData';

export default function Checkout() {
  const [step, setStep] = useState(0);
  return (
    <TemplateShell
      title="Checkout"
      description="Shipping, payment, and order review."
      category="E-Commerce"
    >
      <Progress
        value={((step + 1) / steps.length) * 100}
        className="mb-6"
        showLabel
        label={steps[step]}
      />
      <Card className="max-w-xl mx-auto space-y-4 animate-fade-in" key={step}>
        {step === 0 && (
          <>
            <Input label="Full name" placeholder="Alex Rivera" />
            <Input label="Address" placeholder="123 Main St" />
            <Input label="City" placeholder="Austin" />
          </>
        )}
        {step === 1 && (
          <>
            <Input label="Card number" placeholder="4242 4242 4242 4242" />
            <div className="grid grid-cols-2 gap-3">
              <Input label="Expiry" placeholder="12/28" />
              <Input label="CVC" placeholder="123" />
            </div>
          </>
        )}
        {step === 2 && (
          <div className="space-y-2 text-sm text-muted-foreground">
            <p>Review your shipping and payment details, then place the order.</p>
            <p className="text-foreground font-medium">Order total: $97.00</p>
          </div>
        )}
        {step === 3 && (
          <div className="text-center py-6 animate-scale-in">
            <p className="font-display text-2xl font-bold text-primary">Order placed</p>
            <p className="mt-2 text-muted-foreground">Confirmation sent to your email.</p>
          </div>
        )}
        <div className="flex justify-between pt-2">
          <Button variant="ghost" disabled={step === 0} onClick={() => setStep((s) => s - 1)}>
            Back
          </Button>
          {step < steps.length - 1 ? (
            <Button onClick={() => setStep((s) => s + 1)}>
              {step === 2 ? 'Place order' : 'Continue'}
            </Button>
          ) : (
            <Button variant="secondary">Done</Button>
          )}
        </div>
      </Card>
    </TemplateShell>
  );
}
