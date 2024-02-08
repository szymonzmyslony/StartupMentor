// utils/agent.ts

import { getEmbedding } from '@/lib/openAIUtils'
import getSupabase from '@/lib/supabase'
import {
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
    "As a mentor for a burgeoning entrepreneur, approach each query with a dynamic and adaptable mindset. Begin with a foundational three-step query plan: 1) 'First Principles' to understand the core concepts; 2) 'Solution Frameworks' to identify strategic approaches; and 3) 'Examples' to illustrate these strategies in real-world scenarios. Recognize that this plan may not fit all inquiries, so be prepared to tailor your approach accordingly. When conducting semantic embedding-based searches, it's crucial to vary your phrasing and explore different perspectives to unearth a rich array of resources. If the information provided seems lacking or the query too general, proactively seek further clarification. This will ensure your advice is not only grounded in diverse insights but also precisely customized to the entrepreneur's specific situation. Always leverage fetching insights from the knowledge base with the use of at least 2 diverse quries."
}

const tools: ChatCompletionTool[] = [
  {
    type: 'function',
    function: {
      name: 'matchChunk',
      description: 'Gets relavant document chunks based on query',
      parameters: {
        type: 'object',
        properties: {
          query: {
            type: 'string',
            description:
              'Query against start-up knowledge based. You can ask about first principles, examples, or problem frameworks.'
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
const matchChunk = async (args: Record<string, unknown>) => {
  const topK = 3

  const query: string = args['query']
  const supabase = getSupabase()
  const embedding = await getEmbedding(query)
  const chunks = await supabase.matchChunk(embedding, topK)
  const content = chunks.map(chunk => chunk.content).join('\n')

  return content
}

type AvailableFunctionsType = {
  [key: string]: (...args: any[]) => any
}
const availableFunctions: AvailableFunctionsType = {
  matchChunk: matchChunk
}

async function runConversation(
  currentMessages: ChatCompletionMessageParam[],
  onCompletion: (completion: string) => void
) {
  let messages =
    currentMessages.length > 1
      ? currentMessages
      : [system_message, currentMessages[0]]

  const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY
  })

  // Step 1: send the conversation and available functions to the model
  const response = await openai.chat.completions.create({
    model: 'gpt-3.5-turbo-0125',
    messages: messages,
    tools: tools,
    stream: true,
    tool_choice: 'auto' // auto is default, but we'll be explicit
  })
  const data = new experimental_StreamData()

  const stream = OpenAIStream(response, {
    experimental_onToolCall: async (
      toolCallPayload: ToolCallPayload,
      appendToolCallMessage
    ) => {
      data.append({
        text: 'Some custom data'
      })

      const tools = toolCallPayload.tools
      for (const toolCall of tools) {
        const function_name = toolCall.func.name
        // @ts-ignore
        const functionArgs = JSON.parse(toolCall.func.arguments)
        const tool_call_id = toolCall.id
        const functionToCall = availableFunctions[function_name]
        const tool_call_result = functionToCall(functionArgs)

        appendToolCallMessage({
          tool_call_id,
          function_name,
          tool_call_result
        })
      }
      const finalMessages = [...messages, ...appendToolCallMessage()]
      const secondResponse = await openai.chat.completions.create({
        model: 'gpt-3.5-turbo-0125',
        messages: finalMessages,
        stream: true
      }) // get a new response from the model where it can see the function response
      return secondResponse
    },
    onCompletion(completion) {
      onCompletion(completion)
    },
    onFinal(completion) {
      // IMPORTANT! you must close StreamData manually or the response will never finish.
      data.close()
    },
    // IMPORTANT! until this is stable, you must explicitly opt in to supporting streamData.
    experimental_streamData: true
  })

  data.append({
    text: 'Hello, how are you?'
  })
  return new StreamingTextResponse(stream, {}, data)
}

export { runConversation }
