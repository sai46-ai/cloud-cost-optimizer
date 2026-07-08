import { Suspense } from 'react';
import { Outlet } from 'react-router-dom';
import { CloudRain, Cpu, BarChart3, ShieldCheck } from 'lucide-react';

const AuthFallback = () => (
  <div className="w-full flex items-center justify-center p-12">
    <div className="w-8 h-8 border-4 border-accent-primary border-t-transparent rounded-full animate-spin"></div>
  </div>
);

export default function AuthLayout() {
  return (
    <main className="min-h-screen bg-background-primary flex flex-col md:flex-row overflow-hidden">
      {/* Left Panel: Authentication Form */}
      <div className="flex-1 flex flex-col items-center justify-center px-4 sm:px-6 lg:px-20 py-12 relative z-10 md:max-w-xl lg:max-w-2xl w-full mx-auto md:mx-0 shrink-0">
        <div className="w-full max-w-[440px] mb-8 flex justify-start pl-2 sm:pl-0">
          <div className="flex items-center gap-2 text-accent-primary">
            <CloudRain size={28} />
            <span className="text-xl font-bold tracking-tight text-text-primary">CloudWise AI</span>
          </div>
        </div>
        <div className="w-full relative">
          <Suspense fallback={<AuthFallback />}>
            <Outlet />
          </Suspense>
        </div>
      </div>

      {/* Right Panel: Premium Visual Experience */}
      <div className="hidden md:flex flex-1 relative bg-[#0b0f19] overflow-hidden border-l border-[#FAFAFA]/5 items-center justify-center p-12">
        {/* Subtle mesh background and glowing orbs */}
        <div className="absolute top-[-10%] right-[-5%] w-[600px] h-[600px] bg-accent-primary/20 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-accent-cyan/15 rounded-full blur-[100px]" />
        <div className="absolute top-1/2 left-1/2 w-[400px] h-[400px] bg-accent-emerald/10 rounded-full blur-[90px] transform -translate-x-1/2 -translate-y-1/2" />

        {/* Grid pattern overlay */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(250,250,250,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(250,250,250,0.02)_1px,transparent_1px)] bg-[size:40px_40px] [mask-image:radial-gradient(ellipse_60%_60%_at_50%_50%,#111827_20%,transparent_100%)]"></div>

        <div className="relative z-10 w-full max-w-lg flex flex-col gap-6">
          <div className="mb-4">
            <h2 className="text-4xl lg:text-5xl font-semibold text-[#FAFAFA] tracking-tight mb-4 leading-[1.15]">
              Master your cloud<br />
              with <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent-primary to-accent-cyan">Enterprise AI</span>
            </h2>
            <p className="text-lg text-[#FAFAFA]/60 leading-relaxed font-light">
              Detect anomalies, forecast spending, and optimize your architecture with actionable intelligence.
            </p>
          </div>

          {/* Floating Glass Cards */}
          <div className="grid grid-cols-1 gap-4 mt-6">
            <div className="flex items-center gap-4 bg-[#FAFAFA]/5 backdrop-blur-md border border-[#FAFAFA]/10 p-5 rounded-2xl shadow-2xl transform hover:-translate-y-1 transition-transform duration-300">
              <div className="flex-shrink-0 w-12 h-12 bg-accent-primary/20 rounded-full flex items-center justify-center text-accent-primary">
                <Cpu size={24} />
              </div>
              <div>
                <h3 className="text-[#FAFAFA] font-medium text-[15px]">Automated Rightsizing</h3>
                <p className="text-[#FAFAFA]/50 text-sm mt-0.5">Save up to 40% on compute costs</p>
              </div>
            </div>

            <div className="flex items-center gap-4 bg-[#FAFAFA]/5 backdrop-blur-md border border-[#FAFAFA]/10 p-5 rounded-2xl shadow-2xl transform hover:-translate-y-1 transition-transform duration-300 ml-8">
              <div className="flex-shrink-0 w-12 h-12 bg-accent-cyan/20 rounded-full flex items-center justify-center text-accent-cyan">
                <BarChart3 size={24} />
              </div>
              <div>
                <h3 className="text-[#FAFAFA] font-medium text-[15px]">Real-time Anomaly Detection</h3>
                <p className="text-[#FAFAFA]/50 text-sm mt-0.5">Spot cost spikes before they snowball</p>
              </div>
            </div>

            <div className="flex items-center gap-4 bg-[#FAFAFA]/5 backdrop-blur-md border border-[#FAFAFA]/10 p-5 rounded-2xl shadow-2xl transform hover:-translate-y-1 transition-transform duration-300">
              <div className="flex-shrink-0 w-12 h-12 bg-accent-emerald/20 rounded-full flex items-center justify-center text-accent-emerald">
                <ShieldCheck size={24} />
              </div>
              <div>
                <h3 className="text-[#FAFAFA] font-medium text-[15px]">Enterprise Security</h3>
                <p className="text-[#FAFAFA]/50 text-sm mt-0.5">Role-based access & strict isolation</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
