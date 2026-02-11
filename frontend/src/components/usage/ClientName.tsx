'use client';

import Image from 'next/image';

interface ClientNameProps {
  client: string | null;
}

// Client name mapping (lowercase input to display name) - used for tooltip
const clientNameMap: Record<string, string> = {
  'zed': 'Zed',
  'claude-code': 'Claude-Code',
  'chrome': 'Chrome',
  'safari': 'Safari',
  'firefox': 'Firefox',
  'codex': 'Codex',
};

// Supported clients with PNG icons (prefer PNG over SVG)
const clientsWithPng = ['zed', 'claude-code', 'chrome', 'firefox', 'codex'];

// All known clients (used to determine if we should show unknown icon)
const knownClients = ['zed', 'claude-code', 'chrome', 'safari', 'firefox', 'codex'];

export function ClientName({ client }: ClientNameProps) {
  const clientKey = client?.toLowerCase() || '';
  const isKnownClient = knownClients.includes(clientKey);

  // Use 'unknown' for unknown clients, otherwise use the client key
  const iconKey = isKnownClient ? clientKey : 'unknown';
  const displayName = clientNameMap[clientKey] || client || 'Unknown';

  // Use PNG if available, otherwise fall back to SVG
  const hasPng = clientsWithPng.includes(iconKey);
  const logoPath = `/icons/clients/${iconKey}.${hasPng ? 'png' : 'svg'}`;

  return (
    <span className="inline-flex items-center">
      <Image
        src={logoPath}
        alt={displayName}
        width={20}
        height={20}
        className="rounded"
        title={displayName}
      />
    </span>
  );
}
