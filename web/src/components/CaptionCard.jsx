import { useState } from "react";
import { motion } from "framer-motion";
import { Copy, Check, Briefcase, SmilePlus, Terminal, Heart } from "lucide-react";

const STYLE_CONFIG = {
  formal: {
    label: "Formal",
    icon: Briefcase,
    accentColor: "rgba(99, 102, 241, 0.8)",
    borderColor: "rgba(99, 102, 241, 0.3)",
    bgGlow: "rgba(99, 102, 241, 0.06)",
    badgeBg: "bg-indigo-500/15",
    badgeText: "text-indigo-300",
    badgeBorder: "border-indigo-500/30",
  },
  sarcastic: {
    label: "Sarcastic",
    icon: SmilePlus,
    accentColor: "rgba(6, 182, 212, 0.8)",
    borderColor: "rgba(6, 182, 212, 0.3)",
    bgGlow: "rgba(6, 182, 212, 0.06)",
    badgeBg: "bg-cyan-500/15",
    badgeText: "text-cyan-300",
    badgeBorder: "border-cyan-500/30",
  },
  humorous_tech: {
    label: "Humorous Tech",
    icon: Terminal,
    accentColor: "rgba(124, 58, 237, 0.8)",
    borderColor: "rgba(124, 58, 237, 0.3)",
    bgGlow: "rgba(124, 58, 237, 0.06)",
    badgeBg: "bg-violet-500/15",
    badgeText: "text-violet-300",
    badgeBorder: "border-violet-500/30",
  },
  humorous_non_tech: {
    label: "Humorous Non-Tech",
    icon: Heart,
    accentColor: "rgba(245, 158, 11, 0.8)",
    borderColor: "rgba(245, 158, 11, 0.3)",
    bgGlow: "rgba(245, 158, 11, 0.06)",
    badgeBg: "bg-amber-500/15",
    badgeText: "text-amber-300",
    badgeBorder: "border-amber-500/30",
  },
};

export default function CaptionCard({ style, caption, index = 0 }) {
  const [copied, setCopied] = useState(false);
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

  return (
    <motion.div
      initial={{ opacity: 0, y: 24, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{
        duration: 0.5,
        delay: index * 0.12,
        ease: [0.22, 1, 0.36, 1],
      }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      className="glass-card glass-card-hover rounded-2xl p-6 flex flex-col gap-4
                 relative overflow-hidden group transition-all duration-300"
      style={{
        borderColor: config.borderColor,
        boxShadow: `0 0 0 0 transparent`,
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = `0 0 30px ${config.bgGlow}`;
        e.currentTarget.style.borderColor = config.accentColor;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = "0 0 0 0 transparent";
        e.currentTarget.style.borderColor = config.borderColor;
      }}
    >
      {/* Top accent line */}
      <div
        className="absolute top-0 left-6 right-6 h-[2px] rounded-full opacity-60"
        style={{ background: config.accentColor }}
      />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: config.bgGlow }}
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
          className="p-2 rounded-lg bg-white/5 border border-white/10
                     hover:bg-white/10 hover:border-white/20
                     transition-all duration-200 cursor-pointer
                     disabled:opacity-30 disabled:cursor-not-allowed"
          aria-label={`Copy ${config.label} caption`}
        >
          {copied ? (
            <Check className="w-4 h-4 text-green-400" />
          ) : (
            <Copy className="w-4 h-4 text-on-surface-variant" />
          )}
        </button>
      </div>

      {/* Caption Text */}
      <p className="text-on-surface text-base leading-relaxed min-h-[4rem] flex items-center">
        {caption || (
          <span className="text-on-surface-variant/50 italic">
            No caption generated
          </span>
        )}
      </p>

      {/* Copied feedback */}
      {copied && (
        <motion.div
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          className="absolute bottom-2 right-4 text-xs text-green-400 font-medium"
        >
          Copied!
        </motion.div>
      )}
    </motion.div>
  );
}
