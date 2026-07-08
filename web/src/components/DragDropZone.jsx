import { useState, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, Film, X, CloudUpload } from "lucide-react";

const ACCEPTED_TYPES = ["video/mp4", "video/webm", "video/quicktime", "video/x-msvideo"];
const MAX_SIZE_MB = 100;
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;

export default function DragDropZone({ onFileSelect, isUploading }) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  const validateFile = useCallback((file) => {
    if (!file) return "No file selected.";
    if (!ACCEPTED_TYPES.includes(file.type)) {
      return `Unsupported format. Please upload MP4, WebM, or MOV.`;
    }
    if (file.size > MAX_SIZE_BYTES) {
      return `File too large (${(file.size / 1024 / 1024).toFixed(1)}MB). Max ${MAX_SIZE_MB}MB.`;
    }
    return null;
  }, []);

  const handleFile = useCallback(
    (file) => {
      const err = validateFile(file);
      if (err) {
        setError(err);
        setSelectedFile(null);
        return;
      }
      setError(null);
      setSelectedFile(file);
    },
    [validateFile]
  );

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragOver(false);
      const file = e.dataTransfer.files?.[0];
      handleFile(file);
    },
    [handleFile]
  );

  const handleInputChange = useCallback(
    (e) => {
      const file = e.target.files?.[0];
      handleFile(file);
    },
    [handleFile]
  );

  const clearFile = useCallback(() => {
    setSelectedFile(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  }, []);

  const handleGenerate = useCallback(() => {
    if (selectedFile && onFileSelect) {
      onFileSelect(selectedFile);
    }
  }, [selectedFile, onFileSelect]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.7, delay: 0.2 }}
      className="w-full max-w-2xl mx-auto"
    >
      {/* Upload Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !selectedFile && inputRef.current?.click()}
        className={`upload-zone rounded-2xl p-12 flex flex-col items-center justify-center
                    text-center cursor-pointer transition-all duration-300 relative overflow-hidden
                    ${isDragOver ? "drag-over" : ""}
                    ${selectedFile ? "border-secondary/50" : ""}
                    ${isUploading ? "pointer-events-none opacity-60" : ""}`}
      >
        {/* Ambient glow background */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 rounded-full bg-primary-container/5 blur-3xl" />
        </div>

        <input
          ref={inputRef}
          type="file"
          accept="video/mp4,video/webm,video/quicktime"
          onChange={handleInputChange}
          className="hidden"
          id="video-upload-input"
        />

        <AnimatePresence mode="wait">
          {selectedFile ? (
            <motion.div
              key="selected"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="flex flex-col items-center gap-4 relative z-10"
            >
              <div className="w-16 h-16 rounded-2xl bg-secondary/10 border border-secondary/20 flex items-center justify-center">
                <Film className="w-8 h-8 text-secondary" />
              </div>
              <div>
                <p className="text-on-surface font-medium text-lg">{selectedFile.name}</p>
                <p className="text-on-surface-variant text-sm mt-1">
                  {(selectedFile.size / 1024 / 1024).toFixed(1)} MB
                </p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  clearFile();
                }}
                className="flex items-center gap-1 text-sm text-on-surface-variant hover:text-error transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" /> Remove
              </button>
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="flex flex-col items-center gap-4 relative z-10"
            >
              <motion.div
                animate={{ y: [0, -6, 0] }}
                transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                className="w-16 h-16 rounded-2xl bg-primary-container/10 border border-primary-container/20 flex items-center justify-center"
              >
                <CloudUpload className="w-8 h-8 text-primary" />
              </motion.div>
              <div>
                <p className="text-on-surface font-medium text-lg">
                  Drag & drop your video here
                </p>
                <p className="text-on-surface-variant text-sm mt-1">
                  or click to browse
                </p>
              </div>
              <div className="flex items-center gap-2 mt-2">
                {["MP4", "WebM", "MOV"].map((fmt) => (
                  <span
                    key={fmt}
                    className="px-3 py-1 rounded-lg text-xs font-medium bg-white/5 border border-white/10 text-on-surface-variant"
                  >
                    {fmt}
                  </span>
                ))}
                <span className="px-3 py-1 rounded-lg text-xs font-medium bg-tertiary-container/20 border border-tertiary/20 text-tertiary">
                  {MAX_SIZE_MB}MB max
                </span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Error */}
      <AnimatePresence>
        {error && (
          <motion.p
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="text-error text-sm mt-3 text-center"
          >
            {error}
          </motion.p>
        )}
      </AnimatePresence>

      {/* Generate Button */}
      <motion.button
        onClick={handleGenerate}
        disabled={!selectedFile || isUploading}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className={`w-full mt-6 py-4 rounded-xl text-white font-semibold text-lg
                    transition-all duration-300 cursor-pointer
                    ${
                      selectedFile && !isUploading
                        ? "gradient-primary glow-violet hover:brightness-110"
                        : "bg-white/5 text-on-surface-variant cursor-not-allowed"
                    }`}
      >
        {isUploading ? (
          <span className="flex items-center justify-center gap-2">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full"
            />
            Processing…
          </span>
        ) : (
          <span className="flex items-center justify-center gap-2">
            <Upload className="w-5 h-5" />
            Generate Captions
          </span>
        )}
      </motion.button>
    </motion.div>
  );
}
