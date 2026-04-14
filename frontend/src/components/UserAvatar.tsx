"use client"

import * as React from "react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"

export interface UserAvatarProps extends Omit<React.ComponentProps<typeof Avatar>, "children"> {
  email?: string | null
  name?: string | null
  avatar_url?: string | null
  "aria-label"?: string
}

/**
 * Single neutral color for dark theme avatar fallbacks.
 */
const AVATAR_COLORS = [
  "bg-[#282828]",
] as const

/**
 * Simple string hash function (DJB2 algorithm)
 * Produces deterministic hash values for consistent color selection
 * Uses >>> 0 to ensure 32-bit unsigned integer (prevents overflow issues)
 */
function getStringHash(str: string): number {
  let hash = 5381
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) + hash + str.charCodeAt(i)) >>> 0
  }
  return hash
}

/**
 * Maps email/name to a consistent color from the palette
 */
function getAvatarColor(identifier: string): string {
  const hash = getStringHash(identifier)
  return AVATAR_COLORS[hash % AVATAR_COLORS.length]
}

/**
 * Extracts the first character from name, or email before @ symbol
 * Prioritizes name over email, returns 'U' as fallback
 * Uses toUpperCase() with locale support for international characters
 */
function getInitial(name?: string | null, email?: string | null): string {
  if (name) {
    return name.trim().charAt(0).toLocaleUpperCase()
  }
  if (email) {
    const localPart = email.split("@")[0]
    if (localPart) {
      return localPart.trim().charAt(0).toLocaleUpperCase()
    }
  }
  return "U"
}

/**
 * Validates avatar_url to prevent XSS
 * Only allows http://, https://, and data:image/* protocols
 */
function isValidAvatarUrl(url: string): boolean {
  if (!url || url === "null" || url === "undefined" || url.trim() === "") {
    return false
  }
  const trimmed = url.trim()
  // Allow http/https URLs
  if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
    return true
  }
  // Allow data:image URLs (inline base64 images)
  if (trimmed.startsWith("data:image/")) {
    return true
  }
  return false
}

/**
 * UserAvatar component - displays user avatar with fallback to initial
 *
 * Features:
 * - Prioritizes name over email for initials
 * - Displays avatar_url if valid, otherwise shows colored initial
 * - Color is deterministically generated from email/name hash
 * - Supports custom sizing via className prop
 * - Includes accessibility via aria-label
 * - Validates avatar_url to prevent XSS
 * - Handles image loading errors via Radix UI's built-in fallback
 */
export const UserAvatar = React.forwardRef<
  React.ElementRef<typeof Avatar>,
  UserAvatarProps
>(({ email, name, avatar_url, className, "aria-label": ariaLabel, ...props }, ref) => {
  const [imageLoadFailed, setImageLoadFailed] = React.useState(false)
  const initial = getInitial(name, email)

  // Use name for both display and color if available, otherwise email
  const identifier = name || email
  const bgColor = identifier ? getAvatarColor(identifier) : "bg-[#282828]"

  // Validate and check avatar_url
  const hasValidAvatarUrl = !imageLoadFailed && avatar_url && isValidAvatarUrl(avatar_url)

  // Generate accessible label
  const accessibleLabel = ariaLabel || name || email || "User"

  return (
    <Avatar
      ref={ref}
      className={cn(className)}
      aria-label={accessibleLabel}
      {...props}
    >
      {hasValidAvatarUrl && (
        <AvatarImage
          src={avatar_url}
          alt={accessibleLabel}
          onLoadingStatusChange={(status) => {
            if (status === "error") {
              setImageLoadFailed(true)
            }
          }}
        />
      )}
      <AvatarFallback className={cn(bgColor, "text-[#b3b3b3] font-medium")}>
        {initial}
      </AvatarFallback>
    </Avatar>
  )
})

UserAvatar.displayName = "UserAvatar"
