import { useState, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";
import Header from "./components/Header";
import DragDropZone from "./components/DragDropZone";
import LoadingState from "./components/LoadingState";
import ResultsDashboard from "./components/ResultsDashboard";
import FeatureStrip from "./components/FeatureStrip";

// App states: "idle" | "processing" | "results" | "error"

export default function App() {
  const [appState, setAppState] = useState("idle");
  const [loadingStep, setLoadingStep] = useState(0);
  const [captions, setCaptions] = useState(null);
  const [fileName, setFileName] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  const handleFileSelect = useCallback(async (file) => {
    setAppState("processing");
    setLoadingStep(0);
    setFileName(file.name);
    setErrorMsg("");

    const formData = new FormData();
    formData.append("video", file);

    // Simulate step progression
    const stepTimers = [
      setTimeout(() => setLoadingStep(1), 2000),
      setTimeout(() => setLoadingStep(2), 6000),
      setTimeout(() => setLoadingStep(3), 10000),
    ];

    try {
      const response = await fetch("/api/caption", {
        method: "POST",
        body: formData,
      });

      stepTimers.forEach(clearTimeout);

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Server error: ${response.status}`);
      }

      const data = await response.json();
      setCaptions(data.captions || {});
      setAppState("results");
    } catch (err) {
      stepTimers.forEach(clearTimeout);
      console.error("Caption generation failed:", err);
      setErrorMsg(err.message || "Something went wrong. Please try again.");
      setAppState("error");
    }
  }, []);

  const handleReset = useCallback(() => {
    setAppState("idle");
    setCaptions(null);
    setFileName("");
    setErrorMsg("");
    setLoadingStep(0);
  }, []);

  return (
    <div className="min-h-screen bg-surface-dim relative overflow-hidden">
      {/* Ambient background blobs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full bg-primary-container/4 blur-[120px]" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] rounded-full bg-secondary/3 blur-[100px]" />
        <div className="absolute top-[40%] right-[20%] w-[300px] h-[300px] rounded-full bg-tertiary/2 blur-[80px]" />
      </div>

      {/* Content */}
      <div className="relative z-10">
        <Header onReset={handleReset} showReset={appState !== "idle"} />

        <main className="px-4 sm:px-6 pb-20">
          <AnimatePresence mode="wait">
            {appState === "idle" && (
              <motion.div
                key="idle"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.4 }}
                className="pt-12 sm:pt-20"
              >
                {/* Hero text */}
                <div className="text-center mb-12 max-w-3xl mx-auto">
                  <motion.h1
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.7 }}
                    className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight leading-tight"
                  >
                    Transform Your Videos Into{" "}
                    <span className="gradient-text">Captivating Captions</span>
                  </motion.h1>
                  <motion.p
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.15 }}
                    className="text-on-surface-variant text-lg mt-4"
                  >
                    AI-powered multi-style caption generation in seconds
                  </motion.p>
                </div>

                <DragDropZone onFileSelect={handleFileSelect} isUploading={false} />
                <FeatureStrip />
              </motion.div>
            )}

            {appState === "processing" && (
              <motion.div
                key="processing"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.4 }}
                className="pt-20 sm:pt-32"
              >
                <LoadingState step={loadingStep} />
              </motion.div>
            )}

            {appState === "results" && (
              <motion.div
                key="results"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.4 }}
                className="pt-10 sm:pt-16"
              >
                <ResultsDashboard
                  captions={captions}
                  fileName={fileName}
                  onReset={handleReset}
                />
              </motion.div>
            )}

            {appState === "error" && (
              <motion.div
                key="error"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.4 }}
                className="pt-20 sm:pt-32 text-center max-w-lg mx-auto"
              >
                <div className="glass-card rounded-2xl p-8">
                  <div className="text-4xl mb-4">😔</div>
                  <h2 className="text-xl font-bold text-on-surface mb-2">
                    Something Went Wrong
                  </h2>
                  <p className="text-on-surface-variant text-sm mb-6">{errorMsg}</p>
                  <button
                    onClick={handleReset}
                    className="px-6 py-3 rounded-xl font-medium gradient-primary text-white
                               hover:brightness-110 transition-all duration-200 cursor-pointer"
                  >
                    Try Again
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
