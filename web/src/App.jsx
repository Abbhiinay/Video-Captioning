import { useState, useCallback, lazy, Suspense } from "react";
import { AnimatePresence, motion } from "framer-motion";
import Header from "./components/Header";
import DragDropZone from "./components/DragDropZone";
import LoadingState from "./components/LoadingState";
import ResultsDashboard from "./components/ResultsDashboard";
import FeatureStrip from "./components/FeatureStrip";

const SceneBackground = lazy(() => import("./components/SceneBackground"));

// App states: "idle" | "processing" | "results" | "error"

// In production the Vite proxy is not available, so we hit the backend directly.
const API_BASE = import.meta.env.VITE_API_URL ?? "";

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

    try {
      const xhr = new XMLHttpRequest();
      
      const uploadPromise = new Promise((resolve, reject) => {
        let processingTimers = [];
        let uploadFinished = false;
        
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            if (event.loaded < event.total) {
              setLoadingStep(0);
            } else if (!uploadFinished) {
              uploadFinished = true;
              setLoadingStep(1);
              // Start timers for processing steps only AFTER upload is complete
              processingTimers = [
                setTimeout(() => setLoadingStep(2), 6000),
                setTimeout(() => setLoadingStep(3), 15000),
              ];
            }
          }
        };

        xhr.onload = () => {
          processingTimers.forEach(clearTimeout);
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              resolve(JSON.parse(xhr.responseText));
            } catch (e) {
              reject(new Error("Invalid JSON response from server"));
            }
          } else {
            let detail = `Server error: ${xhr.status}`;
            try {
              detail = JSON.parse(xhr.responseText).detail || detail;
            } catch (e) {}
            reject(new Error(detail));
          }
        };

        xhr.onerror = () => {
          processingTimers.forEach(clearTimeout);
          reject(new Error("Network error. The upload took too long or was blocked."));
        };

        xhr.open("POST", `${API_BASE}/api/caption`);
        xhr.send(formData);
      });

      const data = await uploadPromise;
      setCaptions(data.captions || {});
      setAppState("results");
    } catch (err) {
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
