import JobPageClient from "./JobPageClient";

export async function generateStaticParams() {
  return [];
}

export default function JobPage() {
  return <JobPageClient />;
}
