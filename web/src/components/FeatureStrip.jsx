import { motion } from "framer-motion";
import { Layers, Cpu, Zap, ClipboardCopy } from "lucide-react";

const FEATURES = [
  { icon: Layers, title: "4 Unique Styles", desc: "Formal, Sarcastic, Tech & Non-Tech humor" },
  { icon: Cpu, title: "AI-Powered", desc: "Gemini 2.5 Flash multimodal analysis" },
  { icon: Zap, title: "Instant Results", desc: "Captions generated in under a minute" },
  { icon: ClipboardCopy, title: "One-Click Copy", desc: "Copy any caption to your clipboard" },
];

export default function FeatureStrip() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.7, delay: 0.5 }}
      className="w-full max-w-4xl mx-auto mt-16 grid grid-cols-2 md:grid-cols-4 gap-4"
    >
      {FEATURES.map((f, i) => (
        <motion.div
          key={f.title}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.6 + i * 0.1 }}
          className="glass-card glass-card-hover rounded-xl p-5 flex flex-col items-center text-center gap-3 transition-all duration-300"
        >
          <div className="w-10 h-10 rounded-xl bg-primary-container/10 border border-primary-container/20 flex items-center justify-center">
            <f.icon className="w-5 h-5 text-primary" />
          </div>
          <div>
            <p className="text-on-surface text-sm font-semibold">{f.title}</p>
            <p className="text-on-surface-variant text-xs mt-1 leading-relaxed">{f.desc}</p>
          </div>
        </motion.div>
      ))}
    </motion.div>
  );
}
