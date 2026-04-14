import * as React from "react"

import { cn } from "@/lib/utils"

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          "flex min-h-[80px] w-full rounded-lg border-0 bg-[#1f1f1f] px-4 py-3 text-sm text-white placeholder:text-[#7c7c7c] shadow-[rgb(18,18,18)_0px_1px_0px,rgb(124,124,124)_0px_0px_0px_1px_inset] focus-visible:outline-none focus-visible:shadow-[rgb(18,18,18)_0px_1px_0px,rgb(30,215,96)_0px_0px_0px_1px_inset] disabled:cursor-not-allowed disabled:opacity-50 transition-shadow duration-200 resize-y",
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
