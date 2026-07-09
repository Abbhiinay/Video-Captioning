import { useCallback } from "react";
import { motion } from "framer-motion";
import CaptionCard from "./CaptionCard";
import { Download, RotateCcw } from "lucide-react";

const STYLE_ORDER = ["formal", "sarcastic", "humorous_tech", "humorous_non_tech"];

export default function ResultsDashboard({ captions, fileName, onReset }) {
  const handleDownloadJSON = () => {
    const data = {
      fileName: fileName || "unknown",
      generatedAt: new Date().toISOString(),
      captions,
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `captions_${(fileName || "video").replace(/\.[^.]+$/, "")}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    // Defer revocation so the browser has time to initiate the download
    setTimeout(() => URL.revokeObjectURL(url), 150);
  };

  const handleBtnMouseMove = useCallback((e) => {
    const btn = e.currentTarget;
    const rect = btn.getBoundingClientRect();
    btn.style.setProperty("--mouse-x", `${((e.clientX - rect.left) / rect.width) * 100}%`);
    btn.style.setProperty("--mouse-y", `${((e.clientY - rect.top) / rect.height) * 100}%`);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="w-full max-w-5xl mx-auto"
    >
      {/* Section Header */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="text-center mb-10"
      >
        <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight gradient-text mb-3">
          Your Captions Are Ready
        </h2>
        {fileName && (
          <p className="text-on-surface-variant text-sm">
            Generated from{" "}
            <span className="text-secondary font-medium">{fileName}</span>
          </p>
        )}
      </motion.div>

      {/* 2x2 Caption Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {STYLE_ORDER.map((style, i) => (
          <CaptionCard
            key={style}
            style={style}
            caption={captions?.[style] || ""}
            index={i}
          />
        ))}
      </div>

      {/* Action Buttons */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.6 }}
        className="flex flex-col sm:flex-row items-center justify-center gap-4 mt-10"
      >
        <motion.button
          onClick={handleDownloadJSON}
          onMouseMove={handleBtnMouseMove}
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          className="magnetic-btn flex items-center gap-2 px-7 py-3.5 rounded-xl font-semibold
                     gradient-primary text-white
                     hover:brightness-110 transition-all duration-200 cursor-pointer"
        >
          <Download className="w-4 h-4" />
          Download as JSON
        </motion.button>
        <motion.button
          onClick={onReset}
          onMouseMove={handleBtnMouseMove}
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          className="magnetic-btn flex items-center gap-2 px-7 py-3.5 rounded-xl font-semibold
                     bg-white/5 border border-white/10 text-on-surface-variant
                     hover:bg-white/8 hover:border-white/20
                     transition-all duration-200 cursor-pointer"
        >
          <RotateCcw className="w-4 h-4" />
          Process Another Video
        </motion.button>
      </motion.div>
    </motion.div>
  );
}
