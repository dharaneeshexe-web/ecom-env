"use client";
import React, { useState, useEffect } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer
} from "recharts";
import { 
  CheckCircle, XCircle, Zap, Activity, Fingerprint, Network, 
  Cpu, Workflow, RotateCcw, Box, Crosshair, AlertTriangle, ShieldAlert,
  FileText, Volume2
} from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const API_BASE = "http://localhost:8000";

// --- Cosmic Background Components ---
const NeuralBackground = () => (
  <div className="fixed inset-0 overflow-hidden pointer-events-none z-0 bg-[#050508]">
    <motion.div 
      animate={{ y: [0, -50, 0], x: [0, 30, 0], scale: [1, 1.1, 1] }} 
      transition={{ duration: 15, repeat: Infinity, ease: "easeInOut" }} 
      className="absolute -top-[20%] left-[10%] w-[60vw] h-[60vw] rounded-full bg-purple-900/10 blur-[140px]" 
    />
    <motion.div 
      animate={{ y: [0, 50, 0], x: [0, -40, 0], scale: [1, 1.2, 1] }} 
      transition={{ duration: 20, repeat: Infinity, ease: "easeInOut", delay: 2 }} 
      className="absolute top-[30%] -right-[10%] w-[50vw] h-[50vw] rounded-full bg-cyan-900/10 blur-[140px]" 
    />
    <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_60%_60%_at_50%_50%,#000_10%,transparent_100%)]" />
  </div>
);

const ParticleField = () => (
  <div className="fixed inset-0 pointer-events-none z-0">
    {[...Array(20)].map((_, i) => (
      <motion.div
        key={i}
        className="particle"
        initial={{ top: `${Math.random() * 100}%`, left: `${Math.random() * 100}%`, opacity: 0 }}
        animate={{ y: [-20, -120], opacity: [0, 0.5, 0], x: Math.random() * 50 - 25 }}
        transition={{ duration: 5 + Math.random() * 10, repeat: Infinity, delay: Math.random() * 5 }}
      />
    ))}
  </div>
);

const LoaderCore = () => (
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" className="text-cyan-500 drop-shadow-[0_0_15px_rgba(6,182,212,1)]">
    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1" strokeDasharray="10 40" strokeLinecap="round" className="animate-spin" />
    <path d="M12 8v4l2 2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

export default function Dashboard() {
  const [state, setState] = useState<any>(null);
  const [autoMode, setAutoMode] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [cursorPos, setCursorPos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouse = (e: MouseEvent) => setCursorPos({ x: e.clientX, y: e.clientY });
    window.addEventListener("mousemove", handleMouse);
    return () => window.removeEventListener("mousemove", handleMouse);
  }, []);

  const fetchState = async () => {
    try {
      const res = await axios.get(`${API_BASE}/state`);
      setState(res.data);
    } catch (e) {
      console.error("Backend offline", e);
    }
  };

  useEffect(() => { fetchState(); }, []);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (autoMode && state && !state.done) {
      interval = setInterval(() => { handleAgentAction(); }, 1800);
    }
    return () => clearInterval(interval);
  }, [autoMode, state]);

  const handleAgentAction = async () => {
    if (!state || state.done) return;
    setIsThinking(true);
    try {
      const res = await axios.post(`${API_BASE}/agent_step`);
      setState(res.data);
    } catch (e) {
      setAutoMode(false);
    } finally {
      setIsThinking(false);
    }
  };

  const handleAction = async (action_type: number) => {
    if (!state || state.done) return;
    try {
      const res = await axios.post(`${API_BASE}/step`, { action_type });
      setState(res.data);
    } catch (e) { console.error(e); }
  };

  const handleReset = async () => {
    setAutoMode(false);
    try {
      const res = await axios.post(`${API_BASE}/reset`);
      setState(res.data);
    } catch (e) { console.error(e); }
  };

  if (!state) return (
    <div className="min-h-screen bg-[#050508] flex items-center justify-center text-white font-mono relative">
      <LoaderCore />
      <span className="ml-4 text-cyan-400 tracking-widest uppercase animate-pulse">Initializing Nexus...</span>
    </div>
  );

  const { observation, metrics, done, history, profit_history } = state;

  return (
    <div className="min-h-screen text-white relative font-sans overflow-x-hidden bg-mesh selection:bg-cyan-500/30">
      <NeuralBackground />
      <ParticleField />
      
      <motion.div 
        className="fixed top-0 left-0 w-64 h-64 bg-cyan-500/5 rounded-full blur-[80px] pointer-events-none z-50"
        animate={{ x: cursorPos.x - 128, y: cursorPos.y - 128 }}
      />

      <nav className="fixed top-0 w-full z-50 glass-panel border-b border-white/5 bg-black/20 px-8 py-4 backdrop-blur-2xl">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
              <div className="bg-gradient-to-tr from-cyan-500 to-purple-600 p-2 rounded-xl group hover:shadow-[0_0_20px_rgba(6,182,212,0.5)] transition-all">
                <Cpu className="text-white animate-pulse" size={24} />
              </div>
              <h1 className="text-xl font-bold tracking-tight">Nexus AI <span className="text-gray-500 font-normal">Command</span></h1>
            </div>
            <div className="hidden md:flex items-center gap-2 px-4 py-1 bg-white/5 rounded-full border border-white/10 text-[10px] uppercase tracking-widest text-emerald-400 font-bold">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" /> Neural Online
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            {isThinking && <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-cyan-400 text-xs font-mono tracking-wider animate-pulse">LLM INFERENCE</motion.div>}
            <button 
              onClick={() => setAutoMode(!autoMode)}
              className={cn("px-6 py-2 rounded-full font-bold tracking-wider text-sm border transition-all", autoMode ? "bg-purple-600/20 text-purple-300 border-purple-500/50 shadow-[0_0_15px_#a855f755]" : "bg-white/5 border-white/10 text-gray-300")}
            >
              {autoMode ? "Halt AutoMission" : "Engage AI Auto"}
            </button>
            <button onClick={handleReset} className="p-2 bg-white/5 rounded-full hover:bg-red-500/20 transition-colors"><RotateCcw size={18} /></button>
          </div>
        </div>
      </nav>

      <main className="relative z-10 pt-28 pb-12 px-6 max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        <div className="lg:col-span-7 space-y-8">
          <motion.div layout initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-panel p-8 relative overflow-hidden glow-card">
            {isThinking && <div className="scanline" />}
            
            <div className="flex justify-between items-start mb-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-blue-500/10 rounded-xl text-blue-400 border border-blue-500/20"><Fingerprint size={28}/></div>
                <div>
                  <h2 className="text-2xl font-black text-gray-100 flex items-center gap-3">
                    TXN-ID #{state.step_count + 1042}
                    {observation.is_inspected && <span className="px-2 py-1 bg-amber-500/10 text-amber-500 text-[9px] uppercase font-bold border border-amber-500/20 rounded">Inspected</span>}
                  </h2>
                  <p className="text-xs text-gray-500 font-mono tracking-widest uppercase">Pending Neural Audit</p>
                </div>
              </div>
              <div className="text-right">
                <motion.div key={observation.product_price} initial={{ opacity:0, x:20 }} animate={{ opacity:1, x:0 }} className="text-5xl font-black text-gradient leading-none">${observation.product_price.toFixed(2)}</motion.div>
                <div className="text-[10px] text-gray-500 uppercase font-black tracking-widest mt-2">{observation.order_value_tier} Value Asset</div>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              {[
                { l: 'Profile', v: observation.customer_type, c: observation.customer_type==='fraudster'?'text-red-400':'text-emerald-400' },
                { l: 'Reason', v: {0:'Defect',1:'Wrong',2:'Personal',3:'Late',4:'Price'}[observation.return_reason]||'Subjective', c: 'text-blue-400' },
                { l: 'Days', v: observation.days_since_purchase, c: 'text-purple-400' },
                { l: 'Trust', v: observation.customer_rating.toFixed(1), c: 'text-amber-400' }
              ].map((item, i) => (
                <div key={i} className="bg-black/40 p-4 rounded-2xl border border-white/5">
                  <div className="text-[8px] uppercase tracking-widest text-gray-500 font-black mb-1">{item.l}</div>
                  <div className={cn("text-sm font-bold uppercase", item.c)}>{item.v}</div>
                </div>
              ))}
            </div>

            <div className="mb-8 p-6 bg-white/[0.02] border border-white/5 rounded-2xl">
              <div className="flex justify-between text-[10px] uppercase font-black tracking-widest text-gray-500 mb-4">
                <span>Anomaly Probability</span>
                <span className={cn(observation.fraud_risk > 0.6 ? "text-red-400" : "text-emerald-400")}>{(observation.fraud_risk*100).toFixed(1)}%</span>
              </div>
              <div className="h-2 w-full bg-black/40 rounded-full overflow-hidden border border-white/5">
                <motion.div initial={{ width: 0 }} animate={{ width: `${observation.fraud_risk*100}%` }} transition={{ duration: 1 }} className={cn("h-full relative", observation.fraud_risk > 0.6 ? "bg-red-500" : "bg-emerald-500")}>
                   <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"/>
                </motion.div>
              </div>
              <AnimatePresence>
                {observation.investigation_report && (
                  <motion.div initial={{ opacity:0, height:0 }} animate={{ opacity:1, height:'auto' }} className="mt-6 pt-6 border-t border-white/5 text-[11px] font-mono text-blue-300 leading-relaxed italic">
                    {">"} Analysis Report: {observation.investigation_report}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { id: 0, label: 'APPROVE', icon: CheckCircle, color: 'emerald' },
                { id: 2, label: 'PARTIAL', icon: Zap, color: 'amber' },
                { id: 3, label: 'INSPECT', icon: Crosshair, color: 'blue' },
                { id: 1, label: 'REJECT', icon: XCircle, color: 'rose' }
              ].map((act) => (
                <motion.button 
                  key={act.id} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                  onClick={() => handleAction(act.id)}
                  className={cn("h-24 bg-black/40 border-2 border-white/5 rounded-2xl flex flex-col items-center justify-center transition-all hover:border-current disabled:opacity-20", `text-${act.color}-500`)}
                >
                  <act.icon size={28}/>
                  <span className="text-[9px] font-black tracking-widest mt-2">{act.label}</span>
                </motion.button>
              ))}
            </div>

            <div className="mt-8 pt-8 border-t border-white/5 flex gap-4">
               <button onClick={() => window.open(`${API_BASE}/download_audit`, '_blank')} className="flex-1 bg-white/5 hover:bg-white/10 p-4 rounded-xl text-[10px] uppercase font-black tracking-widest border border-white/10 flex items-center justify-center gap-3"><FileText size={16}/> Build Audit PDF</button>
               <button onClick={() => { const s=window.speechSynthesis; const u=new SpeechSynthesisUtterance(`Risk at ${Math.round(observation.fraud_risk*100)} percent. Requesting manual audit.`); u.pitch=0.7; s.speak(u); }} className="w-16 bg-white/5 rounded-xl border border-white/10 flex items-center justify-center text-cyan-400"><Volume2 size={20}/></button>
               <button onClick={() => handleAction(4)} className="px-8 bg-rose-500/10 border border-rose-500/20 text-rose-500 text-[10px] font-black rounded-xl hover:bg-rose-500/20 transition-all uppercase">HITL ESCALATE</button>
            </div>
          </motion.div>

          <div className="grid grid-cols-3 gap-6">
            {[
              { i: Box, v: metrics.total_steps, l: 'Processed', c: 'text-purple-400' },
              { i: Activity, v: `$${metrics.profit.toFixed(0)}`, l: 'Profit Flow', c: 'text-emerald-400' },
              { i: ShieldAlert, v: metrics.fraud_intercepted, l: 'Intercepted', c: 'text-rose-400' }
            ].map((s, i) => (
              <div key={i} className="glass-panel p-6 flex flex-col items-center border-t-2 border-current hover:shadow-lg transition-all" style={{color: s.c.includes('emerald')?'#10b981':s.c.includes('rose')?'#f43f5e':'#a855f7'}}>
                <s.i size={20} className="mb-2"/>
                <div className="text-3xl font-black text-white">{s.v}</div>
                <div className="text-[9px] uppercase font-black tracking-[0.3em] opacity-40 mt-1">{s.l}</div>
              </div>
            ))}
          </div>

          <div className="glass-panel p-8">
             <div className="h-48 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={profit_history}>
                    <defs><linearGradient id="p" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#22d3ee" stopOpacity={0.3}/><stop offset="95%" stopColor="#22d3ee" stopOpacity={0}/></linearGradient></defs>
                    <XAxis dataKey="step" hide/><YAxis hide domain={['auto','auto']}/>
                    <Tooltip contentStyle={{backgroundColor:'#000',border:'none',borderRadius:'8px',fontSize:'10px'}}/>
                    <Area type="monotone" dataKey="profit" stroke="#22d3ee" strokeWidth={3} fill="url(#p)"/>
                  </AreaChart>
                </ResponsiveContainer>
             </div>
          </div>
        </div>

        <div className="lg:col-span-5 h-[850px] flex flex-col">
          <div className="glass-panel p-6 flex-1 overflow-hidden relative flex flex-col">
            <h3 className="text-[10px] uppercase font-black tracking-widest text-gray-500 mb-6 flex items-center gap-2"><Workflow size={14}/> Neural Trace Engine</h3>
            <div className="flex-1 overflow-y-auto space-y-4 pr-2 scrollbar-hide">
              <AnimatePresence>
                {history.slice().reverse().map((item: any) => (
                  <motion.div key={item.id} layout initial={{ opacity:0, x:20 }} animate={{ opacity:1, x:0 }} className="bg-black/30 border border-white/5 p-4 rounded-xl relative overflow-hidden group hover:bg-black/50 transition-all">
                    <div className={cn("absolute left-0 top-0 bottom-0 w-1", item.action==='Approved'?'bg-emerald-500':item.action==='Rejected'?'bg-rose-500':'bg-blue-500')}/>
                    <div className="flex justify-between items-center mb-2">
                       <span className="text-[9px] font-black uppercase tracking-widest opacity-60">{item.action}</span>
                       <span className="text-[9px] font-mono opacity-40">${item.price.toFixed(0)}</span>
                    </div>
                    <div className="text-[11px] font-mono text-gray-300 leading-relaxed border-l-2 border-white/5 pl-3 py-1 italic">{item.reasoning}</div>
                    <div className="mt-2 text-[9px] font-black flex justify-between">
                       <span className={item.reward > 0 ? "text-emerald-500" : "text-rose-500"}>{item.reward > 0 ? `+${item.reward.toFixed(1)}$` : `${item.reward.toFixed(1)}$`}</span>
                       {item.fraud_intercepted && <span className="text-rose-500 tracking-[0.2em]">SHIELD DETECTED</span>}
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
            <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-black to-transparent pointer-events-none"/>
          </div>
        </div>
      </main>
    </div>
  );
}
