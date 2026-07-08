import React, { Suspense, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { Cloud, Server, Database, Shield, Zap, TrendingDown, Target, BrainCircuit, Activity, Lock, CheckCircle2, ArrowRight, BarChart3, GitBranch, Bell } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { AnimatedHeading } from '../components/ui/AnimatedHeading';
import { FadeIn } from '../components/ui/FadeIn';

const GlobalCanvas = React.lazy(() =>
  import('../components/3d/GlobalCanvas').then(m => ({ default: m.GlobalCanvas }))
);

// ─── Animated counter ────────────────────────────────────────────────────────
function AnimatedNumber({ to, suffix = '' }: { to: number; suffix?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    const start = 0;
    const end = to;
    const duration = 1800;
    const step = (timestamp: number, startTime: number) => {
      const progress = Math.min((timestamp - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      if (ref.current) ref.current.textContent = Math.round(eased * end) + suffix;
      if (progress < 1) requestAnimationFrame(ts => step(ts, startTime));
    };

    const observer = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) {
        requestAnimationFrame(ts => step(ts, ts));
        observer.disconnect();
      }
    });
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [to, suffix]);

  return <span ref={ref}>0{suffix}</span>;
}

// ─── Section wrapper with fade-up animation ───────────────────────────────────
function FadeSection({ children, className = '', delay = 0 }: { children: React.ReactNode; className?: string; delay?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      entries => {
        entries.forEach(e => {
          if (e.isIntersecting) {
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
            observer.disconnect();
          }
        });
      },
      { threshold: 0.1 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      className={className}
      style={{
        opacity: 0,
        transform: 'translateY(32px)',
        transition: `opacity 0.75s cubic-bezier(0.22,1,0.36,1) ${delay}ms, transform 0.75s cubic-bezier(0.22,1,0.36,1) ${delay}ms`,
      }}
    >
      {children}
    </div>
  );
}

export default function Landing() {
  return (
    <main className="relative min-h-screen overflow-x-hidden font-sans selection:bg-blue-300/40">

      {/* ════════════════════════════════════════════════════════════
          GLOBAL 3D CANVAS — fixed behind entire page
      ════════════════════════════════════════════════════════════ */}
      <Suspense fallback={null}>
        <GlobalCanvas />
      </Suspense>

      {/* FULLSCREEN VIDEO BACKGROUND */}
      <div className="fixed inset-0 z-0 overflow-hidden h-screen pointer-events-none">
        <video 
          autoPlay 
          loop 
          muted 
          playsInline
          className="absolute inset-0 w-full h-full object-cover"
        >
          <source src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260403_050628_c4e32401-fab4-4a27-b7a8-6e9291cd5959.mp4" type="video/mp4" />
        </video>
      </div>

      {/* ════════════════════════════════════════════════════════════
          SCROLLABLE CONTENT — sits above the canvas
      ════════════════════════════════════════════════════════════ */}
      <div className="relative z-10">

        {/* ── NAVIGATION ─────────────────────────────────────────── */}
        <header className="fixed top-0 left-0 right-0 z-50 px-6 md:px-12 lg:px-16 pt-6">
          <nav className="liquid-glass rounded-xl px-4 py-2 flex items-center justify-between">
            {/* Left */}
            <div className="text-2xl font-semibold tracking-tight text-[#FAFAFA] flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/30">
                <Cloud size={16} className="text-[#FAFAFA]" />
              </div>
              Cloud Wise
            </div>
            
            {/* Center */}
            <div className="hidden md:flex items-center gap-8 text-sm text-[#FAFAFA]">
              <a href="#overview" className="hover:text-gray-300 transition-colors">Overview</a>
              <a href="#features" className="hover:text-gray-300 transition-colors">Features</a>
              <a href="#security" className="hover:text-gray-300 transition-colors">Security</a>
              <a href="#pricing" className="hover:text-gray-300 transition-colors">Pricing</a>
            </div>

            {/* Right */}
            <div className="flex items-center">
              <Link to="/login">
                <button className="bg-[#FAFAFA] text-slate-900 px-6 py-2 rounded-lg text-sm font-medium hover:bg-gray-100 transition-colors">
                  Sign In
                </button>
              </Link>
            </div>
          </nav>
        </header>

        {/* ── HERO CONTENT ── */}
        <section className="relative z-20 min-h-screen flex flex-col justify-center px-6 md:px-12 lg:px-16 pb-20 pt-32">
          <div className="lg:grid lg:grid-cols-2 lg:items-center w-full max-w-7xl mx-auto">
            
            {/* Left Column */}
              <div className="mb-8 lg:mb-0">
                <AnimatedHeading 
                  text={`Optimize cloud\ninfrastructure costs.`}
                  className="text-4xl md:text-5xl lg:text-6xl xl:text-7xl font-normal mb-4 text-[#FAFAFA]"
                />
                
                <FadeIn delay={800} duration={1000}>
                  <p className="text-base md:text-lg text-gray-300 mb-5 max-w-xl">
                    Monitor spending, identify waste, and automate optimization using AI-powered analytics.
                  </p>
                </FadeIn>

                <FadeIn delay={1200} duration={1000} className="flex flex-wrap gap-4">
                  <Link to="/register">
                    <button className="bg-[#FAFAFA] text-slate-900 px-8 py-3 rounded-lg font-medium hover:bg-gray-100 transition-colors">
                      Start Optimizing
                    </button>
                  </Link>
                  <Link to="/login">
                    <button className="liquid-glass border border-[#FAFAFA]/20 text-[#FAFAFA] px-8 py-3 rounded-lg font-medium hover:bg-[#FAFAFA] hover:text-slate-900 transition-colors duration-300">
                      View Dashboard
                    </button>
                  </Link>
                </FadeIn>
              </div>

              {/* Right Column */}
              <div className="flex items-end justify-start lg:justify-end">
                <FadeIn delay={1400} duration={1000}>
                  <div className="liquid-glass border border-white/20 px-6 py-3 rounded-xl">
                    <span className="text-lg md:text-xl lg:text-2xl font-light text-white">
                      Monitor. Optimize. Automate.
                    </span>
                  </div>
                </FadeIn>
              </div>

            </div>
        </section>

        {/* ── SECTIONS WRAPPER ── */}
        <div className="relative z-20 flex flex-col">

        {/* ── CLOUD PROVIDERS STRIP ───────────────────────────────── */}
        <section className="py-10 bg-slate-900/80 border-y border-slate-700/50 backdrop-blur-md">
          <div className="max-w-7xl mx-auto px-4 md:px-8 text-center">
            <p className="text-xs font-bold text-white uppercase tracking-widest mb-7">
              Seamless integration with major providers
            </p>
            <div className="flex flex-wrap justify-center gap-10 md:gap-20">
              {[
                { icon: Cloud, label: 'AWS' },
                { icon: Server, label: 'Azure' },
                { icon: Database, label: 'Google Cloud' },
                { icon: GitBranch, label: 'Kubernetes' },
              ].map(({ icon: Icon, label }) => (
                <div key={label} className="flex items-center gap-2.5 text-xl font-bold text-slate-300 hover:text-slate-200 transition-colors duration-300">
                  <Icon size={22} />
                  {label}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── PRODUCT OVERVIEW ────────────────────────────────────── */}
        <section id="overview" className="py-28 px-4 md:px-8 lg:px-16">
          <div className="max-w-7xl mx-auto">
            <FadeSection className="text-center max-w-3xl mx-auto mb-20">
              <p className="text-xs font-bold text-blue-600 uppercase tracking-widest mb-4">Platform Overview</p>
              <h2 className="text-3xl md:text-5xl font-bold text-white mb-6 leading-tight">
                Stop guessing your cloud spend
              </h2>
              <p className="text-xl text-slate-200 leading-relaxed">
                CloudWise connects to your infrastructure in minutes, ingesting millions of data points
                to build a comprehensive map of your resource utilization and cost efficiency.
              </p>
            </FadeSection>

            {/* Dashboard preview card */}
            <FadeSection delay={100}>
              <div className="landing-card p-8 md:p-10 max-w-5xl mx-auto">
                {/* Fake dashboard header */}
                <div className="flex items-center justify-between mb-8">
                  <div>
                    <div className="h-3 w-28 bg-slate-200 rounded-full mb-2" />
                    <div className="h-2 w-16 bg-slate-100 rounded-full" />
                  </div>
                  <div className="flex gap-2">
                    {['bg-blue-100', 'bg-cyan-100', 'bg-emerald-100'].map((c, i) => (
                      <div key={i} className={`h-8 w-20 ${c} rounded-lg border border-white/80`} />
                    ))}
                  </div>
                </div>

                {/* Metric cards row */}
                <div className="grid grid-cols-3 gap-4 mb-8">
                  {[
                    { label: 'Monthly Spend', value: '$84,320', delta: '-12%', color: 'text-emerald-600', bg: 'bg-emerald-50' },
                    { label: 'Idle Resources', value: '34', delta: '-8 this week', color: 'text-blue-600', bg: 'bg-blue-50' },
                    { label: 'Forecast (EOM)', value: '$91,000', delta: '↑ 98% accuracy', color: 'text-cyan-600', bg: 'bg-cyan-50' },
                  ].map(({ label, value, delta, color, bg }) => (
                    <div key={label} className={`${bg} rounded-xl p-4 border border-white/80`}>
                      <p className="text-xs font-semibold text-slate-300 uppercase tracking-wide mb-1">{label}</p>
                      <p className="text-2xl font-bold text-slate-900">{value}</p>
                      <p className={`text-xs font-semibold mt-1 ${color}`}>{delta}</p>
                    </div>
                  ))}
                </div>

                {/* Fake chart */}
                <div className="h-40 bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl border border-blue-100/60 flex items-end px-4 pb-4 gap-2 overflow-hidden">
                  {[55, 70, 45, 80, 60, 90, 65, 78, 55, 85, 72, 95].map((h, i) => (
                    <div
                      key={i}
                      className="flex-1 bg-gradient-to-t from-blue-500 to-cyan-400 rounded-t-md opacity-60"
                      style={{ height: `${h}%`, transition: 'height 1s ease' }}
                    />
                  ))}
                </div>
              </div>
            </FadeSection>
          </div>
        </section>

        {/* ── HOW IT WORKS ────────────────────────────────────────── */}
        <section className="py-24 px-4 md:px-8 lg:px-16 landing-section-glass">
          <div className="max-w-7xl mx-auto">
            <FadeSection className="text-center mb-16">
              <p className="text-xs font-bold text-blue-600 uppercase tracking-widest mb-3">The Process</p>
              <h2 className="text-3xl md:text-4xl font-bold text-slate-900">How CloudWise AI Works</h2>
            </FadeSection>

            <div className="grid md:grid-cols-3 gap-6">
              {[
                {
                  step: '01',
                  icon: Activity,
                  title: 'Ingest & Analyze',
                  description: 'Connect your AWS, Azure, or GCP accounts securely. We analyze usage patterns, billing data, and performance metrics in real-time.',
                  color: 'text-blue-600',
                  bg: 'bg-blue-50',
                  delay: 0,
                },
                {
                  step: '02',
                  icon: BrainCircuit,
                  title: 'AI Discovery',
                  description: 'Our machine learning models identify anomalies, idle resources, and right-sizing opportunities that manual audits miss.',
                  color: 'text-cyan-600',
                  bg: 'bg-cyan-50',
                  delay: 100,
                },
                {
                  step: '03',
                  icon: Target,
                  title: 'Actionable FinOps',
                  description: 'Apply cost-saving recommendations with a single click, set strict budget alerts, and generate compliance reports automatically.',
                  color: 'text-emerald-600',
                  bg: 'bg-emerald-50',
                  delay: 200,
                },
              ].map(({ step, icon: Icon, title, description, color, bg, delay }) => (
                <FadeSection key={step} delay={delay}>
                  <div className="landing-card p-8 h-full">
                    <div className="flex items-start gap-4 mb-5">
                      <div className={`w-12 h-12 rounded-xl ${bg} flex items-center justify-center flex-shrink-0`}>
                        <Icon size={22} className={color} />
                      </div>
                      <span className="text-4xl font-bold text-slate-900 leading-none mt-1">{step}</span>
                    </div>
                    <h3 className="text-lg font-bold text-slate-900 mb-3">{title}</h3>
                    <p className="text-slate-600 leading-relaxed">{description}</p>
                  </div>
                </FadeSection>
              ))}
            </div>
          </div>
        </section>

        {/* ── CORE FEATURES ───────────────────────────────────────── */}
        <section id="features" className="py-28 px-4 md:px-8 lg:px-16">
          <div className="max-w-7xl mx-auto">
            <div className="grid lg:grid-cols-2 gap-16 items-center">
              <FadeSection>
                <p className="text-xs font-bold text-blue-600 uppercase tracking-widest mb-4">Core Features</p>
                <h2 className="text-3xl md:text-4xl font-bold text-[#FAFAFA] mb-6 leading-tight">
                  Engineered for Enterprise Scale
                </h2>
                <p className="text-lg text-slate-200 mb-10 leading-relaxed">
                  CloudWise is built to handle massive infrastructure deployments, providing granular
                  visibility into multi-account environments.
                </p>

                <ul className="space-y-7">
                  {[
                    {
                      icon: BarChart3,
                      title: 'Multi-Cloud Visibility',
                      desc: 'Unify billing across all your cloud providers into a single pane of glass.',
                      color: 'text-blue-600',
                      bg: 'bg-blue-50',
                    },
                    {
                      icon: Bell,
                      title: 'Automated Anomaly Alerts',
                      desc: 'Get notified in Slack or PagerDuty the moment spending spikes unexpectedly.',
                      color: 'text-cyan-600',
                      bg: 'bg-cyan-50',
                    },
                    {
                      icon: TrendingDown,
                      title: 'Predictive Forecasting',
                      desc: 'Advanced AI models predict end-of-month spend with 98% accuracy.',
                      color: 'text-emerald-600',
                      bg: 'bg-emerald-50',
                    },
                  ].map(({ icon: Icon, title, desc, color, bg }) => (
                    <li key={title} className="flex gap-4">
                      <div className={`w-10 h-10 rounded-xl ${bg} flex items-center justify-center flex-shrink-0 mt-0.5`}>
                        <Icon size={18} className={color} />
                      </div>
                      <div>
                        <h3 className="font-semibold text-[#FAFAFA] mb-1">{title}</h3>
                        <p className="text-slate-300">{desc}</p>
                      </div>
                    </li>
                  ))}
                </ul>
              </FadeSection>

              {/* Feature visual */}
              <FadeSection delay={100}>
                <div className="landing-card p-8">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="text-sm font-semibold text-slate-600">Live Monitoring</span>
                  </div>

                  <div className="space-y-4">
                    {[
                      { name: 'EC2 Instances', used: 68, cost: '$12,430', status: 'optimal' },
                      { name: 'S3 Storage', used: 43, cost: '$3,210', status: 'saving' },
                      { name: 'RDS Databases', used: 82, cost: '$8,900', status: 'warning' },
                      { name: 'Lambda Functions', used: 31, cost: '$890', status: 'saving' },
                    ].map(({ name, used, cost, status }) => (
                      <div key={name} className="bg-[#FAFAFA]/60 rounded-xl p-4 border border-slate-100">
                        <div className="flex items-center justify-between mb-2.5">
                          <span className="text-sm font-semibold text-[#FAFAFA]">{name}</span>
                          <div className="flex items-center gap-3">
                            <span className="text-sm font-bold text-slate-700">{cost}<span className="text-slate-300 font-normal">/mo</span></span>
                            <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                              status === 'optimal' ? 'bg-blue-100 text-blue-700' :
                              status === 'saving'  ? 'bg-emerald-100 text-emerald-700' :
                                                     'bg-amber-100 text-amber-700'
                            }`}>
                              {status}
                            </span>
                          </div>
                        </div>
                        <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              status === 'warning' ? 'bg-amber-400' :
                              status === 'saving'  ? 'bg-emerald-400' : 'bg-blue-400'
                            }`}
                            style={{ width: `${used}%` }}
                          />
                        </div>
                        <p className="text-xs text-slate-300 mt-1.5">{used}% utilization</p>
                      </div>
                    ))}
                  </div>
                </div>
              </FadeSection>
            </div>
          </div>
        </section>

        {/* ── METRICS ─────────────────────────────────────────────── */}
        <section className="py-24 px-4 md:px-8 landing-section-glass">
          <div className="max-w-7xl mx-auto">
            <FadeSection className="text-center mb-14">
              <h2 className="text-3xl md:text-4xl font-bold text-slate-900">Results that speak for themselves</h2>
            </FadeSection>

            <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
              {[
                { num: 32, suffix: '%', label: 'Average Cost Reduction', sub: 'Across all customers in Q1 2025', color: 'from-blue-500 to-blue-600' },
                { num: 10, suffix: 'x', label: 'ROI in First Quarter', sub: 'Median return on CloudWise investment', color: 'from-cyan-500 to-cyan-600' },
                { num: 0, suffix: '', label: 'Performance Impact', sub: 'Zero overhead on your infrastructure', color: 'from-emerald-500 to-emerald-600', display: 'Zero' },
              ].map(({ num, suffix, label, sub, color, display }) => (
                <FadeSection key={label}>
                  <div className="landing-card p-8 text-center">
                    <div className={`text-5xl font-bold bg-gradient-to-br ${color} bg-clip-text text-transparent mb-2`}>
                      {display ?? <AnimatedNumber to={num} suffix={suffix} />}
                    </div>
                    <div className="text-slate-900 font-semibold text-lg mb-1">{label}</div>
                    <div className="text-slate-500 text-sm">{sub}</div>
                  </div>
                </FadeSection>
              ))}
            </div>
          </div>
        </section>

        {/* ── SECURITY ────────────────────────────────────────────── */}
        <section id="security" className="py-28 px-4 md:px-8 lg:px-16">
          <div className="max-w-7xl mx-auto">
            <FadeSection className="text-center max-w-2xl mx-auto mb-14">
              <div className="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg shadow-blue-100">
                <Shield size={32} className="text-blue-600" />
              </div>
              <p className="text-xs font-bold text-blue-600 uppercase tracking-widest mb-3">Security</p>
              <h2 className="text-3xl md:text-4xl font-bold text-[#FAFAFA] mb-6">Enterprise-Grade Security</h2>
              <p className="text-xl text-slate-200">
                We never require write access to your infrastructure. CloudWise operates via strictly
                scoped, read-only IAM roles.
              </p>
            </FadeSection>

            <FadeSection delay={100}>
              <div className="flex justify-center gap-4 flex-wrap">
                {[
                  { icon: Lock, label: 'SOC2 Type II', sub: 'Audited annually' },
                  { icon: Shield, label: 'GDPR Compliant', sub: 'EU data residency' },
                  { icon: Lock, label: 'End-to-End Encryption', sub: 'AES-256 at rest' },
                  { icon: CheckCircle2, label: 'Read-Only IAM', sub: 'Zero write access' },
                ].map(({ icon: Icon, label, sub }) => (
                  <div key={label} className="landing-card px-6 py-4 flex items-center gap-3 min-w-[200px]">
                    <div className="w-9 h-9 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0">
                      <Icon size={16} className="text-blue-600" />
                    </div>
                    <div>
                      <p className="font-semibold text-slate-900 text-sm">{label}</p>
                      <p className="text-xs text-slate-500">{sub}</p>
                    </div>
                  </div>
                ))}
              </div>
            </FadeSection>
          </div>
        </section>

        {/* ── PRICING ─────────────────────────────────────────────── */}
        <section id="pricing" className="py-24 px-4 md:px-8 lg:px-16 landing-section-glass">
          <div className="max-w-7xl mx-auto">
            <FadeSection className="text-center mb-16">
              <p className="text-xs font-bold text-blue-600 uppercase tracking-widest mb-3">Pricing</p>
              <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">Simple, Transparent Pricing</h2>
              <p className="text-xl text-slate-600">Pay only for what we monitor. Cancel anytime.</p>
            </FadeSection>

            <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
              {/* Growth */}
              <FadeSection delay={0}>
                <div className="landing-card p-8 h-full flex flex-col">
                  <div className="mb-6">
                    <h3 className="text-2xl font-bold text-slate-900 mb-1">Growth</h3>
                    <p className="text-slate-500">Perfect for scaling startups</p>
                    <div className="mt-4">
                      <span className="text-5xl font-bold text-slate-900">$299</span>
                      <span className="text-slate-300 ml-1">/month</span>
                    </div>
                  </div>

                  <ul className="space-y-3 mb-8 flex-1">
                    {['Up to $50k monthly spend', 'Automated recommendations', 'Daily syncing', 'Email support'].map(item => (
                      <li key={item} className="flex items-center gap-3 text-slate-700">
                        <CheckCircle2 size={17} className="text-blue-500 flex-shrink-0" />
                        {item}
                      </li>
                    ))}
                  </ul>

                  <Link to="/register" className="block">
                    <button className="w-full py-3.5 rounded-xl border-2 border-blue-200 text-blue-700 font-semibold hover:bg-blue-50 transition-colors duration-200">
                      Start Free Trial
                    </button>
                  </Link>
                </div>
              </FadeSection>

              {/* Enterprise — popular */}
              <FadeSection delay={100}>
                <div className="landing-card p-8 h-full flex flex-col relative overflow-hidden border-blue-300/60" style={{ background: 'linear-gradient(135deg, rgba(239,246,255,0.85) 0%, rgba(224,242,254,0.85) 100%)' }}>
                  <div className="absolute top-0 right-0 bg-blue-600 text-[#FAFAFA] text-xs font-bold px-4 py-1.5 rounded-bl-xl">
                    MOST POPULAR
                  </div>

                  <div className="mb-6">
                    <h3 className="text-2xl font-bold text-slate-900 mb-1">Enterprise</h3>
                    <p className="text-slate-500">For complex multi-cloud setups</p>
                    <div className="mt-4">
                      <span className="text-5xl font-bold text-slate-900">$899</span>
                      <span className="text-slate-300 ml-1">/month</span>
                    </div>
                  </div>

                  <ul className="space-y-3 mb-8 flex-1">
                    {['Unlimited spend tracking', 'Real-time anomaly alerts', 'Dedicated success manager', 'Priority support & SLA'].map(item => (
                      <li key={item} className="flex items-center gap-3 text-slate-700">
                        <CheckCircle2 size={17} className="text-blue-500 flex-shrink-0" />
                        {item}
                      </li>
                    ))}
                  </ul>

                  <Link to="/register" className="block">
                    <button className="w-full py-3.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-[#FAFAFA] font-semibold shadow-lg shadow-blue-500/30 transition-all duration-200 hover:shadow-blue-500/50">
                      Contact Sales
                    </button>
                  </Link>
                </div>
              </FadeSection>
            </div>
          </div>
        </section>

        {/* ── FINAL CTA ────────────────────────────────────────────── */}
        <section className="py-32 px-4 md:px-8 lg:px-16 text-center">
          <div className="max-w-3xl mx-auto">
            <FadeSection>
              <div className="landing-card p-16">
                <h2 className="text-4xl md:text-5xl font-bold text-slate-900 mb-5">Ready to optimize?</h2>
                <p className="text-xl text-slate-600 mb-10 max-w-xl mx-auto leading-relaxed">
                  Join hundreds of engineering teams saving millions annually with CloudWise AI.
                </p>
                <Link to="/register">
                  <button className="group inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-[#FAFAFA] text-lg font-semibold px-10 py-4 rounded-2xl shadow-xl shadow-blue-500/30 transition-all duration-200 hover:shadow-blue-500/50 hover:-translate-y-0.5">
                    Start your 14-day free trial
                    <ArrowRight size={20} className="group-hover:translate-x-0.5 transition-transform" />
                  </button>
                </Link>
                <p className="text-sm text-slate-300 mt-5">No credit card required · Cancel anytime</p>
              </div>
            </FadeSection>
          </div>
        </section>

        {/* ── FOOTER ──────────────────────────────────────────────── */}
        <footer className="py-10 border-t border-white/10">
          <div className="max-w-7xl mx-auto px-4 md:px-8 flex flex-col md:flex-row justify-between items-center gap-5">
            <div className="flex items-center gap-2.5 font-bold text-[#FAFAFA]">
              <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center">
                <Cloud size={14} className="text-white" />
              </div>
              CloudWise AI
            </div>

            <div className="text-sm text-slate-300">
              © {new Date().getFullYear()} CloudWise FinOps Inc. All rights reserved.
            </div>

            <div className="flex gap-6 text-sm text-slate-300">
              <a href="#" className="hover:text-slate-200 transition-colors duration-200">Privacy Policy</a>
              <a href="#" className="hover:text-slate-200 transition-colors duration-200">Terms of Service</a>
            </div>
          </div>
        </footer>

        </div>{/* end sections wrapper */}

      </div>{/* end scrollable content */}
    </main>
  );
}
