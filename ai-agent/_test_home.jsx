import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Home() {
  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      <main>
        <section className="relative overflow-hidden py-20 lg:py-28">
          <div className="absolute inset-0 -z-10" style={{ background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)' }} />
          <div className="max-w-6xl mx-auto px-6">
            <div className="max-w-2xl">
              <span className="section-eyebrow">FOOD DELIVERY</span>
              <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight leading-tight mb-6" style={{ color: '#1f2937' }}>
                Food Delivery & Restaurant Platform
              </h1>
              <p className="text-lg text-slate-500 leading-relaxed mb-8 max-w-lg">
                Complete food delivery solution: online ordering, restaurant management, and real-time dispatch.
              </p>
              <div className="flex flex-wrap gap-4">
                <Link to="/contact" className="btn-primary">Get Started <ArrowRight className="h-4 w-4" /></Link>
                <Link to="/services" className="btn-outline">View Services</Link>
              </div>
            </div>
          </div>
        </section>

        <section className="py-20 px-6 bg-white">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12">
              <span className="section-eyebrow">What We Offer</span>
              <h2 className="section-heading">Why Choose FoodExpress?</h2>
            </div>
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              <div className="group rounded-xl border border-slate-100 bg-white p-6 transition-all duration-300 hover:shadow-lg">
                <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg text-lg font-bold text-white" style={{ backgroundColor: '#dc2626' }}>
                  1
                </div>
                <h3 className="text-lg font-semibold mb-2" style={{ color: '#1f2937' }}>Online Ordering</h3>
                <p className="text-sm text-slate-500 leading-relaxed">Branded menus with photos, modifiers, and upsells</p>
              </div>
              <div className="group rounded-xl border border-slate-100 bg-white p-6 transition-all duration-300 hover:shadow-lg">
                <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg text-lg font-bold text-white" style={{ backgroundColor: '#dc2626' }}>
                  2
                </div>
                <h3 className="text-lg font-semibold mb-2" style={{ color: '#1f2937' }}>Live Tracking</h3>
                <p className="text-sm text-slate-500 leading-relaxed">Real-time GPS tracking from kitchen to doorstep</p>
              </div>
              <div className="group rounded-xl border border-slate-100 bg-white p-6 transition-all duration-300 hover:shadow-lg">
                <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg text-lg font-bold text-white" style={{ backgroundColor: '#dc2626' }}>
                  3
                </div>
                <h3 className="text-lg font-semibold mb-2" style={{ color: '#1f2937' }}>Restaurant Dashboard</h3>
                <p className="text-sm text-slate-500 leading-relaxed">Order management, analytics, and menu control</p>
              </div>
              <div className="group rounded-xl border border-slate-100 bg-white p-6 transition-all duration-300 hover:shadow-lg">
                <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg text-lg font-bold text-white" style={{ backgroundColor: '#dc2626' }}>
                  4
                </div>
                <h3 className="text-lg font-semibold mb-2" style={{ color: '#1f2937' }}>Dispatch Engine</h3>
                <p className="text-sm text-slate-500 leading-relaxed">Optimized rider assignment and route planning</p>
              </div>
            </div>
          </div>
        </section>

        <section className="py-16 px-6" style={{ backgroundColor: '#f8fafc' }}>
          <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="text-3xl sm:text-4xl font-extrabold mb-1" style={{ color: '#dc2626' }}>10K+</div>
              <div className="text-sm text-slate-500">Restaurants</div>
            </div>
            <div className="text-center">
              <div className="text-3xl sm:text-4xl font-extrabold mb-1" style={{ color: '#dc2626' }}>2M+</div>
              <div className="text-sm text-slate-500">Orders Delivered</div>
            </div>
            <div className="text-center">
              <div className="text-3xl sm:text-4xl font-extrabold mb-1" style={{ color: '#dc2626' }}>30 min</div>
              <div className="text-sm text-slate-500">Avg Delivery</div>
            </div>
            <div className="text-center">
              <div className="text-3xl sm:text-4xl font-extrabold mb-1" style={{ color: '#dc2626' }}>$95M</div>
              <div className="text-sm text-slate-500">GMV</div>
            </div>
          </div>
        </section>

        <section className="py-20 px-6">
          <div className="max-w-3xl mx-auto text-center rounded-2xl p-12" style={{ backgroundColor: '#1f2937' }}>
            <h2 className="text-3xl font-extrabold text-white mb-4">
              Ready to Transform Your Business?
            </h2>
            <p className="text-white/70 mb-8">
              Join thousands of professionals choosing FoodExpress as their growth platform.
            </p>
            <Link to="/contact" className="inline-flex items-center gap-2 rounded-lg bg-white px-8 py-3 font-semibold transition-all hover:shadow-xl" style={{ color: '#dc2626' }}>
              Start Free Trial <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
