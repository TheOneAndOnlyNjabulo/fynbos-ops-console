import type { Source } from "@/lib/chat-types"
import type { SupportResult } from "@/lib/support-types"

const API_URL = process.env.NEXT_PUBLIC_API_URL

export type ChatApiResponse = {
  answer: string
  sources: Source[]
}

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export async function submitSupportEmail(emailText: string): Promise<SupportResult> {
  if (!API_URL) {
    throw new ApiError(0, "NEXT_PUBLIC_API_URL is not configured.")
  }

  let response: Response
  try {
    response = await fetch(`${API_URL}/support`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email_text: emailText }),
    })
  } catch {
    throw new ApiError(0, "Couldn't reach the ops console. Check your connection and try again.")
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = body?.detail
    throw new ApiError(response.status, detail ?? "Failed to process this email. Please try again.")
  }

  return response.json()
}

export async function sendChatMessage(question: string): Promise<ChatApiResponse> {
  if (!API_URL) {
    throw new ApiError(0, "NEXT_PUBLIC_API_URL is not configured.")
  }

  let response: Response
  try {
    response = await fetch(`${API_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    })
  } catch {
    throw new ApiError(0, "Couldn't reach the assistant. Check your connection and try again.")
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = body?.detail
    throw new ApiError(response.status, detail ?? "Failed to generate an answer. Please try again.")
  }

  return response.json()
}
