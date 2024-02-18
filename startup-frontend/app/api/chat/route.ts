import { auth } from '@/auth'
import {
  AIStream,
  AIStreamCallbacksAndOptions,
  AIStreamParser,
  OpenAIStream,
  StreamingTextResponse
} from 'ai'
import { EventSourceParserStream } from 'eventsource-parser/stream'
import {
  createParser,
  type ParsedEvent,
  type ReconnectInterval
} from 'eventsource-parser'

const customParser: AIStreamParser = (data, options) => {
  console.log('Got to custom parser', data, options)
  console.log('Event type:', options.event) // Log the event type, if useful
  try {
    const parsedData = JSON.parse(data)
    console.log('Parsed Data:', parsedData)
    return parsedData.message || '' // Return the relevant part of the data
  } catch (error) {
    console.error('Error parsing JSON:', error)
    return // Return void in case of an error
  }
}
function MyCustomStream(
  res: Response,
  cb?: AIStreamCallbacksAndOptions
): ReadableStream {
  const resylt = res.body?.getReader()
  console.log('Result:', resylt)
  return AIStream(res, customParser, cb)
}

export async function POST(req: Request) {
  const json = await req.json()
  const { messages, previewToken } = json
  const userId = (await auth())?.user.id

  if (!userId) {
    return new Response('Unauthorized', {
      status: 401
    })
  }
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

  const eventStream = fetchResponse.body
    ?.pipeThrough(new TextDecoderStream()) // Decode binary stream to text
    .pipeThrough(loggingStream) // Log the decoded text
    .pipeThrough(new EventSourceParserStream())

  if (!eventStream) {
    return new Response('Failed to create event stream', {
      status: 500
    })
  }

  return new StreamingTextResponse(eventStream)
}
