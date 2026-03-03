import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap text-sm font-semibold transition-all duration-200 ease-out focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50 active:scale-[0.97] active:shadow-[0_2px_8px_rgba(79,70,229,0.15)] active:translate-y-[1px] [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "rounded-[20px] border-b-[4px] border-indigo-800 bg-gradient-to-b from-indigo-500 to-indigo-600 text-white shadow-[0_8px_0_0_#312E81,0_12px_20px_-4px_rgba(79,70,229,0.4)] hover:from-indigo-400 hover:to-indigo-500 hover:shadow-[0_8px_0_0_#3730A3,0_14px_24px_-2px_rgba(79,70,229,0.5)] hover:-translate-y-[1px] active:border-b-[2px] active:shadow-[0_4px_0_0_#312E81,0_6px_12px_-2px_rgba(79,70,229,0.3)] active:translate-y-[3px]",
        destructive:
          "rounded-[20px] border-b-[4px] border-red-800 bg-gradient-to-b from-red-500 to-red-600 text-white shadow-[0_8px_0_0_#991B1B,0_12px_20px_-4px_rgba(239,68,68,0.4)] hover:from-red-400 hover:to-red-500 hover:shadow-[0_8px_0_0_#B91C1C,0_14px_24px_-2px_rgba(239,68,68,0.5)] hover:-translate-y-[1px] active:border-b-[2px] active:shadow-[0_4px_0_0_#991B1B,0_6px_12px_-2px_rgba(239,68,68,0.3)] active:translate-y-[3px]",
        outline:
          "rounded-[20px] border-[3px] border-indigo-300 bg-white text-indigo-700 shadow-[0_4px_0_0_#C7D2FE,0_8px_16px_-4px_rgba(79,70,229,0.15)] hover:bg-indigo-50 hover:border-indigo-400 hover:shadow-[0_4px_0_0_#A5B4FC,0_10px_20px_-2px_rgba(79,70,229,0.2)] hover:-translate-y-[1px] active:border-b-[2px] active:shadow-[0_2px_0_0_#C7D2FE,0_4px_8px_-2px_rgba(79,70,229,0.1)] active:translate-y-[2px] active:bg-white dark:border-indigo-700 dark:bg-indigo-950 dark:text-indigo-200 dark:hover:bg-indigo-900 dark:hover:border-indigo-600 dark:shadow-[0_4px_0_0_#312E81,0_8px_16px_-4px_rgba(79,70,229,0.3)] dark:hover:shadow-[0_4px_0_0_#3730A3,0_10px_20px_-2px_rgba(99,102,241,0.4)]",
        secondary:
          "rounded-[20px] border-b-[4px] border-indigo-400 bg-gradient-to-b from-indigo-300 to-indigo-400 text-indigo-900 shadow-[0_6px_0_0_#818CF8,0_10px_18px_-4px_rgba(129,140,248,0.3)] hover:from-indigo-200 hover:to-indigo-300 hover:shadow-[0_6px_0_0_#A5B4FC,0_12px_22px_-2px_rgba(129,140,248,0.4)] hover:-translate-y-[1px] active:border-b-[2px] active:shadow-[0_3px_0_0_#818CF8,0_5px_10px_-2px_rgba(129,140,248,0.2)] active:translate-y-[3px] dark:border-indigo-600 dark:from-indigo-700 dark:to-indigo-800 dark:text-indigo-100 dark:hover:from-indigo-600 dark:hover:to-indigo-700",
        ghost:
          "rounded-[20px] text-indigo-700 hover:bg-indigo-100 hover:shadow-[inset_0_2px_4px_rgba(79,70,229,0.1)] active:bg-indigo-200 dark:text-indigo-300 dark:hover:bg-indigo-900/50 dark:hover:shadow-[inset_0_2px_4px_rgba(99,102,241,0.2)]",
        link: "text-indigo-600 underline-offset-4 hover:underline dark:text-indigo-400 rounded-none border-0 shadow-none active:scale-100 active:shadow-none active:translate-y-0",
      },
      size: {
        default: "h-12 px-6 py-2.5",
        sm: "h-10 rounded-[16px] px-4 py-2 text-sm",
        lg: "h-14 rounded-[24px] px-10 py-3 text-base",
        icon: "h-12 w-12 rounded-[20px]",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
