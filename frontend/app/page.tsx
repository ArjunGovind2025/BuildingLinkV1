"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Upload } from "lucide-react";
import { API_BASE } from "@/lib/api";

// Cloud Run has a 32MB max HTTP request size; larger uploads fail after ~20–30s with no clear error
const MAX_UPLOAD_BYTES = 32 * 1024 * 1024;

type JobStatus = {
  id: string;
  status: string;
  created_at: string;
  updated_at: string;
  error_message?: string;
};

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) {
      setError("Select a video file");
      return;
    }
    if (file.size > MAX_UPLOAD_BYTES) {
      setError(`File is too large (${(file.size / 1024 / 1024).toFixed(1)}MB). Maximum is 32MB.`);
      return;
    }
    setError(null);
    setUploading(true);
    const uploadUrl = `${API_BASE || ""}/api/jobs`;
    const fileSizeMB = (file.size / 1024 / 1024).toFixed(2);
    console.log("[upload] start", { url: uploadUrl, file: file.name, sizeBytes: file.size, sizeMB: fileSizeMB });
    try {
      const form = new FormData();
      form.append("video", file);
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5 * 60 * 1000); // 5 min for slow connections
      const res = await fetch(uploadUrl, {
        method: "POST",
        body: form,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      console.log("[upload] response", { status: res.status, ok: res.ok, statusText: res.statusText });
      if (!res.ok) {
        const t = await res.text();
        console.error("[upload] error body", t);
        throw new Error(`${res.status}: ${t || res.statusText}`);
      }
      const job: JobStatus = await res.json();
      console.log("[upload] success", job.id);
      router.push(`/jobs/${job.id}`);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Upload failed";
      const name = err instanceof Error ? err.name : "";
      console.error("[upload] failed", { name, message: msg, err });
      if (err instanceof Error) {
        if (err.name === "AbortError") {
          setError("Upload timed out. Try a smaller file (under 32MB) or a faster connection.");
        } else {
          setError(msg || "Upload failed");
        }
      } else {
        setError("Upload failed. Try a smaller file (under 32MB).");
      }
    } finally {
      setUploading(false);
    }
  }

  return (
    <main className="min-h-screen bg-background">
      <div className="container mx-auto max-w-2xl px-4 py-12">
        <Card>
          <CardHeader>
            <CardTitle className="text-3xl font-bold">Video to Acceptance Criteria</CardTitle>
            <CardDescription className="text-base">
              Upload a narrated screen recording. We extract transcript and screenshots on meaningful changes, then generate a feature spec and GIVEN/WHEN/THEN acceptance criteria with evidence.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="video">Video (MP4 or WebM, max 32MB)</Label>
                <Input
                  id="video"
                  type="file"
                  accept="video/mp4,video/webm"
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                  disabled={uploading}
                  className="cursor-pointer"
                />
              </div>
              {error && (
                <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive space-y-1">
                  <p>{error}</p>
                  <p className="text-muted-foreground text-xs">Open DevTools (F12) → Console to see request URL and server response.</p>
                </div>
              )}
              <Button type="submit" disabled={uploading || !file} className="w-full" size="lg">
                <Upload className="mr-2 h-4 w-4" />
                {uploading ? "Uploading…" : "Upload and process"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
