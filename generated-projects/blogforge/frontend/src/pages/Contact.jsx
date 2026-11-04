import React, { useState } from 'react';
import { Mail, MessageSquare, LifeBuoy, ArrowRight, AlertCircle } from 'lucide-react';

const SUPPORT_EMAIL = 'hello@blogforge.app';

export default function Contact() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [topic, setTopic] = useState('Product question');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const submit = (e) => {
    e.preventDefault();
    if (!name.trim() || !email.trim() || !message.trim()) {
      setError('Name, email and message are all required.');
      return;
    }
    if (message.trim().length < 10) {
      setError('Please add a little more detail (at least 10 characters).');
      return;
    }
    setError('');
    const subject = encodeURIComponent(`[BlogForge] ${topic}`);
    const body = encodeURIComponent(`Name: ${name}\nEmail: ${email}\n\n${message}`);
    window.location.href = `mailto:${SUPPORT_EMAIL}?subject=${subject}&body=${body}`;
  };

  return (
    <div className="pb-24">
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 lg:pt-20">
        <div className="grid lg:grid-cols-[0.9fr_1.1fr] gap-12">
          <div>
            <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold bg-brand-primary/10 text-brand-accent border border-brand-primary/30">
              <LifeBuoy className="w-3.5 h-3.5" /> Contact
            </span>
            <h1 className="mt-6 text-4xl sm:text-5xl font-extrabold tracking-tight text-white">Talk to us</h1>
            <p className="mt-5 text-slate-300 leading-relaxed">
              Questions about deploying BlogForge, connecting a provider or wiring payments? Send a
              message — we read every one.
            </p>

            <div className="mt-9 space-y-4">
              <div className="flex items-start gap-4 rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
                <Mail className="w-5 h-5 text-brand-accent mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-white">Email</p>
                  <a href={`mailto:${SUPPORT_EMAIL}`} className="text-sm text-slate-400 hover:text-white transition-colors">
                    {SUPPORT_EMAIL}
                  </a>
                  <p className="text-xs text-slate-500 mt-1">Replies within two business days.</p>
                </div>
              </div>
              <div className="flex items-start gap-4 rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
                <MessageSquare className="w-5 h-5 text-brand-accent mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-white">In-app questions</p>
                  <p className="text-sm text-slate-400">
                    Already have an account? Open the workspace and check the FAQ on the home page for
                    credits, exports and provider setup.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <form onSubmit={submit} className="rounded-3xl border border-slate-800 bg-slate-900/60 p-7 sm:p-8 space-y-4">
            {error && (
              <div role="alert" className="flex items-start gap-2 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-200 text-sm">
                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" /> {error}
              </div>
            )}
            <div className="grid sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label htmlFor="contact-name" className="text-xs font-semibold text-slate-400">Name</label>
                <input
                  id="contact-name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  autoComplete="name"
                  className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/30 outline-none transition-all duration-200"
                />
              </div>
              <div className="space-y-1.5">
                <label htmlFor="contact-email" className="text-xs font-semibold text-slate-400">Email</label>
                <input
                  id="contact-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/30 outline-none transition-all duration-200"
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <label htmlFor="contact-topic" className="text-xs font-semibold text-slate-400">Topic</label>
              <select
                id="contact-topic"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/30 outline-none transition-all duration-200"
              >
                {['Product question', 'Deployment help', 'AI provider setup', 'Payments', 'Something else'].map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5">
              <label htmlFor="contact-message" className="text-xs font-semibold text-slate-400">Message</label>
              <textarea
                id="contact-message"
                rows={6}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/30 outline-none transition-all duration-200 resize-y"
              />
            </div>
            <button
              type="submit"
              className="w-full inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl font-bold text-white bg-gradient-to-r from-brand-primary to-cyan-500 hover:opacity-95 transition-all duration-200"
            >
              Open in email app <ArrowRight className="w-4 h-4" />
            </button>
            <p className="text-xs text-slate-500 text-center">
              The form composes an email in your own mail client — no message is stored on our server.
            </p>
          </form>
        </div>
      </section>
    </div>
  );
}
