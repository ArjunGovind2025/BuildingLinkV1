"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ChevronDown, ChevronRight, Download, FileText, RefreshCw, ArrowLeft } from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/api";

type EvidenceRef = { timestamp?: number; transcript_excerpt?: string; screenshot_id?: string };
type ACCriterion = { id?: string; given?: string; when?: string; then?: string; and?: string[]; evidence_refs?: EvidenceRef[] };
type UserStory = { 
  id?: string; 
  title?: string; 
  persona?: string | string[]; 
  story_text?: string; 
  tags?: string[]; 
  description?: string; 
  evidence_refs?: EvidenceRef[]; 
  acceptance_criteria?: ACCriterion[] 
};
type JobResponse = {
  id: string;
  status: string;
  spec: {
    feature_summary?: string;
    user_stories?: UserStory[];
    open_questions?: string[];
    [k: string]: unknown;
  } | null;
  acceptance_criteria: { acceptance_criteria?: ACCriterion[] } | null;
  error_message?: string;
  transcript_segments?: number | null;
  screenshots_captured?: number | null;
  screenshots_analyzed?: number | null;
};

export default function JobPageClient() {
  const params = useParams();
  const jobId = typeof params?.id === "string" ? params.id : "";
  const [job, setJob] = useState<JobResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [expandedStories, setExpandedStories] = useState<Set<number>>(new Set());

  async function fetchJob() {
    if (!jobId) return null;
    const res = await fetch(`${API_BASE}/api/jobs/${jobId}`);
    if (!res.ok) throw new Error("Job not found");
    const data: JobResponse = await res.json();
    setJob(data);
    return data;
  }

  useEffect(() => {
    if (!jobId) {
      setLoading(false);
      setJob(null);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const data = await fetchJob();
        if (cancelled) return;
        if (data?.status === "pending" || data?.status === "processing") {
          const t = setInterval(async () => {
            const d = await fetch(`${API_BASE}/api/jobs/${jobId}`).then((r) => r.json());
            if (cancelled) return;
            setJob(d);
            if (d.status !== "pending" && d.status !== "processing") clearInterval(t);
          }, 2000);
          return () => clearInterval(t);
        }
      } catch {
        if (!cancelled) setJob(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [jobId]);

  async function regenerateAC() {
    setRegenerating(true);
    try {
      await fetch(`${API_BASE}/api/jobs/${jobId}/regenerate-ac`, { method: "POST" });
      await fetchJob();
    } finally {
      setRegenerating(false);
    }
  }

  function downloadExport(format: "md" | "json") {
    window.open(`${API_BASE}/api/jobs/${jobId}/export?format=${format}`, "_blank");
  }

  async function downloadTranscript(format: "txt" | "json") {
    const res = await fetch(`${API_BASE}/api/jobs/${jobId}/transcript?format=${format}`);
    if (!res.ok) throw new Error("Transcript not found");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `transcript-${jobId.slice(0, 8)}.${format}`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (loading && !job) {
    return (
      <main className="min-h-screen bg-background">
        <div className="container mx-auto max-w-4xl px-4 py-8">
          <p className="text-muted-foreground">Loading job…</p>
        </div>
      </main>
    );
  }
  if (!job) {
    return (
      <main className="min-h-screen bg-background">
        <div className="container mx-auto max-w-4xl px-4 py-8">
          <p>Job not found.</p>
          <Link href="/" className="text-primary hover:underline">Back to upload</Link>
        </div>
      </main>
    );
  }

  const spec = job.spec || {};
  const isComplete = job.status === "completed";
  // User stories now have nested acceptance_criteria
  const userStories = (spec.user_stories || []) as UserStory[];

  return (
    <main className="min-h-screen bg-background">
      <div className="container mx-auto max-w-4xl px-4 py-8">
        <div className="mb-6">
          <Link href="/" className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground mb-2">
            <ArrowLeft className="mr-1 h-4 w-4" />
            Back to upload
          </Link>
          <h1 className="text-2xl font-bold mb-2">Job {jobId.slice(0, 8)}</h1>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span className="font-medium">Status: {job.status}</span>
            {isComplete && (job.transcript_segments != null || job.screenshots_captured != null || job.screenshots_analyzed != null) && (
              <>
                <span>•</span>
                <span>Transcript: {job.transcript_segments ?? "—"} segments</span>
                <span>•</span>
                <span>Screenshots captured: {job.screenshots_captured ?? "—"}</span>
                <span>•</span>
                <span>Screenshots analyzed: {job.screenshots_analyzed ?? "—"}</span>
              </>
            )}
          </div>
          {job.error_message && (
            <div className="mt-3 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {job.error_message}
            </div>
          )}
        </div>

        {job.status === "pending" || job.status === "processing" ? (
          <Card>
            <CardContent className="pt-6">
              <p className="text-muted-foreground">Processing… (transcription, vision, spec extraction, acceptance criteria). This may take a few minutes.</p>
            </CardContent>
          </Card>
        ) : null}

        {isComplete && (
          <>
            <Card className="mb-6">
              <CardHeader>
                <CardTitle>Feature summary</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="whitespace-pre-wrap text-foreground">{spec.feature_summary || "—"}</p>
              </CardContent>
            </Card>

            <Card className="mb-6">
              <CardHeader>
                <div className="flex items-center justify-between flex-wrap gap-4">
                  <CardTitle>User stories & Acceptance criteria</CardTitle>
                  <Button onClick={regenerateAC} disabled={regenerating} size="sm" variant="outline">
                    <RefreshCw className={cn("mr-2 h-4 w-4", regenerating && "animate-spin")} />
                    {regenerating ? "Regenerating…" : "Regenerate AC"}
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {userStories.map((us, i) => {
                  const acs = us.acceptance_criteria || [];
                  const isOpen = expandedStories.has(i);
                  return (
                    <Collapsible key={i} open={isOpen} onOpenChange={() => {
                      setExpandedStories((prev) => {
                        const next = new Set(prev);
                        if (next.has(i)) next.delete(i);
                        else next.add(i);
                        return next;
                      });
                    }}>
                      <CollapsibleTrigger className="w-full">
                        <Card className="text-left hover:bg-accent/50 transition-colors">
                          <CardContent className="pt-6">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <h3 className="font-semibold text-lg mb-2">{us.title || `Story ${i + 1}`}</h3>
                                {us.persona && (
                                  <p className="text-sm text-muted-foreground mb-1">
                                    <strong>Persona:</strong> {Array.isArray(us.persona) ? us.persona.join(", ") : us.persona}
                                  </p>
                                )}
                                {us.story_text && (
                                  <p className="text-sm text-foreground mb-2 italic">{us.story_text}</p>
                                )}
                                {us.description && !us.story_text && (
                                  <p className="text-sm text-muted-foreground mb-2">{us.description}</p>
                                )}
                                {us.tags && us.tags.length > 0 && (
                                  <div className="flex flex-wrap gap-1 mb-2">
                                    {us.tags.map((tag, idx) => (
                                      <span key={idx} className="text-xs px-2 py-0.5 bg-primary/10 text-primary rounded">
                                        {tag}
                                      </span>
                                    ))}
                                  </div>
                                )}
                                {us.evidence_refs?.length ? (
                                  <p className="text-xs text-muted-foreground mb-1">
                                    Evidence: {us.evidence_refs.map((r) => `${r.timestamp}ms`).join(", ")}
                                  </p>
                                ) : null}
                                {acs.length > 0 && (
                                  <p className="text-xs text-primary font-medium mt-2">{acs.length} acceptance criteria</p>
                                )}
                              </div>
                              {isOpen ? <ChevronDown className="h-5 w-5 text-muted-foreground" /> : <ChevronRight className="h-5 w-5 text-muted-foreground" />}
                            </div>
                          </CardContent>
                        </Card>
                      </CollapsibleTrigger>
                      {acs.length > 0 && (
                        <CollapsibleContent>
                          <div className="ml-4 mt-2 space-y-3 border-l-2 border-border pl-4">
                            {acs.map((ac, acIdx) => (
                              <Card key={acIdx} className="bg-muted/30">
                                <CardContent className="pt-4">
                                  <h4 className="font-semibold mb-2">{ac.id || `AC${acIdx + 1}`}</h4>
                                  <div className="space-y-1 text-sm">
                                    <p><strong>GIVEN</strong> {ac.given}</p>
                                    <p><strong>WHEN</strong> {ac.when}</p>
                                    <p><strong>THEN</strong> {ac.then}</p>
                                    {ac.and && ac.and.length > 0 && (
                                      <>
                                        {ac.and.map((andItem, idx) => (
                                          <p key={idx}><strong>AND</strong> {andItem}</p>
                                        ))}
                                      </>
                                    )}
                                  </div>
                                  {ac.evidence_refs?.length ? (
                                    <div className="mt-3 space-y-2">
                                      <p className="text-xs font-medium text-muted-foreground">Evidence:</p>
                                      {ac.evidence_refs.map((r, j) => (
                                        <div key={j} className="flex items-start gap-3 text-xs text-muted-foreground">
                                          <img
                                            src={`${API_BASE}/api/jobs/${jobId}/screenshots/${r.screenshot_id}`}
                                            alt=""
                                            className="w-24 h-14 object-cover rounded border"
                                          />
                                          <span>{r.timestamp}ms — {String(r.transcript_excerpt || "").slice(0, 120)}…</span>
                                        </div>
                                      ))}
                                    </div>
                                  ) : null}
                                </CardContent>
                              </Card>
                            ))}
                          </div>
                        </CollapsibleContent>
                      )}
                    </Collapsible>
                  );
                })}
              </CardContent>
            </Card>

            {(spec.open_questions || []).length > 0 && (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Open questions</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                    {(spec.open_questions || []).map((q, i) => (
                      <li key={i}>{q}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}

            <Card className="mb-6">
              <CardHeader>
                <CardTitle>Transcript</CardTitle>
                <CardDescription>
                  Full timestamped transcript ({job.transcript_segments ?? 0} segments). Download as plain text or JSON.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex gap-2 flex-wrap">
                  <Button onClick={() => downloadTranscript("txt")} variant="outline" size="sm">
                    <FileText className="mr-2 h-4 w-4" />
                    Download transcript (TXT)
                  </Button>
                  <Button onClick={() => downloadTranscript("json")} variant="outline" size="sm">
                    <FileText className="mr-2 h-4 w-4" />
                    Download transcript (JSON)
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Export</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex gap-2 flex-wrap">
                  <Button onClick={() => downloadExport("md")} variant="outline" size="sm">
                    <Download className="mr-2 h-4 w-4" />
                    Download Markdown
                  </Button>
                  <Button onClick={() => downloadExport("json")} variant="outline" size="sm">
                    <Download className="mr-2 h-4 w-4" />
                    Download JSON (Jira/Linear)
                  </Button>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </main>
  );
}
