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
const data = {
  messages: [{ role: 'user', content: 'How do i start a startup?' }]
}
export async function handler({ messages }: { messages: Message[] }) {
  const fetchResponse = await fetch('http://127.0.0.1:8000/ask', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream'
    },
    body: JSON.stringify(data)
  })

  const textStream = fetchResponse.body

  // const dataStream = fetchResponse.body
  //   ?.pipeThrough(new TextDecoderStream())
  //   .pipeThrough(loggingStream)

  if (!textStream) {
    throw new Error('No textStream stream')
  }

  return new experimental_StreamingReactResponse(textStream, {
    ui({ content, data }) {
      console.log('Content:', content, 'Data:', data)
      return (
        <div className="italic text-red-800">
          {data &&
            data.map((message: any, index: number) => (
              <StatusMessage key={index} text={message['text']} />
            ))}
        </div>
      )
    },
    data: new experimental_StreamData()
  })
}
