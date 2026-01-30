"use client";

import * as React from "react";
import Link from "next/link";
import { User } from "lucide-react";

export function Header() {
  // Simplified header per requirements: removed unnecessary nav links, kept only account avatar for settings access
  return (
    <header className="bg-white border-b border-purple-100 px-8 py-4">
      <div className="flex items-center justify-between">
        <Link href="/settings" className="flex items-center justify-center w-8 h-8 bg-purple-100 hover:bg-purple-200 rounded-full transition-colors">
          <User className="w-4 h-4 text-purple-600" />
        </Link>
      </div>
    </header>
  );
}
