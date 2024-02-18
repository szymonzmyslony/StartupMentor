'use server'

import OpenAI from 'openai'
import {
  OpenAIStream,
  experimental_StreamingReactResponse,
  Message,
  AIStream
} from 'ai'
import { EventSourceParserStream } from 'eventsource-parser/stream'

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY!
})

export async function handler({ messages }: { messages: Message[] }) {
  // Request the OpenAI API for the response based on the prompt
  const data = {
    messages: [{ role: 'user', content: 'How do i start a startup?' }]
  }
  const fetchResponse = await fetch('http://127.0.0.1:8000/ask', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream'
    },
    body: JSON.stringify(data)
  })
  const loggingStream = new TransformStream({
    transform(chunk, controller) {
      console.log('Chunk from stream:', chunk)
      console.log(typeof chunk)
      controller.enqueue(chunk) // Pass the chunk along unchanged
    }
  })

  // const eventStream = fetchResponse.body
  //   ?.pipeThrough(new TextDecoderStream()) // Decode binary stream to text
  //   .pipeThrough(new EventSourceParserStream()) // Parse the SSE-formatted text
  // const ourStream = fetchResponse.body
  //   ? fetchResponse.body.pipeThrough(loggingStream)
  //   : null
  // if (!ourStream) {
  //   return new Response('Failed to create event stream', {
  //     status: 500
  //   })
  // }
  // }

  // Convert the response into a friendly text-stream
  const stream = OpenAIStream(fetchResponse, {
    onStart: async () => {
      console.log('Stream started')
    },
    onCompletion: async completion => {
      console.log('Completion completed', completion)
    },
    onFinal: async completion => {
      console.log('Stream completed', completion)
    },
    onToken: async token => {
      console.log('Token received', token)
    }
  })
  // Respond with the stream
  return new experimental_StreamingReactResponse(stream, {
    ui({ content, data }) {
      console.log('Content:', content, 'Data', data)
      return (
        <div className="italic text-red-800">
          {content} Visit Next.js docs at{' '}
          <a
            href="https://nextjs.org/docs"
            target="_blank"
            className="underline"
          >
            https://nextjs.org/docs
          </a>
        </div>
      )
    }
  })
}
