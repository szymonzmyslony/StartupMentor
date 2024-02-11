import { kv } from '@vercel/kv'
import { CreateMessage, OpenAIStream, StreamingTextResponse } from 'ai'
import OpenAI from 'openai'

import { auth } from '@/auth'
import { nanoid } from '@/lib/utils'
import { runConversation } from '@/lib/agent'
import { ChatCompletionMessageParam } from 'openai/resources/chat/completions'

export const runtime = 'edge'

export async function POST(req: Request) {
  const json = await req.json()
  const { messages, previewToken } = json
  const userId = (await auth())?.user.id

  if (!userId) {
    return new Response('Unauthorized', {
      status: 401
    })
  }
  const onCompletion = async (completion: string) => {
    // console.log('In completion with completion string of ', completion)
    const final_messages = [
      ...messages,
      {
        content: completion,
        role: 'assistant'
      }
    ]
    // console.log('==================================\n\n')

    const title = json.messages[0].content.substring(0, 100)
    const id = json.id ?? nanoid()
    const createdAt = Date.now()
    const path = `/chat/${id}`
    const payload = {
      id,
      title,
      userId,
      createdAt,
      path,
      messages: final_messages
    }
    // await kv.hmset(`chat:${id}`, payload)
    // await kv.zadd(`user:chat:${userId}`, {
    //   score: createdAt,
    //   member: `chat:${id}`
    // })
  }
  return runConversation(messages, onCompletion)
}
