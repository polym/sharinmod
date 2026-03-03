import * as React from "react"

import { cn } from "@/lib/utils"

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-12 w-full rounded-[20px] border-[3px] border-indigo-300 bg-white px-4 py-3 text-sm text-gray-950 shadow-[0_4px_0_0_#C7D2FE,0_8px_16px_-4px_rgba(79,70,229,0.15),inset_0_2px_4px_rgba(255,255,255,0.5)] file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-indigo-400 focus-visible:outline-none focus-visible:shadow-[0_4px_0_0_#A5B4FC,0_10px_20px_-2px_rgba(79,70,229,0.2),inset_0_2px_4px_rgba(255,255,255,0.8)] focus-visible:border-indigo-500 disabled:cursor-not-allowed disabled:opacity-50 dark:border-indigo-700 dark:bg-indigo-950 dark:text-gray-50 dark:placeholder:text-indigo-500 dark:shadow-[0_4px_0_0_#312E81,0_8px_16px_-4px_rgba(79,70,229,0.2),inset_0_2px_4px_rgba(99,102,241,0.1)] dark:focus-visible:border-indigo-400 dark:focus-visible:shadow-[0_4px_0_0_#4338CA,0_10px_20px_-2px_rgba(99,102,241,0.3),inset_0_2px_4px_rgba(99,102,241,0.15)]",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input }
