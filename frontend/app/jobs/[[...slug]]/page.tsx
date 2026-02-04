import JobPageClient from "./JobPageClient";

export async function generateStaticParams(): Promise<Array<{ slug?: string[] }>> {
  // Return at least one placeholder for static export validation
  // Actual routing is handled client-side
  return [{ slug: ['placeholder'] }];
}

export default function JobPage() {
  return <JobPageClient />;
}
