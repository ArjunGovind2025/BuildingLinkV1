/**
 * Firebase Cloud Functions for BuildingLink.
 * - api: Proxies /api/* to your backend (Railway, etc.). Set BACKEND_URL in Firebase config.
 */
import { onRequest } from "firebase-functions/v2/https";
import fetch from "node-fetch";

/**
 * Proxies all /api/* requests to the backend URL.
 * Set BACKEND_URL in Firebase Console → Functions → Environment variables (e.g. https://your-app.up.railway.app)
 */
export const api = onRequest(
  {
    cors: true,
    timeoutSeconds: 300,
    memory: "512MiB",
  },
  async (req, res) => {
    const backend = (process.env.BACKEND_URL || "").replace(/\/$/, "");
    if (!backend) {
      res.status(500).json({
        error: "Backend not configured",
        message: "Set BACKEND_URL in Firebase Console → Functions → Environment variables.",
      });
      return;
    }

    const path = req.path.startsWith("/api") ? req.path : `/api${req.path}`;
    const url = `${backend}${path}${req.url.includes("?") ? req.url.slice(req.url.indexOf("?")) : ""}`;

    try {
      const headers = { ...req.headers };
      delete headers.host;
      delete headers["content-length"];

      const opts = {
        method: req.method,
        headers,
        redirect: "manual",
      };
      // Use rawBody for uploads (multipart), otherwise body
      if (req.method !== "GET" && req.method !== "HEAD") {
        if (req.rawBody) {
          opts.body = req.rawBody;
        } else if (req.body !== undefined) {
          opts.body = typeof req.body === "string" ? req.body : JSON.stringify(req.body);
        }
      }

      const backendRes = await fetch(url, opts);
      const contentType = backendRes.headers.get("content-type");
      if (contentType) res.setHeader("Content-Type", contentType);
      backendRes.headers.forEach((v, k) => {
        const low = k.toLowerCase();
        if (low !== "content-type" && low !== "transfer-encoding") res.setHeader(k, v);
      });
      res.status(backendRes.status);
      const buffer = await backendRes.buffer();
      res.send(buffer);
    } catch (err) {
      console.error("Proxy error:", err);
      res.status(502).json({ error: "Bad Gateway", message: String(err.message) });
    }
  }
);
