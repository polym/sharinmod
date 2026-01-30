"use client";

import * as React from "react";
import Link from "next/link";
import { Grid, Sparkles, Store, User } from "lucide-react";

export function Header() {
  return (
    <header className="bg-white border-b border-purple-100 px-8 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Grid className="w-5 h-5 text-gray-400" />
          <nav className="flex items-center gap-6 text-sm">
            <Link href="/" className="flex items-center gap-2 text-purple-600 font-medium">
              <Grid className="w-4 h-4" />
              Dashboard
            </Link>
            <Link href="#" className="flex items-center gap-2 text-gray-600 hover:text-purple-600">
              <Sparkles className="w-4 h-4" />
              What&apos;s New
            </Link>
            <Link href="#" className="flex items-center gap-2 text-gray-600 hover:text-purple-600">
              <Store className="w-4 h-4" />
              Resources
            </Link>
            <Link href="#" className="flex items-center gap-2 text-gray-600 hover:text-purple-600">
              <User className="w-4 h-4" />
              Account
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
}
