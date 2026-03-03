import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-[16px] border-[2px] px-3 py-1 text-xs font-semibold transition-all duration-200 ease-out focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 active:scale-95",
  {
    variants: {
      variant: {
        default:
          "border-indigo-700 bg-gradient-to-b from-indigo-500 to-indigo-600 text-white shadow-[0_4px_0_0_#312E81,0_8px_12px_-4px_rgba(79,70,229,0.3)] hover:from-indigo-400 hover:to-indigo-500 hover:shadow-[0_4px_0_0_#3730A3,0_10px_16px_-2px_rgba(79,70,229,0.4)] hover:-translate-y-[1px] active:shadow-[0_2px_0_0_#312E81,0_4px_8px_-2px_rgba(79,70,229,0.2)] active:translate-y-[2px]",
        secondary:
          "border-indigo-400 bg-gradient-to-b from-indigo-200 to-indigo-300 text-indigo-900 shadow-[0_3px_0_0_#818CF8,0_6px_10px_-3px_rgba(129,140,248,0.2)] hover:from-indigo-100 hover:to-indigo-200 hover:shadow-[0_3px_0_0_#A5B4FC,0_8px_14px_-2px_rgba(129,140,248,0.3)] hover:-translate-y-[1px] active:shadow-[0_2px_0_0_#818CF8,0_4px_8px_-2px_rgba(129,140,248,0.15)] active:translate-y-[2px]",
        destructive:
          "border-red-700 bg-gradient-to-b from-red-500 to-red-600 text-white shadow-[0_4px_0_0_#991B1B,0_8px_12px_-4px_rgba(239,68,68,0.3)] hover:from-red-400 hover:to-red-500 hover:shadow-[0_4px_0_0_#B91C1C,0_10px_16px_-2px_rgba(239,68,68,0.4)] hover:-translate-y-[1px] active:shadow-[0_2px_0_0_#991B1B,0_4px_8px_-2px_rgba(239,68,68,0.2)] active:translate-y-[2px]",
        outline:
          "border-indigo-300 bg-white text-indigo-700 shadow-[0_2px_0_0_#C7D2FE,0_4px_8px_-3px_rgba(79,70,229,0.1)] hover:bg-indigo-50 hover:border-indigo-400 hover:shadow-[0_2px_0_0_#A5B4FC,0_6px_12px_-2px_rgba(79,70,229,0.15)] hover:-translate-y-[1px] active:shadow-[0_1px_0_0_#C7D2FE,0_3px_6px_-2px_rgba(79,70,229,0.08)] active:translate-y-[2px] active:bg-white dark:border-indigo-700 dark:bg-indigo-950 dark:text-indigo-200 dark:hover:bg-indigo-900 dark:hover:border-indigo-600 dark:shadow-[0_2px_0_0_#312E81,0_4px_8px_-3px_rgba(79,70,229,0.2)] dark:hover:shadow-[0_2px_0_0_#4338CA,0_6px_12px_-2px_rgba(99,102,241,0.3)]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
