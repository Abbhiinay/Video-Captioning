import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";

const STEPS = [
  { label: "Uploading video", icon: "📤" },
  { label: "Extracting frames", icon: "🎞️" },
  { label: "Analyzing content", icon: "🔍" },
  { label: "Generating captions", icon: "✨" },
];

export default function LoadingState({ step = 0 }) {
  const progress = ((step + 1) / STEPS.length) * 100;

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="w-full max-w-2xl mx-auto flex flex-col items-center"
    >
      {/* Orbiting AI indicator */}
      <div className="relative w-36 h-36 mb-12">
        {/* Outer orbit ring */}
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
          className="absolute inset-0 rounded-full"
          style={{
            border: "1.5px solid transparent",
            borderTopColor: "rgba(124, 58, 237, 0.6)",
            borderRightColor: "rgba(6, 182, 212, 0.3)",
          }}
        />
        {/* Outer orbit particle */}
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
          className="absolute inset-0"
        >
          <div
            className="absolute w-2 h-2 rounded-full bg-primary"
            style={{ top: "0%", left: "50%", transform: "translate(-50%, -50%)", boxShadow: "0 0 10px rgba(124, 58, 237, 0.6)" }}
          />
        </motion.div>

        {/* Middle orbit ring */}
        <motion.div
          animate={{ rotate: -360 }}
          transition={{ duration: 7, repeat: Infinity, ease: "linear" }}
          className="absolute inset-4 rounded-full"
          style={{
            border: "1.5px solid transparent",
            borderBottomColor: "rgba(6, 182, 212, 0.5)",
            borderLeftColor: "rgba(124, 58, 237, 0.2)",
          }}
        />
        {/* Middle orbit particle */}
        <motion.div
          animate={{ rotate: -360 }}
          transition={{ duration: 7, repeat: Infinity, ease: "linear" }}
          className="absolute inset-4"
        >
          <div
            className="absolute w-1.5 h-1.5 rounded-full bg-secondary"
            style={{ bottom: "0%", left: "50%", transform: "translate(-50%, 50%)", boxShadow: "0 0 8px rgba(6, 182, 212, 0.6)" }}
          />
        </motion.div>

        {/* Inner orbit ring */}
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 5, repeat: Infinity, ease: "linear" }}
          className="absolute inset-8 rounded-full"
          style={{
            border: "1px solid transparent",
            borderTopColor: "rgba(251, 191, 36, 0.3)",
          }}
        />

        {/* Center pulse */}
        <motion.div
          animate={{
            scale: [1, 1.15, 1],
            boxShadow: [
              "0 0 30px rgba(124, 58, 237, 0.2), 0 0 60px rgba(124, 58, 237, 0.1)",
              "0 0 50px rgba(124, 58, 237, 0.4), 0 0 90px rgba(124, 58, 237, 0.15)",
              "0 0 30px rgba(124, 58, 237, 0.2), 0 0 60px rgba(124, 58, 237, 0.1)",
            ],
          }}
          transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }}
          className="absolute inset-10 rounded-full gradient-primary flex items-center justify-center"
        >
          <Sparkles className="w-7 h-7 text-white" />
        </motion.div>
      </div>

      {/* Progress steps — vertical timeline */}
      <div className="flex flex-col gap-1 w-full max-w-sm">
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
              className="flex items-center gap-3 relative"
            >
              {/* Timeline connector */}
              {i < STEPS.length - 1 && (
                <div className="absolute left-[18px] top-[40px] w-[2px] h-[20px]">
                  <div
                    className="w-full h-full rounded-full transition-all duration-500"
                    style={{
                      background: isDone
                        ? "linear-gradient(180deg, rgba(124, 58, 237, 0.6), rgba(6, 182, 212, 0.4))"
                        : "rgba(255, 255, 255, 0.06)",
                    }}
                  />
                </div>
              )}
              {/* Step content */}
              <div
                className={`flex items-center gap-3 w-full px-4 py-3 rounded-xl transition-all duration-300 ${
                  isActive
                    ? "glass-elevated"
                    : isDone
                    ? "glass-card"
                    : "bg-transparent"
                }`}
                style={
                  isActive
                    ? {
                        boxShadow: "0 0 30px rgba(124, 58, 237, 0.15)",
                      }
                    : undefined
                }
              >
                {/* Step indicator */}
                <div className="relative flex-shrink-0">
                  <div
                    className={`w-9 h-9 rounded-full flex items-center justify-center text-base transition-all duration-300 ${
                      isActive
                        ? "bg-primary-container/20 border border-primary/30"
                        : isDone
                        ? "bg-green-500/10 border border-green-500/20"
                        : "bg-white/3 border border-white/5"
                    }`}
                  >
                    {isDone ? (
                      <motion.span
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="text-green-400 text-sm"
                      >
                        ✓
                      </motion.span>
                    ) : (
                      <span>{s.icon}</span>
                    )}
                  </div>
                  {isActive && (
                    <motion.div
                      animate={{ scale: [1, 1.6, 1], opacity: [0.5, 0, 0.5] }}
                      transition={{ duration: 2, repeat: Infinity }}
                      className="absolute inset-0 rounded-full border border-primary/40"
                    />
                  )}
                </div>

                <span
                  className={`text-sm font-medium flex-1 ${
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
                    className="text-xs text-secondary font-mono"
                  >
                    •••
                  </motion.div>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Progress bar */}
      <div className="w-full max-w-sm mt-8 h-1.5 rounded-full bg-white/5 overflow-hidden relative">
        <motion.div
          initial={{ width: "0%" }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          className="h-full rounded-full relative"
          style={{
            background: "linear-gradient(90deg, #7c3aed, #06b6d4)",
          }}
        >
          {/* Glowing leading edge */}
          <div
            className="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 rounded-full"
            style={{
              background: "#67e8f9",
              boxShadow: "0 0 12px rgba(6, 182, 212, 0.6), 0 0 24px rgba(6, 182, 212, 0.3)",
            }}
          />
        </motion.div>
      </div>

      <p className="text-on-surface-variant/50 text-sm mt-5">
        This may take 30–60 seconds depending on video length
      </p>
    </motion.div>
  );
}
