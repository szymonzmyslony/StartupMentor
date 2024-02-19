// utils/agent.ts

import { getEmbedding } from '@/lib/openAIUtils'
import getSupabase from '@/lib/supabase'
import {
  CreateMessage,
  OpenAIStream,
  StreamingTextResponse,
  ToolCallPayload,
  experimental_StreamData
} from 'ai'
import OpenAI from 'openai'
import { sleep } from 'openai/core'
import {
  ChatCompletionMessageParam,
  ChatCompletionSystemMessageParam,
  ChatCompletionTool
} from 'openai/resources/chat/completions'

const system_message: ChatCompletionSystemMessageParam = {
  role: 'system',
  content:
    'You are a world renowned tech startup mentor. Your job is to contextualize founder question based on their background. Think step-by-step, breaking down complex questions to understand the core issues, and real world situations. Then ask any nesssary follow up questions to get a clear and concise answer as well as return the query plan.'
}

const tools: ChatCompletionTool[] = [
  {
    type: 'function',
    function: {
      name: 'matchChunk',
      description: 'Fetches relavant document chunks based on question',
      parameters: {
        type: 'object',
        properties: {
          query: {
            type: 'string',
            description:
              'Query to match against the document chunks. The query should be a sentence or a paragraph that you want to find relevant chunks for'
          },
          topK: {
            type: 'number',
            description: 'How many chunks to retrieve'
          }
        },
        required: ['query']
      }
    }
  }
]
const matchChunk = async ({
  query,
  topK = 1
}: {
  query: string
  topK: number
}) => {
  const supabase = getSupabase()
  const embedding = await getEmbedding(query)
  const chunks = await supabase.matchChunk(embedding, 1)
  const content = chunks.map(chunk => chunk.content).join('\n')
  const urls: string[] = chunks.map(chunk => chunk.url)
  console.log('Calling tools, got, ', content, urls)
  return { content, sources: urls }
}

type AvailableFunctionsType = {
  [key: string]: (
    ...args: any[]
  ) => Promise<{ content: string; sources: string[] }>
}
const availableFunctions: AvailableFunctionsType = {
  matchChunk: matchChunk
}

async function runConversation(
  currentMessages: ChatCompletionMessageParam[],
  onCompletion: (completion: string) => void
): Promise<[ReadableStream<any>, experimental_StreamData]> {
  let messages = [system_message, ...currentMessages]

  const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY
  })
  const data = new experimental_StreamData()

  // Step 1: send the conversation and available functions to the model
  data.append({ text: 'Calling first endpoint' })

  const response = openai.chat.completions.create({
    model: 'gpt-3.5-turbo-0125',
    messages: messages,
    tools: tools,
    stream: true,
    tool_choice: 'auto' //{ type: 'function', function: { name: 'matchChunk' } } // auto is default, but we'll be explicit
  })
  data.append({ text: 'Finished first endpoint' })

  let finalMessages: (
    | OpenAI.Chat.Completions.ChatCompletionMessageParam
    | CreateMessage
  )[] = []
  data.append({ text: 'Getting into stream' })

  const stream = OpenAIStream(await response, {
    experimental_streamData: true,
    experimental_onToolCall: async (
      toolCallPayload: ToolCallPayload,
      appendToolCallMessage
    ) => {
      const inFeredtools = toolCallPayload.tools
      for (const toolCall of inFeredtools) {
        data.append({ text: `Need to call some tools` })

        const function_name = toolCall.func.name
        // @ts-ignore
        const functionArgs = JSON.parse(toolCall.func.arguments)
        const tool_call_id = toolCall.id
        const functionToCall = availableFunctions[function_name]

        const tool_call_result = await functionToCall(functionArgs)

        const { sources, content } = tool_call_result
        const sourcesText = sources.join(' ')

        appendToolCallMessage({
          tool_call_id,
          function_name,
          tool_call_result: content
        })
      }
      finalMessages = [...messages, ...appendToolCallMessage()]
      if (inFeredtools) {
        data.append({ text: `Finished callling tools` })
      }
      data.append({ text: `Making 2nd request` })

      const secondResponse = await openai.chat.completions.create({
        model: 'gpt-3.5-turbo-0125',
        // @ts-ignore
        messages: finalMessages,
        stream: true,
        tools: tools,
        tool_choice: 'auto'
      }) // get a new response from the model where it can see the function response
      return secondResponse
    },
    onStart() {
      console.log('started streaming')
    },
    onCompletion(completion) {
      onCompletion(completion)
    },
    onToken(token) {
      console.log('token is', token)
    },
    onFinal() {
      // IMPORTANT! you must close StreamData manually or the response will never finish.
      data.close()
    }

    // IMPORTANT! until this is stable, you must explicitly opt in to supporting streamData.
  })

  data.append({ text: `Returning promise` })

  return Promise.resolve([stream, data])
  // return new StreamingTextResponse(stream, {}, data)
}

export { runConversation }
