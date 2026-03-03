"use client";

import * as React from "react";
import * as CheckboxPrimitive from "@radix-ui/react-checkbox";
import { CheckIcon } from "lucide-react";

import { cn } from "@/lib/utils";

function Checkbox({
  className,
  ...props
}: React.ComponentProps<typeof CheckboxPrimitive.Root>) {
  return (
    <CheckboxPrimitive.Root
      data-slot="checkbox"
      className={cn(
        "peer border-2 border-indigo-300 bg-white data-[state=checked]:bg-gradient-to-br data-[state=checked]:from-indigo-400 data-[state=checked]:to-indigo-500 data-[state=checked]:text-white data-[state=checked]:border-indigo-500 focus-visible:border-indigo-400 focus-visible:ring-indigo-400/50 aria-invalid:ring-red-500/20 aria-invalid:border-red-500 h-5 w-5 shrink-0 rounded-lg shadow-[0_2px_4px_rgba(79,70,229,0.1),inset_0_1px_2px_rgba(79,70,229,0.05)] transition-all duration-200 outline-none focus-visible:ring-2 disabled:cursor-not-allowed disabled:opacity-50 hover:border-indigo-400 data-[state=checked]:shadow-[0_2px_4px_rgba(79,70,229,0.2)]",
        className,
      )}
      {...props}
    >
      <CheckboxPrimitive.Indicator
        data-slot="checkbox-indicator"
        className="flex items-center justify-center text-current transition-none"
      >
        <CheckIcon className="h-3.5 w-3.5" />
      </CheckboxPrimitive.Indicator>
    </CheckboxPrimitive.Root>
  );
}

export { Checkbox };
