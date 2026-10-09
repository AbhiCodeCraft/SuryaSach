import { SystemDetail } from "@/components/system-detail";

export default async function SystemPage({ params }: { params: Promise<{ systemId: string }> }) {
  const { systemId } = await params;
  return <SystemDetail key={systemId} systemId={systemId} />;
}
