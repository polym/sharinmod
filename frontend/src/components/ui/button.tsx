import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap text-sm font-bold tracking-[1.4px] uppercase transition-all duration-200 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#1ed760] focus-visible:ring-offset-2 focus-visible:ring-offset-[#121212] disabled:pointer-events-none disabled:opacity-50 cursor-pointer [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "rounded-full bg-[#1ed760] text-black hover:bg-[#1fdf64] hover:scale-[1.02] active:scale-[0.98]",
        destructive:
          "rounded-full bg-[#f3727f] text-white hover:bg-[#f5868f] active:scale-[0.98]",
        outline:
          "rounded-full border border-[#7c7c7c] bg-transparent text-white hover:border-white hover:scale-[1.02] active:scale-[0.98]",
        secondary:
          "rounded-full bg-[#1f1f1f] text-white hover:bg-[#282828] active:scale-[0.98]",
        ghost:
          "rounded-full text-[#b3b3b3] hover:text-white hover:bg-[#1f1f1f] tracking-normal normal-case",
        link: "text-[#1ed760] underline-offset-4 hover:underline rounded-none tracking-normal normal-case font-normal",
      },
      size: {
        default: "h-10 px-8 py-2",
        sm: "h-8 px-4 py-1.5 text-xs",
        lg: "h-12 px-10 py-3 text-base tracking-[2px]",
        icon: "h-10 w-10 rounded-full tracking-normal",
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
