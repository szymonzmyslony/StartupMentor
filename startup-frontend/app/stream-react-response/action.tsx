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
import mentorParser from './mentorParser'
import { auth } from '@/auth'

export async function handler({ messages }: { messages: Message[] }) {
  const userId = (await auth())?.user.id
  console.log('User ID:', userId)

  if (!userId) {
    return new Response('Unauthorized', {
      status: 401
    })
  }

  const data = {
    messages
  }

  const fetchResponse = await fetch('http://127.0.0.1:8000/ask', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream'
    },
    body: JSON.stringify(data)
  })
  const headers = fetchResponse.headers

  console.log('Headers:', headers)

  const x_data = new experimental_StreamData()

  const aiStream = AIStream(fetchResponse, mentorParser(), {
    onStart: async () => {
      console.log('Stream started')
    },
    onCompletion: async completion => {
      x_data.close()
    },
    onFinal: async completion => {
      console.log('Stream completed')
    }
  })

  return new experimental_StreamingReactResponse(aiStream, {
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
    data: x_data
  })
}
