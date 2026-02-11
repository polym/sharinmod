'use client';

import { useState } from 'react';
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

// Client Logo Tooltip component (consistent with ProviderLogoTooltip in ModelCard)
function ClientLogoTooltip({ displayName, children }: { displayName: string; children: React.ReactNode }) {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      {children}
      {showTooltip && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 bg-gray-900 text-white text-xs rounded whitespace-nowrap z-50 pointer-events-none">
          {displayName}
          <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900" />
        </div>
      )}
    </div>
  );
}

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
    <ClientLogoTooltip displayName={displayName}>
      <span className="inline-flex items-center">
        <Image
          src={logoPath}
          alt={displayName}
          width={20}
          height={20}
          className="rounded"
        />
      </span>
    </ClientLogoTooltip>
  );
}
