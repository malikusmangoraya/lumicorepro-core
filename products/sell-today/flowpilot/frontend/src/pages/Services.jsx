import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import {
  Code,
  Megaphone,
  BarChart3,
  Cloud,
  Lock,
  Headphones,
  ArrowRight,
  Check,
} from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import PricingTable from '../components/ecommerce/PricingTable';
import FAQAccordion from '../components/common/FAQAccordion';
import TestimonialGrid from '../components/common/TestimonialGrid';

const buildservices = (t) => [
  {
    icon: Code,
    title: t('Services.fullstack_engineering', 'Fullstack Engineering'),
    desc: t('Services.custom_enterprise_web_platforms_built_with_react_19_vite_and', 'Custom enterprise web platforms built with React 19, Vite, and high-performance backends.'),
    perks: [t('Services.react_19_architecture', 'React 19 Architecture'), 'Micro-interactions', t('Services.sub_second_loading', 'Sub-second Loading')],
  },
  {
    icon: Megaphone,
    title: t('Services.growth_marketing', 'Growth & Marketing'),
    desc: t('Services.comprehensive_seo_automation_conversion_optimization_and_ana', 'Comprehensive SEO automation, conversion optimization, and analytics tracking.'),
    perks: [t('Services.automated_meta_seo', 'Automated Meta SEO'), t('Services.opengraph_cards', 'OpenGraph Cards'), t('Services.conversion_funnels', 'Conversion Funnels')],
  },
  {
    icon: BarChart3,
    title: t('Services.data_analytics', 'Data Analytics'),
    desc: t('Services.actionable_real_time_intelligence_and_interactive_data_visua', 'Actionable real-time intelligence and interactive data visualization suites.'),
    perks: [t('Services.interactive_charts', 'Interactive Charts'), t('Services.custom_metrics', 'Custom Metrics'), t('Services.automated_reports', 'Automated Reports')],
  },
  {
    icon: Cloud,
    title: t('Services.cloud_infrastructure', 'Cloud Infrastructure'),
    desc: t('Services.zero_downtime_deployment_pipelines_with_edge_cdn_optimizatio', 'Zero-downtime deployment pipelines with edge CDN optimization and autoscaling.'),
    perks: [t('Services.global_cdn', 'Global CDN'), t('Services.automated_backups', 'Automated Backups'), '99.99% SLA'],
  },
  {
    icon: Lock,
    title: t('Services.security_compliance', 'Security & Compliance'),
    desc: t('Services.full_audits_including_gdpr_hipaa_soc2_readiness_and_encrypti', 'Full audits including GDPR, HIPAA, SOC2 readiness, and encryption hardening.'),
    perks: [t('Services.penetration_testing', 'Penetration Testing'), t('Services.jwt_rotation', 'JWT Rotation'), t('Services.access_control', 'Access Control')],
  },
  {
    icon: Headphones,
    title: '24/7 Dedicated Support',
    desc: t('Services.continuous_health_monitoring_proactive_patching_and_rapid_sl', 'Continuous health monitoring, proactive patching, and rapid SLA assistance.'),
    perks: [t('Services.live_telemetry', 'Live Telemetry'), t('Services.priority_response', 'Priority Response'), t('Services.scheduled_audits', 'Scheduled Audits')],
  },
];

export default function Services() {
  const { t } = useTranslation();

  const services = buildservices(t);
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main id="main-content" className="flex-1 px-6 py-16 max-w-6xl mx-auto w-full">
        <section className="text-center max-w-3xl mx-auto mb-16 space-y-4">
          <span className="text-xs font-semibold uppercase tracking-wider text-cyan-400">
            Capabilities
          </span>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">
            Tailored Solutions for Your Growth
          </h1>
          <p className="text-slate-400 text-base leading-relaxed">
            Every service is meticulously crafted to give your business an undeniable competitive
            edge in modern markets.
          </p>
        </section>

        <section className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 mb-16">
          {services.map((s) => (
            <div
              key={s.title}
              className="rounded-2xl border border-slate-800 bg-slate-900/40 p-7 flex flex-col justify-between hover:border-cyan-500/40 transition-all"
            >
              <div>
                <div className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400">
                  <s.icon className="h-5 w-5" />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-white">{s.title}</h3>
                <p className="mb-6 text-sm text-slate-400 leading-relaxed">{s.desc}</p>
                <ul className="space-y-2 mb-6 border-t border-slate-800/80 pt-4">
                  {s.perks.map((p) => (
                    <li key={p} className="flex items-center gap-2 text-xs text-slate-300">
                      <Check className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
                      <span>{p}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <Link
                to="/contact"
                className="inline-flex items-center gap-1 text-xs font-semibold text-cyan-400 hover:text-cyan-300"
              >
                Inquire Now <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          ))}
        </section>
      </main>

      <Footer />
    </div>
  );
}
