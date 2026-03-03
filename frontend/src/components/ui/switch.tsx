"use client"

import * as React from "react"
import * as SwitchPrimitives from "@radix-ui/react-switch"

import { cn } from "@/lib/utils"

const Switch = React.forwardRef<
  React.ElementRef<typeof SwitchPrimitives.Root>,
  React.ComponentPropsWithoutRef<typeof SwitchPrimitives.Root>
>(({ className, ...props }, ref) => (
  <SwitchPrimitives.Root
    className={cn(
      "peer inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-indigo-200/50 transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-offset-2 focus-visible:ring-offset-white disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-gradient-to-r data-[state=checked]:from-indigo-400 data-[state=checked]:to-indigo-500 data-[state=unchecked]:bg-indigo-50 shadow-[0_2px_4px_rgba(79,70,229,0.1),inset_0_1px_2px_rgba(79,70,229,0.05)] data-[state=checked]:shadow-[0_2px_4px_rgba(79,70,229,0.2),inset_0_-1px_2px_rgba(0,0,0,0.1)] dark:focus-visible:ring-indigo-500 dark:focus-visible:ring-offset-gray-950 dark:data-[state=checked]:from-indigo-500 dark:data-[state=checked]:to-indigo-600 dark:data-[state=unchecked]:bg-indigo-950",
      className
    )}
    {...props}
    ref={ref}
  >
    <SwitchPrimitives.Thumb
      className={cn(
        "pointer-events-none block h-5 w-5 rounded-full bg-white shadow-md data-[state=checked]:translate-x-5 data-[state=unchecked]:translate-x-0 transition-transform duration-200 border-2 border-indigo-100 data-[state=checked]:border-indigo-200"
      )}
    />
  </SwitchPrimitives.Root>
))
Switch.displayName = SwitchPrimitives.Root.displayName

export { Switch }
