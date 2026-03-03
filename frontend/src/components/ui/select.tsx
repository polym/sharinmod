import * as React from "react"
import * as SelectPrimitive from "@radix-ui/react-select"
import { Check, ChevronDown, ChevronUp } from "lucide-react"

import { cn } from "@/lib/utils"

const Select = SelectPrimitive.Root

const SelectGroup = SelectPrimitive.Group

const SelectValue = SelectPrimitive.Value

const SelectTrigger = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Trigger>
>(({ className, children, ...props }, ref) => (
  <SelectPrimitive.Trigger
    ref={ref}
    className={cn(
      "flex h-12 w-full items-center justify-between rounded-[20px] border-[3px] border-indigo-300 bg-white px-4 py-3 text-sm text-gray-950 shadow-[0_4px_0_0_#C7D2FE,0_8px_16px_-4px_rgba(79,70,229,0.15),inset_0_2px_4px_rgba(255,255,255,0.5)] placeholder:text-indigo-400 focus:outline-none focus:shadow-[0_4px_0_0_#A5B4FC,0_10px_20px_-2px_rgba(79,70,229,0.2),inset_0_2px_4px_rgba(255,255,255,0.8)] focus:border-indigo-500 disabled:cursor-not-allowed disabled:opacity-50 [&>span]:line-clamp-1 dark:border-indigo-700 dark:bg-indigo-950 dark:text-gray-50 dark:placeholder:text-indigo-500 dark:shadow-[0_4px_0_0_#312E81,0_8px_16px_-4px_rgba(79,70,229,0.2),inset_0_2px_4px_rgba(99,102,241,0.1)] dark:focus:border-indigo-400 dark:focus:shadow-[0_4px_0_0_#4338CA,0_10px_20px_-2px_rgba(99,102,241,0.3),inset_0_2px_4px_rgba(99,102,241,0.15)]",
      className
    )}
    {...props}
  >
    {children}
    <SelectPrimitive.Icon asChild>
      <ChevronDown className="h-4 w-4 opacity-50" />
    </SelectPrimitive.Icon>
  </SelectPrimitive.Trigger>
))
SelectTrigger.displayName = SelectPrimitive.Trigger.displayName

const SelectScrollUpButton = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.ScrollUpButton>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.ScrollUpButton>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.ScrollUpButton
    ref={ref}
    className={cn(
      "flex cursor-default items-center justify-center py-1",
      className
    )}
    {...props}
  >
    <ChevronUp className="h-4 w-4" />
  </SelectPrimitive.ScrollUpButton>
))
SelectScrollUpButton.displayName = SelectPrimitive.ScrollUpButton.displayName

const SelectScrollDownButton = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.ScrollDownButton>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.ScrollDownButton>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.ScrollDownButton
    ref={ref}
    className={cn(
      "flex cursor-default items-center justify-center py-1",
      className
    )}
    {...props}
  >
    <ChevronDown className="h-4 w-4" />
  </SelectPrimitive.ScrollDownButton>
))
SelectScrollDownButton.displayName =
  SelectPrimitive.ScrollDownButton.displayName

const SelectContent = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Content>
>(({ className, children, position = "popper", ...props }, ref) => (
  <SelectPrimitive.Portal>
    <SelectPrimitive.Content
      ref={ref}
      className={cn(
        "relative z-50 max-h-96 min-w-[8rem] overflow-hidden rounded-[24px] border-[3px] border-indigo-200 bg-white text-gray-950 shadow-[0_6px_0_0_#C7D2FE,0_12px_24px_-8px_rgba(79,70,229,0.25),inset_0_2px_4px_rgba(255,255,255,0.8)] data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 dark:border-indigo-800 dark:bg-indigo-950 dark:text-gray-50 dark:shadow-[0_6px_0_0_#312E81,0_12px_24px_-8px_rgba(79,70,229,0.35),inset_0_2px_4px_rgba(99,102,241,0.1)]",
        position === "popper" &&
          "data-[side=bottom]:translate-y-1 data-[side=left]:-translate-x-1 data-[side=right]:translate-x-1 data-[side=top]:-translate-y-1",
        className
      )}
      position={position}
      {...props}
    >
      <SelectScrollUpButton />
      <SelectPrimitive.Viewport
        className={cn(
          "p-2",
          position === "popper" &&
            "h-[var(--radix-select-trigger-height)] w-full min-w-[var(--radix-select-trigger-width)]"
        )}
      >
        {children}
      </SelectPrimitive.Viewport>
      <SelectScrollDownButton />
    </SelectPrimitive.Content>
  </SelectPrimitive.Portal>
))
SelectContent.displayName = SelectPrimitive.Content.displayName

const SelectLabel = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Label>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Label>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.Label
    ref={ref}
    className={cn("py-1.5 pl-8 pr-2 text-sm font-semibold", className)}
    {...props}
  />
))
SelectLabel.displayName = SelectPrimitive.Label.displayName

const SelectItem = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Item>
>(({ className, children, ...props }, ref) => (
  <SelectPrimitive.Item
    ref={ref}
    className={cn(
      "relative flex w-full cursor-pointer select-none items-center rounded-[16px] py-2.5 pl-8 pr-3 text-sm font-medium outline-none transition-all duration-150 ease-out focus:bg-indigo-50 focus:text-indigo-900 hover:bg-indigo-100 hover:text-indigo-900 data-[disabled]:pointer-events-none data-[disabled]:opacity-50 data-[state=checked]:bg-indigo-100 data-[state=checked]:text-indigo-900 active:scale-98 dark:focus:bg-indigo-900 dark:focus:text-indigo-100 dark:hover:bg-indigo-800 dark:hover:text-indigo-100 dark:data-[state=checked]:bg-indigo-800 dark:data-[state=checked]:text-indigo-100",
      className
    )}
    {...props}
  >
    <span className="absolute left-3 flex h-4 w-4 items-center justify-center rounded-full bg-white shadow-sm dark:bg-indigo-950">
      <SelectPrimitive.ItemIndicator>
        <Check className="h-3 w-3 text-indigo-600 dark:text-indigo-400" />
      </SelectPrimitive.ItemIndicator>
    </span>

    <SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>
  </SelectPrimitive.Item>
))
SelectItem.displayName = SelectPrimitive.Item.displayName

const SelectSeparator = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Separator>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Separator>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.Separator
    ref={ref}
    className={cn("-mx-2 my-2 h-px bg-indigo-200 dark:bg-indigo-800", className)}
    {...props}
  />
))
SelectSeparator.displayName = SelectPrimitive.Separator.displayName

export {
  Select,
  SelectGroup,
  SelectValue,
  SelectTrigger,
  SelectContent,
  SelectLabel,
  SelectItem,
  SelectSeparator,
  SelectScrollUpButton,
  SelectScrollDownButton,
}
