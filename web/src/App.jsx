import { useState, useCallback, lazy, Suspense } from "react";
import { AnimatePresence, motion } from "framer-motion";
import Header from "./components/Header";
import DragDropZone from "./components/DragDropZone";
import LoadingState from "./components/LoadingState";
import ResultsDashboard from "./components/ResultsDashboard";
import FeatureStrip from "./components/FeatureStrip";

const SceneBackground = lazy(() => import("./components/SceneBackground"));

// App states: "idle" | "processing" | "results" | "error"

const pageTransition = {
  initial: { opacity: 0, y: 30, scale: 0.98, filter: "blur(8px)" },
  animate: { opacity: 1, y: 0, scale: 1, filter: "blur(0px)" },
  exit: { opacity: 0, y: -20, scale: 0.98, filter: "blur(6px)" },
  transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] },
};

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
      {/* Three.js 3D Background */}
      <Suspense fallback={null}>
        <SceneBackground />
      </Suspense>

      {/* Content */}
      <div className="relative z-10">
        <Header onReset={handleReset} showReset={appState !== "idle"} />

        <main className="px-4 sm:px-6 pb-20">
          <AnimatePresence mode="wait">
            {appState === "idle" && (
              <motion.div
                key="idle"
                {...pageTransition}
                className="pt-12 sm:pt-20"
              >
                {/* Hero text */}
                <div className="text-center mb-12 max-w-3xl mx-auto">
                  <motion.h1
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.7 }}
                    className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-tight"
                  >
                    Transform Your Videos Into{" "}
                    <span className="gradient-text">Captivating Captions</span>
                  </motion.h1>
                  <motion.p
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.15 }}
                    className="text-on-surface-variant text-lg mt-5 max-w-xl mx-auto"
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
                {...pageTransition}
                className="pt-20 sm:pt-32"
              >
                <LoadingState step={loadingStep} />
              </motion.div>
            )}

            {appState === "results" && (
              <motion.div
                key="results"
                {...pageTransition}
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
                {...pageTransition}
                className="pt-20 sm:pt-32 text-center max-w-lg mx-auto"
              >
                <div className="glass-card gradient-border rounded-2xl p-8">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-error/10 border border-error/20 flex items-center justify-center">
                    <span className="text-3xl">✕</span>
                  </div>
                  <h2 className="text-xl font-bold text-on-surface mb-2">
                    Something Went Wrong
                  </h2>
                  <p className="text-on-surface-variant text-sm mb-6">{errorMsg}</p>
                  <button
                    onClick={handleReset}
                    className="px-6 py-3 rounded-xl font-medium gradient-primary text-white magnetic-btn
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
