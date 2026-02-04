import JobPageClient from "./JobPageClient";

export const dynamic = 'force-static';

export async function generateStaticParams(): Promise<Array<{ id: string }>> {
  // Return empty array for static export - routes will be handled client-side
  return [];
}

export default function JobPage() {
  return <JobPageClient />;
}
