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

  const x_data = new experimental_StreamData()

  const aiStream = AIStream(fetchResponse, parseMyPythonStream(), {
    onStart: async () => {
      console.log('Stream started')
    },
    onCompletion: async completion => {
      console.log('Completion completed', completion)
      x_data.close()
    },
    onFinal: async completion => {
      console.log('Stream completed', completion)
    }
    // onToken: async token => {
    //   console.log('Token received', token)
    // }
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

function parseMyPythonStream(): AIStreamParser {
  return data => {
    const json = JSON.parse(data)

    if (json.event === 'text') {
      const text = json.value
      const Parsedtext = JSON.stringify(text)
      const formattedText = `0:${Parsedtext}\n`
      return formattedText
    }
    if (json.event === 'data') {
      const x_data = json.value
      return `2: ${x_data}\n`
    }
  }
}
