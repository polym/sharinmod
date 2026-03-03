import * as React from "react"

import { cn } from "@/lib/utils"

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          "clay-input flex min-h-[80px] w-full rounded-xl border-2 border-indigo-200/50 bg-gradient-to-br from-white to-indigo-50/30 px-4 py-3 text-sm text-indigo-900 placeholder:text-indigo-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-offset-2 focus-visible:border-indigo-300 disabled:cursor-not-allowed disabled:opacity-50 shadow-[inset_2px_2px_4px_rgba(79,70,229,0.05),inset_-2px_-2px_4px_rgba(255,255,255,0.8)] transition-all duration-200",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Textarea.displayName = "Textarea"

export { Textarea }
