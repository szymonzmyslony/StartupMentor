'use server'

import OpenAI from 'openai'
import {
  OpenAIStream,
  experimental_StreamingReactResponse,
  Message,
  AIStream,
  experimental_StreamData,
  AIStreamParser
} from 'ai'
import { StatusMessage } from '@/components/StatusMessage'

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY!
})
const data = {
  messages: [{ role: 'user', content: 'How do i start a startup?' }]
}

function wrapStreamWithCompletion(
  originalStream: ReadableStream<any>,
  onComplete: () => Promise<void>
) {
  const reader = originalStream.getReader()

  return new ReadableStream({
    async pull(controller) {
      const { done, value } = await reader.read()
      if (done) {
        // When the stream is finished, call the onComplete callback
        onComplete()
        // Close the controller to finish the ReadableStream
        controller.close()
        return
      }
      // Enqueue the chunk so it can be read from the new stream
      controller.enqueue(value)
    },
    cancel() {
      // If the stream is cancelled, we should also call the onComplete callback
      onComplete()
    }
  })
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

  const x_data = new experimental_StreamData()

  const textStream = fetchResponse.body

  if (!textStream) {
    throw new Error('Failed to connect to the server')
  }
  const aiStream = wrapStreamWithCompletion(textStream, async () => {
    x_data.close()
  })

  return new experimental_StreamingReactResponse(aiStream, {
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
    data: x_data
  })
}
