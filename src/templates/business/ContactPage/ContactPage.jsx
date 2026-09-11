import TemplateShell from '../../_shared/TemplateShell';
import { Card } from '@/components/ui';
import { ContactForm } from '@/components/common';
import { Mail, MapPin, Phone } from 'lucide-react';
import { info } from './data/mockData';

export default function ContactPage() {
  return (
    <TemplateShell
      title="Contact"
      description="Validated inquiry form and contact info."
      category="Business"
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="space-y-4" animate="fade-up">
          <div className="flex gap-3 text-sm">
            <Mail className="h-4 w-4 text-primary" />
            {info.email}
          </div>
          <div className="flex gap-3 text-sm">
            <Phone className="h-4 w-4 text-primary" />
            {info.phone}
          </div>
          <div className="flex gap-3 text-sm">
            <MapPin className="h-4 w-4 text-primary" />
            {info.address}
          </div>
        </Card>
        <Card className="lg:col-span-2" animate="fade-up" animationDelay={80}>
          <ContactForm />
        </Card>
      </div>
    </TemplateShell>
  );
}
