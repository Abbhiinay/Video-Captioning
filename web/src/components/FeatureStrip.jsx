import { useCallback, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Layers, Cpu, Zap, ClipboardCopy } from "lucide-react";

const FEATURES = [
  { icon: Layers, title: "4 Unique Styles", desc: "Formal, Sarcastic, Tech & Non-Tech humor", color: "#7c3aed" },
  { icon: Cpu, title: "AI-Powered", desc: "Gemini 2.5 Flash multimodal analysis", color: "#06b6d4" },
  { icon: Zap, title: "Instant Results", desc: "Captions generated in under a minute", color: "#fbbf24" },
  { icon: ClipboardCopy, title: "One-Click Copy", desc: "Copy any caption to your clipboard", color: "#c4b5fd" },
];

function TiltFeatureCard({ feature, index }) {
  const cardRef = useRef(null);
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = useCallback((e) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    setTilt({ x: y * -10, y: x * 10 });
  }, []);

  const handleMouseLeave = useCallback(() => {
    setTilt({ x: 0, y: 0 });
    setIsHovered(false);
  }, []);

  const Icon = feature.icon;

  return (
    <motion.div
      ref={cardRef}
      initial={{ opacity: 0, y: 20, rotateX: 10 }}
      animate={{ opacity: 1, y: 0, rotateX: 0 }}
      transition={{
        duration: 0.5,
        delay: 0.6 + index * 0.1,
        ease: [0.22, 1, 0.36, 1],
      }}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={handleMouseLeave}
      className="glass-card glass-card-hover rounded-xl p-5 flex flex-col items-center text-center gap-3
                 transition-all duration-300 cursor-default"
      style={{
        transform: `perspective(600px) rotateX(${tilt.x}deg) rotateY(${tilt.y}deg)`,
        transition: "transform 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
      }}
    >
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-300"
        style={{
          background: `rgba(${hexToRgb(feature.color)}, 0.1)`,
          border: `1px solid rgba(${hexToRgb(feature.color)}, 0.2)`,
          boxShadow: isHovered
            ? `0 0 25px rgba(${hexToRgb(feature.color)}, 0.25)`
            : "none",
        }}
      >
        <Icon className="w-5 h-5" style={{ color: feature.color }} />
      </div>
      <div>
        <p className="text-on-surface text-sm font-semibold">{feature.title}</p>
        <p className="text-on-surface-variant text-xs mt-1 leading-relaxed">{feature.desc}</p>
      </div>
    </motion.div>
  );
}

/* Convert hex color to r,g,b for rgba() usage */
function hexToRgb(hex) {
  const h = hex.replace("#", "");
  const r = parseInt(h.substring(0, 2), 16);
  const g = parseInt(h.substring(2, 4), 16);
  const b = parseInt(h.substring(4, 6), 16);
  return `${r}, ${g}, ${b}`;
}

export default function FeatureStrip() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.7, delay: 0.5 }}
      className="w-full max-w-4xl mx-auto mt-16 grid grid-cols-2 md:grid-cols-4 gap-4"
    >
      {FEATURES.map((f, i) => (
        <TiltFeatureCard key={f.title} feature={f} index={i} />
      ))}
    </motion.div>
  );
}
