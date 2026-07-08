import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";

const STEPS = [
  { label: "Uploading video", emoji: "📤" },
  { label: "Extracting frames", emoji: "🎞️" },
  { label: "Analyzing content", emoji: "🔍" },
  { label: "Generating captions", emoji: "✨" },
];

export default function LoadingState({ step = 0 }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="w-full max-w-2xl mx-auto flex flex-col items-center"
    >
      {/* Orbiting AI indicator */}
      <div className="relative w-32 h-32 mb-10">
        {/* Outer ring */}
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
          className="absolute inset-0 rounded-full border-2 border-primary-container/30"
          style={{
            borderTopColor: "rgba(124, 58, 237, 0.8)",
            borderRightColor: "rgba(6, 182, 212, 0.5)",
          }}
        />
        {/* Inner ring */}
        <motion.div
          animate={{ rotate: -360 }}
          transition={{ duration: 5, repeat: Infinity, ease: "linear" }}
          className="absolute inset-4 rounded-full border-2 border-secondary/20"
          style={{
            borderBottomColor: "rgba(6, 182, 212, 0.7)",
            borderLeftColor: "rgba(124, 58, 237, 0.4)",
          }}
        />
        {/* Center pulse */}
        <motion.div
          animate={{ scale: [1, 1.2, 1], opacity: [0.6, 1, 0.6] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          className="absolute inset-8 rounded-full gradient-primary flex items-center justify-center glow-violet-strong"
        >
          <Sparkles className="w-8 h-8 text-white" />
        </motion.div>
      </div>

      {/* Progress steps */}
      <div className="flex flex-col gap-3 w-full max-w-sm">
        {STEPS.map((s, i) => {
          const isActive = i === step;
          const isDone = i < step;
          return (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, x: -20 }}
              animate={{
                opacity: isDone || isActive ? 1 : 0.3,
                x: 0,
              }}
              transition={{ duration: 0.4, delay: i * 0.1 }}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 ${
                isActive
                  ? "glass-elevated glow-violet"
                  : isDone
                  ? "glass-card"
                  : "bg-transparent"
              }`}
            >
              <span className="text-lg">{s.emoji}</span>
              <span
                className={`text-sm font-medium ${
                  isActive
                    ? "text-primary"
                    : isDone
                    ? "text-on-surface-variant line-through"
                    : "text-on-surface-variant/40"
                }`}
              >
                {s.label}
              </span>
              {isActive && (
                <motion.div
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  className="ml-auto text-xs text-secondary font-mono"
                >
                  •••
                </motion.div>
              )}
              {isDone && (
                <span className="ml-auto text-xs text-green-400">✓</span>
              )}
            </motion.div>
          );
        })}
      </div>

      {/* Progress bar */}
      <div className="w-full max-w-sm mt-6 h-1 rounded-full bg-white/5 overflow-hidden">
        <motion.div
          initial={{ width: "0%" }}
          animate={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="h-full rounded-full gradient-primary relative"
        >
          <div className="absolute right-0 top-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-white glow-cyan" />
        </motion.div>
      </div>

      <p className="text-on-surface-variant/60 text-sm mt-4">
        This may take 30–60 seconds depending on video length
      </p>
    </motion.div>
  );
}
