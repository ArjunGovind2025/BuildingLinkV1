"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Upload } from "lucide-react";

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
    setError(null);
    setUploading(true);
    try {
      const form = new FormData();
      form.append("video", file);
      const res = await fetch("/api/jobs", {
        method: "POST",
        body: form,
      });
      if (!res.ok) {
        const t = await res.text();
        throw new Error(t || res.statusText);
      }
      const job: JobStatus = await res.json();
      router.push(`/jobs/${job.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
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
                <Label htmlFor="video">Video (MP4 or WebM, max 500MB)</Label>
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
                <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                  {error}
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
