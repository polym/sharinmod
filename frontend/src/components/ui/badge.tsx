import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-3 py-1 text-xs font-bold tracking-[1.4px] uppercase transition-all duration-200 cursor-default",
  {
    variants: {
      variant: {
        default:
          "bg-[#1ed760] text-black",
        secondary:
          "bg-[#1f1f1f] text-[#b3b3b3] border border-[#4d4d4d]",
        destructive:
          "bg-[#f3727f] text-white",
        outline:
          "bg-transparent text-white border border-[#7c7c7c] hover:border-white tracking-normal normal-case",
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
