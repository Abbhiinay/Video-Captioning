import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, Video, ArrowLeft } from "lucide-react";

export default function Header({ onReset, showReset }) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const handleMouseMove = useCallback((e) => {
    const btn = e.currentTarget;
    const rect = btn.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    btn.style.setProperty("--mouse-x", `${x}%`);
    btn.style.setProperty("--mouse-y", `${y}%`);
  }, []);

  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className={`sticky top-0 z-50 w-full px-6 py-4 navbar-glass ${scrolled ? "scrolled" : ""}`}
    >
      <div className="flex items-center justify-between max-w-[1440px] mx-auto">
        <div className="flex items-center gap-3">
          <motion.div
            className="w-10 h-10 rounded-xl gradient-primary flex items-center justify-center relative"
            animate={{
              boxShadow: [
                "0 0 20px rgba(124, 58, 237, 0.2)",
                "0 0 35px rgba(124, 58, 237, 0.4)",
                "0 0 20px rgba(124, 58, 237, 0.2)",
              ],
            }}
            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
          >
            <Video className="w-5 h-5 text-white" />
          </motion.div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-on-surface flex items-center gap-2">
              Caption<span className="gradient-text">AI</span>
              <Sparkles className="w-4 h-4 text-secondary" />
            </h1>
          </div>
        </div>

        <AnimatePresence>
          {showReset && (
            <motion.button
              initial={{ opacity: 0, scale: 0.9, x: 10 }}
              animate={{ opacity: 1, scale: 1, x: 0 }}
              exit={{ opacity: 0, scale: 0.9, x: 10 }}
              transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
              onClick={onReset}
              onMouseMove={handleMouseMove}
              className="magnetic-btn flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium
                         bg-white/5 border border-white/10 text-on-surface-variant
                         hover:bg-white/10 hover:border-white/20
                         transition-all duration-200 cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              New Video
            </motion.button>
          )}
        </AnimatePresence>
      </div>
    </motion.header>
  );
}
