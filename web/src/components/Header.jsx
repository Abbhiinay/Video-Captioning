import { motion } from "framer-motion";
import { Sparkles, Video } from "lucide-react";

export default function Header({ onReset, showReset }) {
  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="w-full px-6 py-4 flex items-center justify-between max-w-[1440px] mx-auto"
    >
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl gradient-primary flex items-center justify-center glow-violet">
          <Video className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-xl font-bold tracking-tight text-on-surface flex items-center gap-2">
            Caption<span className="gradient-text">AI</span>
            <Sparkles className="w-4 h-4 text-secondary" />
          </h1>
        </div>
      </div>

      {showReset && (
        <motion.button
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          onClick={onReset}
          className="px-4 py-2 rounded-xl text-sm font-medium
                     bg-white/5 border border-white/10 text-on-surface-variant
                     hover:bg-white/10 hover:border-white/20
                     transition-all duration-200 cursor-pointer"
        >
          ← New Video
        </motion.button>
      )}
    </motion.header>
  );
}
