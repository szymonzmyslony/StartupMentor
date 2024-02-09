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
import {
  ChatCompletionMessageParam,
  ChatCompletionSystemMessageParam,
  ChatCompletionTool
} from 'openai/resources/chat/completions'

const system_message: ChatCompletionSystemMessageParam = {
  role: 'system',
  content:
    "In responding to entrepreneurial queries, it's essential to leverage the full breadth of available resources. Beyond applying a dynamic and adaptable mindset, actively engage external tools to enrich your responses with diverse, up-to-date information. For each question, fetch additional data could refine or enhance the answer. When faced with broad or complex inquiries, prioritize the retrieval of external insights to provide well-rounded, evidence-based advice. This approach ensures each response is not only informed by a wide spectrum of sources but also tailored to the unique context of the entrepreneur's question. Clarity and conciseness remain key, even as we deepen our exploration through external data."
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
) {
  let messages = [system_message, ...currentMessages]

  const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY
  })
  const data = new experimental_StreamData()
  // Step 1: send the conversation and available functions to the model
  const response = await openai.chat.completions.create({
    model: 'gpt-3.5-turbo-0125',
    messages: messages,
    tools: tools,
    stream: true,
    tool_choice: 'auto' //{ type: 'function', function: { name: 'matchChunk' } } // auto is default, but we'll be explicit
  })
  let finalMessages: (
    | OpenAI.Chat.Completions.ChatCompletionMessageParam
    | CreateMessage
  )[] = []

  const stream = OpenAIStream(response, {
    experimental_streamData: true,
    experimental_onToolCall: async (
      toolCallPayload: ToolCallPayload,
      appendToolCallMessage
    ) => {
      const inFeredtools = toolCallPayload.tools
      for (const toolCall of inFeredtools) {
        const function_name = toolCall.func.name
        // @ts-ignore
        const functionArgs = JSON.parse(toolCall.func.arguments)
        const tool_call_id = toolCall.id
        const functionToCall = availableFunctions[function_name]
        const tool_call_result = await functionToCall(functionArgs)
        const { sources, content } = tool_call_result
        data.append({ text: 'chuj' })
        data.append({ sources: sources.join(' ') })
        console.log('Logging functionToCall tool_call_result', tool_call_result)
        console.log('==================================')
        appendToolCallMessage({
          tool_call_id,
          function_name,
          tool_call_result: content
        })
      }
      finalMessages = [...messages, ...appendToolCallMessage()]
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
    onCompletion(completion) {
      onCompletion(completion)
    },
    onFinal() {
      // IMPORTANT! you must close StreamData manually or the response will never finish.
      data.close()
    }
    // IMPORTANT! until this is stable, you must explicitly opt in to supporting streamData.
  })

  data.append({
    text: 'Hello, how are you?'
  })
  return new StreamingTextResponse(stream, {}, data)
}

export { runConversation }
