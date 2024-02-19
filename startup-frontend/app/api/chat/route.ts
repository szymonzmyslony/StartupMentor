import { auth } from '@/auth'
import {
  AIStream,
  AIStreamCallbacksAndOptions,
  AIStreamParser,
  OpenAIStream,
  StreamingTextResponse
} from 'ai'

import { runConversation } from '@/lib/agent'

export async function POST(req: Request) {
  const json = await req.json()
  const { messages, previewToken } = json
  const userId = (await auth())?.user.id

  if (!userId) {
    return new Response('Unauthorized', {
      status: 401
    })
  }
  return runConversation(messages as any, async completion => {})
}
