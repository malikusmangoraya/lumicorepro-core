/**
 * Generate complete template files for all education categories.
 * Run: node scripts/generate-templates.js
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const root = path.resolve(__dirname, '..');

const templates = [
  {
    category: 'education',
    template: 'lms-template-01',
    name: 'EduLearn Pro',
    icon: 'BookOpen',
    tagline: 'Learn Without Limits',
    subtitle: 'Master New Skills',
    description: 'Join 50,000+ students learning from world-class instructors. Choose from 200+ courses designed to accelerate your career.',
    cta: 'Start Learning',
    sectionNames: ['Hero', 'Features', 'Courses', 'Instructors', 'Stats', 'Testimonials', 'Pricing', 'Contact', 'Footer', 'Navbar'],
    sections: ['hero', 'features', 'courses', 'instructors', 'stats', 'testimonials', 'pricing', 'contact'],
    accent: 'cyan',
    heroBg: 'from-indigo-950/90 via-slate-950 to-cyan-950/80',
    features: [
      { title: 'Expert Instructors', desc: 'Learn from industry leaders and academics with years of experience.' },
      { title: 'Lifetime Access', desc: 'Once enrolled, access your course materials forever.' },
      { title: 'Certificates', desc: 'Earn recognized certificates of completion for your resume.' },
    ],
    courses: [
      { title: 'Web Development Bootcamp', students: '12,450', level: 'Beginner', rating: '4.9', price: '$49' },
      { title: 'Data Science Fundamentals', students: '8,320', level: 'Intermediate', rating: '4.8', price: '$69' },
      { title: 'UI/UX Design Masterclass', students: '6,780', level: 'Beginner', rating: '4.9', price: '$59' },
      { title: 'Python for AI/ML', students: '11,200', level: 'Advanced', rating: '4.7', price: '$79' },
      { title: 'Mobile App Development', students: '5,640', level: 'Intermediate', rating: '4.8', price: '$59' },
      { title: 'Digital Marketing Pro', students: '9,870', level: 'Beginner', rating: '4.6', price: '$39' },
    ],
    instructors: [
      { name: 'Dr. Sarah Chen', role: 'Computer Science', students: '15,000+' },
      { name: 'James Rodriguez', role: 'Design Expert', students: '12,000+' },
      { name: 'Priya Sharma', role: 'Data Science', students: '18,000+' },
    ],
    stats: [
      { value: '200+', label: 'Courses' },
      { value: '50K+', label: 'Students' },
      { value: '120+', label: 'Instructors' },
      { value: '98%', label: 'Satisfaction' },
    ],
    testimonials: [
      { name: 'Alex Thompson', role: 'Software Engineer', text: 'This platform completely changed my career trajectory. The courses are well-structured and the instructors are world-class.' },
      { name: 'Maria Garcia', role: 'UX Designer', text: "I went from zero design knowledge to landing my dream job in just 6 months. The UI/UX masterclass is incredible." },
      { name: 'David Kim', role: 'Data Analyst', text: 'The Data Science track gave me practical skills that I use every day at work. Highly recommended!' },
    ],
    pricing: [
      { name: 'Starter', price: '$9', period: '/month', features: ['Access to 50 courses', 'Certificate of completion', 'Community forum', 'Email support'], popular: false },
      { name: 'Pro', price: '$29', period: '/month', features: ['Access to all courses', 'Certificate of completion', 'Community forum', 'Priority support', 'Offline downloads', '1-on-1 sessions'], popular: true },
      { name: 'Team', price: '$79', period: '/month', features: ['Everything in Pro', 'Team analytics', 'Admin dashboard', 'SSO integration', 'Custom learning paths', 'Dedicated manager'], popular: false },
    ],
  },
  {
    category: 'fitness',
    template: 'gym-template-01',
    name: 'FitZone Pro',
    icon: 'Dumbbell',
    tagline: 'Stronger Every Day',
    subtitle: 'Transform Your Body',
    description: 'Professional gym website with class schedules, trainer profiles, membership plans, and BMI calculator.',
    cta: 'Join Now',
    sectionNames: ['Hero', 'Features', 'Classes', 'Trainers', 'Stats', 'Testimonials', 'Pricing', 'Contact', 'Footer', 'Navbar'],
    sections: ['hero', 'features', 'classes', 'trainers', 'stats', 'testimonials', 'pricing', 'contact'],
    accent: 'orange',
    heroBg: 'from-red-950/90 via-slate-950 to-orange-950/80',
    features: [
      { title: 'Expert Trainers', desc: 'Certified professionals to guide your fitness journey.' },
      { title: 'Modern Equipment', desc: 'State-of-the-art machines and free weight areas.' },
      { title: 'Group Classes', desc: 'High-energy classes from yoga to HIIT.' },
    ],
    courses: [],
    instructors: [
      { name: 'Mike Johnson', role: 'Head Trainer', students: '500+ members' },
      { name: 'Lisa Park', role: 'Yoga Instructor', students: '300+ members' },
      { name: 'Carlos Rivera', role: 'HIIT Coach', students: '400+ members' },
    ],
    stats: [
      { value: '50+', label: 'Weekly Classes' },
      { value: '2K+', label: 'Members' },
      { value: '25+', label: 'Trainers' },
      { value: '15', label: 'Years' },
    ],
    testimonials: [
      { name: 'Tom Wilson', role: 'Member since 2022', text: 'Best gym in town! The trainers are knowledgeable and the atmosphere is motivating.' },
      { name: 'Rachel Adams', role: 'Member since 2023', text: "The group classes are amazing. I've lost 30 lbs and gained so much confidence." },
      { name: 'Steve Brown', role: 'Member since 2021', text: 'The facilities are top-notch and the membership is fair for what you get.' },
    ],
    pricing: [
      { name: 'Basic', price: '$29', period: '/month', features: ['Gym floor access', 'Locker room', 'Free WiFi', 'Fitness assessment'], popular: false },
      { name: 'Premium', price: '$59', period: '/month', features: ['All Basic features', 'Group classes', 'Sauna & steam', 'Personal trainer session', 'Nutrition coaching'], popular: true },
      { name: 'Elite', price: '$99', period: '/month', features: ['All Premium features', 'Unlimited PT sessions', 'Recovery suite', 'Guest passes', 'Priority booking'], popular: false },
    ],
  },
  {
    category: 'healthcare',
    template: 'medical-template-01',
    name: 'HealthCare+',
    icon: 'Heart',
    tagline: 'Caring for You',
    subtitle: 'Your Health, Our Priority',
    description: 'Leading healthcare provider with expert doctors, modern facilities, and compassionate care.',
    cta: 'Book Appointment',
    sectionNames: ['Hero', 'Features', 'Services', 'Doctors', 'Stats', 'Testimonials', 'About', 'Contact', 'Footer', 'Navbar'],
    sections: ['hero', 'features', 'services', 'doctors', 'stats', 'testimonials', 'about', 'contact'],
    accent: 'emerald',
    heroBg: 'from-emerald-950/90 via-slate-950 to-teal-950/80',
    features: [
      { title: 'Expert Doctors', desc: 'Board-certified physicians across all specialties.' },
      { title: 'Modern Facilities', desc: 'State-of-the-art equipment for accurate diagnosis.' },
      { title: '24/7 Emergency', desc: 'Round-the-clock emergency care when you need it.' },
    ],
    courses: [],
    instructors: [
      { name: 'Dr. Emily Watson', role: 'Cardiology', students: '2000+ patients' },
      { name: 'Dr. Robert Lee', role: 'Neurology', students: '1500+ patients' },
      { name: 'Dr. Susan Patel', role: 'Oncology', students: '1800+ patients' },
    ],
    stats: [
      { value: '50+', label: 'Specialists' },
      { value: '10K+', label: 'Patients' },
      { value: '25+', label: 'Departments' },
      { value: '98%', label: 'Satisfaction' },
    ],
    testimonials: [
      { name: 'John Mitchell', role: 'Patient', text: 'Outstanding care from start to finish. The medical team is caring and professional.' },
      { name: 'Jane Foster', role: 'Patient', text: 'I encountered no issues - the booking system works flawlessly.' },
      { name: 'Mark Davis', role: 'Patient', text: 'I found their schedule quite convenient - appointments are never hard to get.' },
    ],
    pricing: [],
  },
  {
    category: 'portfolio',
    template: 'personal-template-01',
    name: 'Creative Portfolio',
    icon: 'User',
    tagline: 'Design. Build. Inspire.',
    subtitle: 'Hello, I\'m a Creative Developer',
    description: 'Personal portfolio showcasing my design work, development projects, and creative vision.',
    cta: 'View My Work',
    sectionNames: ['Hero', 'About', 'Skills', 'Projects', 'Stats', 'Testimonials', 'Timeline', 'Contact', 'Footer', 'Navbar'],
    sections: ['hero', 'about', 'skills', 'projects', 'stats', 'testimonials', 'timeline', 'contact'],
    accent: 'violet',
    heroBg: 'from-violet-950/90 via-slate-950 to-purple-950/80',
    features: [
      { title: 'UI/UX Design', desc: 'Creating beautiful and intuitive digital experiences.' },
      { title: 'Web Development', desc: 'Building performant, modern web applications.' },
      { title: 'Brand Identity', desc: 'Crafting memorable brand experiences that resonate.' },
    ],
    courses: [],
    instructors: [],
    stats: [
      { value: '100+', label: 'Projects' },
      { value: '50+', label: 'Clients' },
      { value: '8+', label: 'Years' },
      { value: '99%', label: 'Happy Clients' },
    ],
    testimonials: [
      { name: 'Sarah Johnson', role: 'CEO, TechStart', text: 'Exceptional design skills and attention to detail. Highly recommended for any project.' },
      { name: 'Mike Chen', role: 'CTO, InnovateCo', text: "Delivered our project on time and exceeded all expectations." },
      { name: 'Lisa Wang', role: 'Founder, DesignHub', text: 'A rare talent who understands both design and technology.' },
    ],
    pricing: [],
  },
  {
    category: 'realestate',
    template: 'property-template-01',
    name: 'PropertyHub',
    icon: 'Home',
    tagline: 'Find Your Dream Home',
    subtitle: 'Premium Real Estate Listings',
    description: 'Discover premium properties in top locations. Expert agents ready to help you find the perfect home.',
    cta: 'Browse Properties',
    sectionNames: ['Hero', 'Features', 'Listings', 'Agents', 'Stats', 'Testimonials', 'About', 'Contact', 'Footer', 'Navbar'],
    sections: ['hero', 'features', 'listings', 'agents', 'stats', 'testimonials', 'about', 'contact'],
    accent: 'amber',
    heroBg: 'from-amber-950/90 via-slate-950 to-yellow-950/80',
    features: [
      { title: 'Verified Listings', desc: 'Every property is verified and quality-checked.' },
      { title: 'Expert Agents', desc: 'Professional agents to guide your property search.' },
      { title: 'Easy Financing', desc: 'Flexible mortgage options and financial guidance.' },
    ],
    courses: [],
    instructors: [
      { name: 'Mark Thompson', role: 'Senior Agent', students: '200+ sales' },
      { name: 'Jessica Brown', role: 'Luxury Specialist', students: '150+ sales' },
      { name: 'David Wilson', role: 'Commercial Expert', students: '180+ sales' },
    ],
    stats: [
      { value: '1K+', label: 'Properties' },
      { value: '500+', label: 'Happy Families' },
      { value: '30+', label: 'Agents' },
      { value: '15', label: 'Years' },
    ],
    testimonials: [
      { name: 'The Johnsons', role: 'Home Buyers', text: 'Found our dream home in just 2 weeks with PropertyHub\'s expert guidance.' },
      { name: 'Amanda Foster', role: 'First-time Buyer', text: 'The process was smooth and stress-free. Our agent was incredibly helpful.' },
      { name: 'Robert Kim', role: 'Property Investor', text: 'Best real estate platform I\'ve used. Great listings and professional service.' },
    ],
    pricing: [],
  },
  {
    category: 'restaurant',
    template: 'cafe-template-01',
    name: 'Savory Dining',
    icon: 'UtensilsCrossed',
    tagline: 'Taste the Difference',
    subtitle: 'Fine Dining Experience',
    description: 'Experience culinary excellence with fresh ingredients and creative flavors in an elegant setting.',
    cta: 'Reserve a Table',
    sectionNames: ['Hero', 'Features', 'Menu', 'Chefs', 'Stats', 'Testimonials', 'Gallery', 'Contact', 'Footer', 'Navbar'],
    sections: ['hero', 'features', 'menu', 'chefs', 'stats', 'testimonials', 'gallery', 'contact'],
    accent: 'rose',
    heroBg: 'from-rose-950/90 via-slate-950 to-red-950/80',
    features: [
      { title: 'Fresh Ingredients', desc: 'Locally sourced, seasonal ingredients for every dish.' },
      { title: 'Award Winning Chef', desc: 'Michelin-starred chef crafting unforgettable experiences.' },
      { title: 'Ambiance', desc: 'Elegant dining atmosphere for every occasion.' },
    ],
    courses: [],
    instructors: [
      { name: 'Chef Marco Rossi', role: 'Head Chef', students: 'Michelin Star' },
      { name: 'Chef Yuki Tanaka', role: 'Pastry Chef', students: '15 years exp' },
      { name: 'Chef Sophie Dupont', role: 'Sous Chef', students: '10 years exp' },
    ],
    stats: [
      { value: '50+', label: 'Dishes' },
      { value: '5K+', label: 'Happy Guests' },
      { value: '15', label: 'Years' },
      { value: '4.9', label: 'Rating' },
    ],
    testimonials: [
      { name: 'David & Emma', role: 'Anniversary Dinner', text: 'An incredible dining experience. Every dish was a masterpiece.' },
      { name: 'Maria Santos', role: 'Food Blogger', text: 'One of the best restaurants in the city. The tasting menu is to die for.' },
      { name: 'James Wright', role: 'Regular Customer', text: "The atmosphere is perfect for date nights. Quality is always consistent." },
    ],
    pricing: [],
  },
  {
    category: 'travel',
    template: 'agency-template-01',
    name: 'Wanderlust Travel',
    icon: 'Plane',
    tagline: 'Explore The World',
    subtitle: 'Your Journey Starts Here',
    description: 'Discover breathtaking destinations with expert travel planners and curated tour packages.',
    cta: 'Explore Destinations',
    sectionNames: ['Hero', 'Features', 'Destinations', 'Packages', 'Stats', 'Testimonials', 'About', 'Contact', 'Footer', 'Navbar'],
    sections: ['hero', 'features', 'destinations', 'packages', 'stats', 'testimonials', 'about', 'contact'],
    accent: 'sky',
    heroBg: 'from-sky-950/90 via-slate-950 to-blue-950/80',
    features: [
      { title: 'Curated Tours', desc: 'Hand-picked experiences by travel experts.' },
      { title: 'Best Prices', desc: 'Competitive pricing with no hidden fees.' },
      { title: '24/7 Support', desc: 'Assistance wherever you go in the world.' },
    ],
    courses: [],
    instructors: [
      { name: 'Anna Explorer', role: 'Travel Planner', students: '500+ trips' },
      { name: 'Tom Voyager', role: 'Adventure Guide', students: '300+ trips' },
      { name: 'Sophie Nomad', role: 'Luxury Specialist', students: '200+ trips' },
    ],
    stats: [
      { value: '100+', label: 'Destinations' },
      { value: '10K+', label: 'Happy Travelers' },
      { value: '200+', label: 'Tour Packages' },
      { value: '4.9', label: 'Rating' },
    ],
    testimonials: [
      { name: 'Family Smith', role: 'Bali Retreat', text: 'The best family vacation we\'ve ever had. Every detail was perfectly planned.' },
      { name: 'Chris & Karen', role: 'Europe Tour', text: 'An unforgettable trip. The local experiences were authentic and amazing.' },
      { name: 'Diana Lopez', role: 'Adventure Hiker', text: 'Challenging hikes, stunning views, and expert guides. Highly recommend!' },
    ],
    pricing: [],
  },
];

const componentJSX = {
  Navbar(config) {
    return `import React, { useState, useEffect } from 'react';
import { ${config.icon}, Menu, X } from 'lucide-react';

export const Navbar = () => {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav className={\`fixed top-0 left-0 right-0 z-50 transition-all duration-300 \${scrolled ? 'bg-white/95 backdrop-blur-md shadow-md py-3' : 'bg-transparent py-5'}\`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
        <a href="#" className="flex items-center gap-2 text-xl font-bold">
          <${config.icon} className="w-7 h-7 text-${config.accent}-500" />
          <span className="gradient-text">{config.name}</span>
        </a>
        <div className="hidden md:flex items-center space-x-8 text-sm font-semibold text-slate-700">
          ${config.sections.slice(0, 6).map(s => `<a href="#${s}" className="hover:text-${config.accent}-600 transition-colors">${s.charAt(0).toUpperCase() + s.slice(1)}</a>`).join('\n          ')}
        </div>
        <div className="hidden md:block">
          <a href="#${config.sections[0]}" className="bg-gradient-to-r from-${config.accent}-500 to-${config.accent}-700 hover:from-${config.accent}-600 hover:to-${config.accent}-800 text-white px-5 py-2.5 rounded-full font-semibold shadow-lg shadow-${config.accent}-500/20 transition-all duration-300 transform hover:scale-105">
            ${config.cta}
          </a>
        </div>
        <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)} className="md:hidden text-slate-700 focus:outline-none">
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>
      {mobileMenuOpen && (
        <div className="md:hidden bg-white border-b border-slate-100 px-4 pt-4 pb-6 space-y-4 shadow-xl">
          ${config.sections.map(s => `<a href="#${s}" onClick={() => setMobileMenuOpen(false)} className="block font-medium text-slate-700 hover:text-${config.accent}-600">${s.charAt(0).toUpperCase() + s.slice(1)}</a>`).join('\n          ')}
          <a href="#${config.sections[0]}" onClick={() => setMobileMenuOpen(false)} className="block text-center bg-${config.accent}-600 text-white py-2 rounded-lg font-semibold">${config.cta}</a>
        </div>
      )}
    </nav>
  );
};

export default Navbar;`;
  },

  Hero(config) {
    return `import React from 'react';
import { ${config.icon}, CheckCircle, ArrowRight } from 'lucide-react';

export const Hero = () => {
  return (
    <section id="hero" className="relative min-h-screen flex items-center justify-center overflow-hidden pt-20">
      <div className="absolute inset-0 bg-gradient-to-br ${config.heroBg}" />
      <div className="absolute inset-0 opacity-10" style={{ backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(255,255,255,0.1) 1px, transparent 0)', backgroundSize: '40px 40px' }} />
      <div className="relative max-w-5xl mx-auto px-4 text-center">
        <div className="inline-flex items-center gap-2 bg-${config.accent}-500/10 border border-${config.accent}-500/20 rounded-full px-4 py-2 text-${config.accent}-400 text-sm mb-6">
          <${config.icon} size={16} /> {config.tagline}
        </div>
        <h1 className="text-4xl sm:text-5xl lg:text-7xl font-extrabold mb-6 leading-tight">
          {config.subtitle}
          <span className="gradient-text block">{config.tagline}</span>
        </h1>
        <p className="text-lg text-slate-400 mb-10 max-w-2xl mx-auto">{config.description}</p>
        <div className="flex flex-wrap gap-4 justify-center mb-12">
          <a href="#${config.sections[2] || config.sections[1]}" className="bg-gradient-to-r from-${config.accent}-500 to-${config.accent}-700 text-white px-8 py-3.5 rounded-full font-semibold shadow-lg shadow-${config.accent}-500/30 hover:scale-105 transition-all text-lg">
            ${config.cta}
          </a>
          <button className="flex items-center gap-2 glass-panel px-8 py-3.5 rounded-full font-semibold text-slate-200 hover:border-${config.accent}-500/50 transition-all text-lg">
            Learn More <ArrowRight size={18} />
          </button>
        </div>
        ${config.features.length ? `'<span code}{config.features.slice(0, 4).map((f, i) => (
            <span key={i} className="flex items-center gap-2"><CheckCircle size={16} className="text-${config.accent}-400" /> {f.title}</span>
          ))}</span>'` : ''}
      </div>
    </section>
  );
};

export default Hero;`;
  },
};

// Since template generation is complex, let me use a different approach
// Create a generic section component for each section type
const genericComponents = {
  Features(config) {
    return `import React from 'react';
import { Star, Clock, Shield, Award, Zap, Users } from 'lucide-react';

const featureIcons = [Star, Clock, Shield, Award, Zap, Users];

export const Features = () => {
  const features = ${JSON.stringify(config.features, null, 2)};
  return (
    <section id="features" className="py-24 bg-slate-950">
      <div className="max-w-7xl mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            Why Choose <span className="gradient-text">{config.name}</span>
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto">Discover what makes us the preferred choice for {config.category === 'fitness' ? 'fitness' : config.category === 'healthcare' ? 'healthcare' : config.category === 'portfolio' ? 'creative projects' : config.category === 'realestate' ? 'property' : config.category === 'restaurant' ? 'dining' : config.category === 'travel' ? 'travel' : 'learning'}.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {features.map((f, i) => {
            const Icon = featureIcons[i % featureIcons.length];
            return (
              <div key={i} className="glass-card rounded-2xl p-8 text-center">
                <div className="w-14 h-14 rounded-xl bg-${config.accent}-500/10 flex items-center justify-center mx-auto mb-6">
                  <Icon className="w-7 h-7 text-${config.accent}-400" />
                </div>
                <h3 className="text-xl font-bold mb-3">{f.title}</h3>
                <p className="text-slate-400">{f.desc}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default Features;`;
  },

  Stats(config) {
    return `import React from 'react';

export const Stats = () => {
  const stats = ${JSON.stringify(config.stats, null, 2)};
  return (
    <section id="stats" className="py-20 bg-gradient-to-r from-${config.accent}-600 to-${config.accent}-700">
      <div className="max-w-7xl mx-auto px-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          {stats.map((s, i) => (
            <div key={i}>
              <div className="text-3xl sm:text-4xl font-extrabold text-white mb-2">{s.value}</div>
              <div className="text-${config.accent}-100 font-medium">{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Stats;`;
  },

  Testimonials(config) {
    return `import React from 'react';
import { Quote } from 'lucide-react';

const testimonials = ${JSON.stringify(config.testimonials, null, 2)};

export const Testimonials = () => {
  return (
    <section id="testimonials" className="py-24 bg-slate-950">
      <div className="max-w-7xl mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            What People <span className="gradient-text">Say</span>
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {testimonials.map((t, i) => (
            <div key={i} className="glass-card rounded-2xl p-8">
              <Quote className="w-8 h-8 text-${config.accent}-400 mb-4" />
              <p className="text-slate-300 mb-6 text-sm leading-relaxed">"{t.text}"</p>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-${config.accent}-500/20 flex items-center justify-center font-bold text-${config.accent}-400">
                  {t.name.charAt(0)}
                </div>
                <div>
                  <div className="font-semibold text-sm">{t.name}</div>
                  <div className="text-slate-500 text-xs">{t.role}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Testimonials;`;
  },

  Pricing(config) {
    const plans = config.pricing;
    if (!plans || !plans.length) {
      return `import React from 'react';
export const Pricing = () => null;
export default Pricing;`;
    }
    return `import React from 'react';
import { Check, Crown } from 'lucide-react';

const plans = ${JSON.stringify(plans, null, 2)};

export const Pricing = () => {
  return (
    <section id="pricing" className="py-24 bg-slate-950">
      <div className="max-w-7xl mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            Simple, <span className="gradient-text">Transparent</span> Pricing
          </h2>
          <p className="text-slate-400">Choose the plan that works best for you</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((p, i) => (
            <div key={i} className={\`rounded-2xl p-8 \${p.popular ? 'bg-gradient-to-b from-${config.accent}-500/20 to-slate-900 border-2 border-${config.accent}-500' : 'glass-card'}\`}>
              {p.popular && <div className="flex items-center gap-1 text-${config.accent}-400 text-sm font-semibold mb-4"><Crown size={14} /> Most Popular</div>}
              <h3 className="text-xl font-bold mb-2">{p.name}</h3>
              <div className="flex items-baseline gap-1 mb-6">
                <span className="text-4xl font-extrabold">{p.price}</span>
                <span className="text-slate-400">{p.period}</span>
              </div>
              <ul className="space-y-3 mb-8">
                {p.features.map((f, j) => (
                  <li key={j} className="flex items-center gap-2 text-sm text-slate-300">
                    <Check size={16} className="text-${config.accent}-400 flex-shrink-0" /> {f}
                  </li>
                ))}
              </ul>
              <a href="#contact" className={\`block text-center py-3 rounded-full font-semibold transition-all \${p.popular ? 'bg-gradient-to-r from-${config.accent}-500 to-${config.accent}-700 text-white' : 'bg-slate-800 text-slate-200 hover:bg-slate-700'}\`}>
                Get Started
              </a>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Pricing;`;
  },

  Contact(config) {
    return `import React from 'react';
import { Mail, MapPin, Phone } from 'lucide-react';

export const Contact = () => {
  return (
    <section id="contact" className="py-24 bg-slate-950">
      <div className="max-w-7xl mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            Get In <span className="gradient-text">Touch</span>
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto">Have questions? We'd love to hear from you. Reach out and we'll get back to you promptly.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
          <form className="space-y-6" onSubmit={(e) => e.preventDefault()}>
            <div className="grid grid-cols-2 gap-4">
              <input type="text" placeholder="Name" className="w-full px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-white placeholder:text-slate-500 focus:border-${config.accent}-500 focus:outline-none" />
              <input type="email" placeholder="Email" className="w-full px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-white placeholder:text-slate-500 focus:border-${config.accent}-500 focus:outline-none" />
            </div>
            <input type="text" placeholder="Subject" className="w-full px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-white placeholder:text-slate-500 focus:border-${config.accent}-500 focus:outline-none" />
            <textarea rows={5} placeholder="Message" className="w-full px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-white placeholder:text-slate-500 focus:border-${config.accent}-500 focus:outline-none resize-none" />
            <button type="submit" className="w-full bg-gradient-to-r from-${config.accent}-500 to-${config.accent}-700 text-white py-3.5 rounded-xl font-semibold hover:scale-[1.02] transition-all">Send Message</button>
          </form>
          <div className="space-y-8">
            {[
              { icon: MapPin, label: 'Address', value: '123 Main Street, Suite 100, City, Country' },
              { icon: Phone, label: 'Phone', value: '+1 (555) 123-4567' },
              { icon: Mail, label: 'Email', value: 'hello@${config.name.toLowerCase().replace(/\s+/g, '')}.com' },
            ].map((item, i) => (
              <div key={i} className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-${config.accent}-500/10 flex items-center justify-center flex-shrink-0">
                  <item.icon className="w-5 h-5 text-${config.accent}-400" />
                </div>
                <div>
                  <div className="font-semibold text-sm mb-1">{item.label}</div>
                  <div className="text-slate-400 text-sm">{item.value}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default Contact;`;
  },

  Footer(config) {
    return `import React from 'react';
import { ${config.icon} } from 'lucide-react';

export const Footer = () => {
  return (
    <footer className="bg-slate-950 border-t border-slate-800 py-12">
      <div className="max-w-7xl mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center gap-2 text-xl font-bold mb-4">
              <${config.icon} className="w-6 h-6 text-${config.accent}-500" />
              <span className="gradient-text">{config.name}</span>
            </div>
            <p className="text-slate-400 text-sm max-w-sm">{config.description.slice(0, 120)}...</p>
          </div>
          <div>
            <div className="font-semibold mb-4">Quick Links</div>
            <div className="space-y-2 text-sm text-slate-400">
              ${config.sections.slice(0, 4).map(s => `<a href="#${s}" className="block hover:text-${config.accent}-400 transition-colors">${s.charAt(0).toUpperCase() + s.slice(1)}</a>`).join('\n              ')}
            </div>
          </div>
          <div>
            <div className="font-semibold mb-4">Connect</div>
            <div className="space-y-2 text-sm text-slate-400">
              <a href="#" className="block hover:text-${config.accent}-400">Twitter</a>
              <a href="#" className="block hover:text-${config.accent}-400">LinkedIn</a>
              <a href="#" className="block hover:text-${config.accent}-400">Instagram</a>
            </div>
          </div>
        </div>
        <div className="border-t border-slate-800 pt-8 text-center text-sm text-slate-500">
          &copy; 2026 {config.name}. All rights reserved. Built with LumicorePro.
        </div>
      </div>
    </footer>
  );
};

export default Footer;`;
  },

  // Generic placeholder for category-specific sections (Courses/Classes/Listings etc.)
  CategorySection(config) {
    const sectionId = config.sections[2];
    const sectionLabel = sectionId.charAt(0).toUpperCase() + sectionId.slice(1);
    const items = config.courses.length ? config.courses : [
      { title: `${sectionLabel} Item 1`, students: 'N/A', level: 'Featured', rating: '4.9', price: 'Contact Us' },
      { title: `${sectionLabel} Item 2`, students: 'N/A', level: 'Popular', rating: '4.8', price: 'Contact Us' },
      { title: `${sectionLabel} Item 3`, students: 'N/A', level: 'New', rating: '4.7', price: 'Contact Us' },
    ];

    return `import React from 'react';
import { Star, Users } from 'lucide-react';

const items = ${JSON.stringify(items, null, 2)};

export const ${sectionId.charAt(0).toUpperCase() + sectionId.slice(1)} = () => {
  return (
    <section id="${sectionId}" className="py-24 bg-slate-950">
      <div className="max-w-7xl mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            Our <span className="gradient-text">${sectionLabel}</span>
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto">Explore our ${sectionId.toLowerCase()} offerings designed to deliver excellence.</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
          {items.map((item, i) => (
            <div key={i} className="glass-card rounded-2xl overflow-hidden group">
              <div className="h-48 bg-gradient-to-br from-${config.accent}-900/50 to-slate-800 flex items-center justify-center">
                <span className="text-5xl font-extrabold text-white/10">{i + 1}</span>
              </div>
              <div className="p-6">
                <div className="flex items-center gap-2 mb-3">
                  <span className="px-2 py-1 rounded-full text-xs font-medium bg-${config.accent}-500/10 text-${config.accent}-400">{item.level}</span>
                  <div className="flex items-center gap-1 text-amber-400 text-xs">
                    <Star size={12} fill="currentColor" /> {item.rating}
                  </div>
                </div>
                <h3 className="text-lg font-bold mb-2 group-hover:text-${config.accent}-400 transition-colors">{item.title}</h3>
                <div className="flex items-center justify-between text-sm text-slate-400">
                  <span className="flex items-center gap-1"><Users size={14} /> {item.students}</span>
                  <span className="text-${config.accent}-400 font-bold">{item.price}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default ${sectionId.charAt(0).toUpperCase() + sectionId.slice(1)};`;
  },

  Instructors(config) {
    const persons = config.instructors;
    const sectionId = config.sections[3] || 'people';
    const component = sectionId.replace(/(Trainer|Agent|Chef|Doctor)/, '');
    const SectionName = sectionId.charAt(0).toUpperCase() + sectionId.slice(1);
    if (!persons.length) {
      return `import React from 'react';\nexport const ${SectionName} = () => null;\nexport default ${SectionName};`;
    }
    return `import React from 'react';

const people = ${JSON.stringify(persons, null, 2)};

export const ${SectionName} = () => {
  return (
    <section id="${sectionId}" className="py-24 bg-slate-950">
      <div className="max-w-7xl mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            Meet Our <span className="gradient-text">${SectionName}</span>
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto">Talented professionals dedicated to delivering the best experience.</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
          {people.map((p, i) => (
            <div key={i} className="glass-card rounded-2xl p-8 text-center group">
              <div className="w-24 h-24 rounded-full bg-gradient-to-br from-${config.accent}-500 to-${config.accent}-700 flex items-center justify-center mx-auto mb-6 text-2xl font-bold text-white group-hover:scale-110 transition-transform">
                {p.name.charAt(0)}
              </div>
              <h3 className="text-lg font-bold mb-1">{p.name}</h3>
              <p className="text-${config.accent}-400 text-sm mb-3">{p.role}</p>
              <p className="text-slate-500 text-xs">{p.students}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default ${SectionName};`;
  },
};

// Write function
function write(path, content) {
  fs.mkdirSync(path.substring(0, path.lastIndexOf('/')), { recursive: true });
  fs.writeFileSync(path, content, 'utf-8');
  console.log(`  ✓ ${path.replace(root, '.').replace(/\\/g, '/')}`);
}

// eslint-disable-next-line no-unused-vars
function writeJ(path, content) {
  fs.mkdirSync(path.substring(0, path.lastIndexOf('/')), { recursive: true });
  fs.writeFileSync(path, content, 'utf-8');
  console.log(`  ✓ ${path.replace(root, '.').replace(/\\/g, '/')}`);
}

console.log('\n🚀 Generating template files...\n');

// Process each template
for (const config of templates) {
  console.log(`� ${config.category}/${config.template}:`);
  const base = path.join(root, 'src/templates', config.category, config.template, 'src');
  const compDir = path.join(base, 'components');

  // 1. main.jsx
  write(path.join(base, 'main.jsx'), `import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
`);

  // 2. index.css
  write(path.join(base, 'index.css'), `@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-slate-950 text-slate-100 font-sans antialiased selection:bg-${config.accent}-500 selection:text-slate-950;
  }
}

@layer utilities {
  .glass-panel {
    @apply bg-slate-900/70 backdrop-blur-md border border-slate-800 shadow-xl;
  }
  .glass-card {
    @apply bg-slate-900/60 backdrop-blur border border-slate-800/80 hover:border-${config.accent}-500/50 transition-all duration-300;
  }
  .gradient-text {
    @apply bg-gradient-to-r from-${config.accent}-400 via-blue-500 to-violet-500 bg-clip-text text-transparent;
  }
}

::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #090d16; }
::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #06b6d4; }
`);

  // 3. App.jsx
  const sectionImports = config.sections.map(s => {
    const name = s.charAt(0).toUpperCase() + s.slice(1);
    return `import ${name} from './components/${name}';`;
  }).join('\n');

  const sectionComponents = config.sections.map(s => {
    const name = s.charAt(0).toUpperCase() + s.slice(1);
    return `<${name} />`;
  }).join('\n        ');

  write(path.join(base, 'App.jsx'), `import React from 'react';
${sectionImports}

export function App() {
  return (
    <div className="min-h-screen bg-slate-950 font-sans text-slate-100 antialiased selection:bg-${config.accent}-500 selection:text-white">
      <Navbar />
      <main>
        ${sectionComponents}
      </main>
      <Footer />
    </div>
  );
}

export default App;
`);

  // 4. Generate components
  // Navbar
  write(path.join(compDir, 'Navbar.jsx'), componentJSX.Navbar(config));

  // Hero
  write(path.join(compDir, 'Hero.jsx'), `import React from 'react';
import { ${config.icon}, CheckCircle, ArrowRight } from 'lucide-react';

const Hero = () => {
  return (
    <section id="hero" className="relative min-h-screen flex items-center justify-center overflow-hidden pt-20">
      <div className="absolute inset-0 bg-gradient-to-br ${config.heroBg}" />
      <div className="absolute inset-0 opacity-10" style={{ backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(255,255,255,0.1) 1px, transparent 0)', backgroundSize: '40px 40px' }} />
      <div className="relative max-w-5xl mx-auto px-4 text-center">
        <div className="inline-flex items-center gap-2 bg-${config.accent}-500/10 border border-${config.accent}-500/20 rounded-full px-4 py-2 text-${config.accent}-400 text-sm mb-6">
          <${config.icon} size={16} /> {config.tagline}
        </div>
        <h1 className="text-4xl sm:text-5xl lg:text-7xl font-extrabold mb-6 leading-tight">
          {config.subtitle}
          <span className="gradient-text block">{config.tagline}</span>
        </h1>
        <p className="text-lg text-slate-400 mb-10 max-w-2xl mx-auto">{config.description}</p>
        <div className="flex flex-wrap gap-4 justify-center mb-12">
          <a href="#${config.sections[2] || config.sections[1]}" className="bg-gradient-to-r from-${config.accent}-500 to-${config.accent}-700 text-white px-8 py-3.5 rounded-full font-semibold shadow-lg shadow-${config.accent}-500/30 hover:scale-105 transition-all text-lg">
            ${config.cta}
          </a>
          <button className="flex items-center gap-2 glass-panel px-8 py-3.5 rounded-full font-semibold text-slate-200 hover:border-${config.accent}-500/50 transition-all text-lg">
            Learn More <ArrowRight size={18} />
          </button>
        </div>
        ${config.features.slice(0, 4).map(f => `<span className="flex items-center gap-2"><CheckCircle size={16} className="text-${config.accent}-400" /> ${f.title}</span>`).join('\n        ')}
      </div>
    </section>
  );
};

export default Hero;
`);

  // Features
  write(path.join(compDir, 'Features.jsx'), genericComponents.Features(config));

  // Category-specific section (Courses/Classes/Listings/Menu/Destinations/Skills)
  const catSectionId = config.sections[2];
  const catSectionName = catSectionId.charAt(0).toUpperCase() + catSectionId.slice(1);
  write(path.join(compDir, `${catSectionName}.jsx`), genericComponents.CategorySection(config));

  // People section (Instructors/Trainers/Doctors/Agents/Chefs)
  const peopleSectionId = config.sections[3];
  const peopleSectionName = peopleSectionId.charAt(0).toUpperCase() + peopleSectionId.slice(1);
  if (config.instructors.length) {
    write(path.join(compDir, `${peopleSectionName}.jsx`), genericComponents.Instructors(config));
  } else {
    write(path.join(compDir, `${peopleSectionName}.jsx`), `import React from 'react';\nconst ${peopleSectionName} = () => null;\nexport default ${peopleSectionName};`);
  }

  // Stats
  write(path.join(compDir, 'Stats.jsx'), genericComponents.Stats(config));

  // Testimonials
  write(path.join(compDir, 'Testimonials.jsx'), genericComponents.Testimonials(config));

  // Pricing (or About/Timeline/Gallery as needed)
  const pricingSectionId = config.sections[5];
  if (pricingSectionId === 'pricing') {
    write(path.join(compDir, 'Pricing.jsx'), genericComponents.Pricing(config));
  } else {
    // Generic section for the remaining slot
    const pName = pricingSectionId.charAt(0).toUpperCase() + pricingSectionId.slice(1);
    write(path.join(compDir, `${pName}.jsx`), `import React from 'react';\n\nconst ${pName} = () => (\n  <section id="${pricingSectionId}" className="py-24 bg-slate-950">\n    <div className="max-w-7xl mx-auto px-4 text-center">\n      <h2 className="text-3xl sm:text-4xl font-bold mb-6">${pName}</h2>\n      <p className="text-slate-400 max-w-xl mx-auto">${config.name} offers comprehensive ${pricingSectionId.toLowerCase()} to meet your needs.</p>\n    </div>\n  </section>\n);\nexport default ${pName};`);
  }

  // Contact
  write(path.join(compDir, 'Contact.jsx'), genericComponents.Contact(config));

  // Footer
  write(path.join(compDir, 'Footer.jsx'), genericComponents.Footer(config));

  // Update package.json with proper dependencies
  const pkgPath = path.join(root, 'src/templates', config.category, config.template, 'package.json');
  const existingPkg = fs.existsSync(pkgPath) ? JSON.parse(fs.readFileSync(pkgPath, 'utf-8')) : {};
  const newPkg = {
    name: config.template,
    private: true,
    version: "1.0.0",
    type: "module",
    scripts: {
      "dev": "vite",
      "build": "vite build",
      "preview": "vite preview"
    },
    dependencies: {
      "react": "^18.2.0",
      "react-dom": "^18.2.0",
      "lucide-react": "^0.344.0",
      "react-router-dom": "^6.22.0"
    },
    devDependencies: {
      "@vitejs/plugin-react": "^4.2.1",
      "autoprefixer": "^10.4.18",
      "postcss": "^8.4.35",
      "tailwindcss": "^3.4.1",
      "vite": "^5.1.4"
    }
  };
  writeJ(pkgPath, JSON.stringify(newPkg, null, 2) + '\n');

  // Create vite.config.js
  write(path.join(root, 'src/templates', config.category, config.template, 'vite.config.js'), `import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
});
`);

  // Create tailwind.config.js
  write(path.join(root, 'src/templates', config.category, config.template, 'tailwind.config.js'), `/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: { extend: {} },
  plugins: [],
};
`);

  // Create postcss.config.js
  write(path.join(root, 'src/templates', config.category, config.template, 'postcss.config.js'), `export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
`);

  // Create index.html
  write(path.join(root, 'src/templates', config.category, config.template, 'index.html'), `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>${config.name}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
`);

  console.log('');
}

console.log('✅ All templates generated successfully!\n');