'use server'

import OpenAI from 'openai'
import {
  OpenAIStream,
  experimental_StreamingReactResponse,
  Message,
  AIStream,
  experimental_StreamData
} from 'ai'
import { runConversation } from '@/lib/agent'
import { StatusMessage } from '@/components/StatusMessage'

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY!
})

export async function handler({ messages }: { messages: Message[] }) {
  const [stream, streamed_data] = await runConversation(
    messages as any,
    async completion => {}
  )
  return new experimental_StreamingReactResponse(stream, {
    ui({ content, data }) {
      return (
        <div className="italic text-red-800">
          {data &&
            data.map((message: any, index: number) => (
              <StatusMessage key={index} text={message['text']} />
            ))}
        </div>
      )
    },
    data: streamed_data
  })
}
