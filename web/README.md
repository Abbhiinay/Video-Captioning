# CaptionAI Web Client (React + Vite)

This is the interactive frontend for the AI Video Caption Generator. Built using React, TailwindCSS, and Framer Motion, it offers a visually stunning dashboard to drag-and-drop videos, monitor the extraction steps, and view generated captions in four distinct styles.

---

## Features

- **Drag and Drop Interface**: Easily upload `.mp4`, `.webm`, or `.mov` files.
- **Dynamic Progress Updates**: Visual indicators showing the steps of the analysis pipeline.
- **Stylized Results Dashboard**: Interactive cards displaying:
  - **Formal Caption** (Professional tone)
  - **Sarcastic Caption** (Dry irony)
  - **Humorous Tech Caption** (Software engineering metaphors)
  - **Humorous Non-Tech Caption** (Everyday situational humor)
  - **Video Understanding** (Identified camera motion and apparent emotion)

---

## Local Development & Setup

### 1. Prerequisites
Ensure you have [Node.js](https://nodejs.org/) installed on your machine.

### 2. Install Dependencies
From the `web/` directory, run:
```bash
npm install
```

### 3. Run the Development Server
Start Vite:
```bash
npm run dev
```
Once started, open `http://localhost:5173/` in your browser.

---

## API Proxy Configuration

To prevent Cross-Origin Resource Sharing (CORS) errors during development, Vite is configured to proxy all `/api` traffic directly to the FastAPI server running on port `8000`.

This setup is defined in [vite.config.js](file:///c:/Users/ktony/Desktop/HTML/Video-Captioning/web/vite.config.js):
```javascript
server: {
  proxy: {
    "/api": {
      target: "http://localhost:8000",
      changeOrigin: true,
    },
  },
},
```

Make sure your FastAPI server is running on `http://127.0.0.1:8000` (refer to the main [README.md](file:///c:/Users/ktony/Desktop/HTML/Video-Captioning/README.md) for backend instructions) so that the proxy resolves successfully.
