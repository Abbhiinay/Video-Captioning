import { useState, useCallback, useRef } from "react";
import { motion } from "framer-motion";
import { Copy, Check, Briefcase, SmilePlus, Terminal, Heart } from "lucide-react";

const STYLE_CONFIG = {
  formal: {
    label: "Formal",
    icon: Briefcase,
    accentColor: "rgba(99, 102, 241, 0.8)",
    borderColor: "rgba(99, 102, 241, 0.2)",
    bgGlow: "rgba(99, 102, 241, 0.06)",
    glowStrong: "rgba(99, 102, 241, 0.2)",
    badgeBg: "bg-indigo-500/15",
    badgeText: "text-indigo-300",
    badgeBorder: "border-indigo-500/25",
  },
  sarcastic: {
    label: "Sarcastic",
    icon: SmilePlus,
    accentColor: "rgba(6, 182, 212, 0.8)",
    borderColor: "rgba(6, 182, 212, 0.2)",
    bgGlow: "rgba(6, 182, 212, 0.06)",
    glowStrong: "rgba(6, 182, 212, 0.2)",
    badgeBg: "bg-cyan-500/15",
    badgeText: "text-cyan-300",
    badgeBorder: "border-cyan-500/25",
  },
  humorous_tech: {
    label: "Humorous Tech",
    icon: Terminal,
    accentColor: "rgba(124, 58, 237, 0.8)",
    borderColor: "rgba(124, 58, 237, 0.2)",
    bgGlow: "rgba(124, 58, 237, 0.06)",
    glowStrong: "rgba(124, 58, 237, 0.2)",
    badgeBg: "bg-violet-500/15",
    badgeText: "text-violet-300",
    badgeBorder: "border-violet-500/25",
  },
  humorous_non_tech: {
    label: "Humorous Non-Tech",
    icon: Heart,
    accentColor: "rgba(251, 191, 36, 0.8)",
    borderColor: "rgba(251, 191, 36, 0.2)",
    bgGlow: "rgba(251, 191, 36, 0.06)",
    glowStrong: "rgba(251, 191, 36, 0.2)",
    badgeBg: "bg-amber-500/15",
    badgeText: "text-amber-300",
    badgeBorder: "border-amber-500/25",
  },
};

export default function CaptionCard({ style, caption, index = 0 }) {
  const [copied, setCopied] = useState(false);
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);
  const cardRef = useRef(null);
  const config = STYLE_CONFIG[style] || STYLE_CONFIG.formal;
  const Icon = config.icon;

  const handleCopy = async () => {
    if (!caption) return;
    try {
      await navigator.clipboard.writeText(caption);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard may not be available */
    }
  };

  const handleMouseMove = useCallback((e) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    setTilt({ x: y * -8, y: x * 8 });
  }, []);

  const handleMouseLeave = useCallback(() => {
    setTilt({ x: 0, y: 0 });
    setIsHovered(false);
  }, []);

  return (
    <motion.div
      ref={cardRef}
      initial={{ opacity: 0, y: 28, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{
        duration: 0.5,
        delay: index * 0.12,
        ease: [0.22, 1, 0.36, 1],
      }}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={handleMouseLeave}
      className="glass-card rounded-2xl p-6 flex flex-col gap-4
                 relative overflow-hidden group cursor-default"
      style={{
        transform: `perspective(1000px) rotateX(${tilt.x}deg) rotateY(${tilt.y}deg)`,
        transition: "transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s ease, border-color 0.3s ease",
        borderColor: isHovered ? config.accentColor : config.borderColor,
        boxShadow: isHovered
          ? `0 0 40px ${config.glowStrong}, 0 8px 32px rgba(0, 0, 0, 0.3)`
          : "0 0 0 0 transparent",
      }}
    >
      {/* Top accent line */}
      <motion.div
        className="absolute top-0 left-6 right-6 h-[2px] rounded-full"
        style={{ background: config.accentColor }}
        animate={
          isHovered
            ? { opacity: [0.5, 1, 0.5] }
            : { opacity: 0.4 }
        }
        transition={isHovered ? { duration: 2, repeat: Infinity, ease: "easeInOut" } : { duration: 0.3 }}
      />

      {/* Header */}
      <div className="flex items-center justify-between relative z-10">
        <div className="flex items-center gap-2">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-300"
            style={{
              background: config.bgGlow,
              boxShadow: isHovered ? `0 0 16px ${config.bgGlow}` : "none",
            }}
          >
            <Icon className="w-4 h-4" style={{ color: config.accentColor }} />
          </div>
          <span
            className={`px-3 py-1 rounded-lg text-xs font-semibold border ${config.badgeBg} ${config.badgeText} ${config.badgeBorder}`}
          >
            {config.label}
          </span>
        </div>

        <button
          onClick={handleCopy}
          disabled={!caption}
          className="p-2 rounded-lg bg-white/5 border border-white/8
                     hover:bg-white/10 hover:border-white/15
                     transition-all duration-200 cursor-pointer
                     disabled:opacity-30 disabled:cursor-not-allowed relative z-10"
          aria-label={`Copy ${config.label} caption`}
        >
          {copied ? (
            <motion.div
              initial={{ scale: 0, rotate: -90 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ type: "spring", stiffness: 400, damping: 15 }}
            >
              <Check className="w-4 h-4 text-green-400" />
            </motion.div>
          ) : (
            <Copy className="w-4 h-4 text-on-surface-variant" />
          )}
        </button>
      </div>

      {/* Caption Text */}
      <div className="relative z-10">
        <div
          className="absolute left-0 top-0 bottom-0 w-[2px] rounded-full opacity-30"
          style={{ background: config.accentColor }}
        />
        <p className="text-on-surface text-base leading-relaxed min-h-[4rem] flex items-center pl-4">
          {caption || (
            <span className="text-on-surface-variant/40 italic">
              No caption generated
            </span>
          )}
        </p>
      </div>

      {/* Copied feedback */}
      {copied && (
        <motion.div
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          className="absolute bottom-3 right-4 text-xs text-green-400 font-medium z-10"
        >
          Copied to clipboard!
        </motion.div>
      )}
    </motion.div>
  );
}
