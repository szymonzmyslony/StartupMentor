// utils/agent.ts

import { getEmbedding, createChatCompletion } from '@/lib/openAIUtils'
import getSupabase from '@/lib/supabase'
import { OpenAIStream } from 'ai'
import OpenAI from 'openai'
import { ChatCompletionChunk, FunctionDefinition } from 'openai/resources'
import {
  ChatCompletionMessage,
  ChatCompletionMessageParam,
  ChatCompletionSystemMessageParam,
  ChatCompletionTool
} from 'openai/resources/chat/completions'

const system_message: ChatCompletionSystemMessageParam = {
  role: 'system',
  content:
    "As a mentor for a burgeoning entrepreneur, approach each query with a dynamic and adaptable mindset. Begin with a foundational three-step query plan: 1) 'First Principles' to understand the core concepts; 2) 'Solution Frameworks' to identify strategic approaches; and 3) 'Examples' to illustrate these strategies in real-world scenarios. Recognize that this plan may not fit all inquiries, so be prepared to tailor your approach accordingly. When conducting semantic embedding-based searches, it's crucial to vary your phrasing and explore different perspectives to unearth a rich array of resources. If the information provided seems lacking or the query too general, proactively seek further clarification. This will ensure your advice is not only grounded in diverse insights but also precisely customized to the entrepreneur's specific situation. Always leverage fetching insights from the knowledge base with the use of at least 2 diverse quries."
}

const tools: Array<ChatCompletionTool> = [
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

async function runConversation(currentMessages: Array<ChatCompletionMessage>) {
  const matchChunk = async ({
    query,
    topK = 4
  }: {
    query: string
    topK: number
  }) => {
    console.log('Calling the db with query', query)
    const supabase = getSupabase()
    const embedding = await getEmbedding(query)
    const chunks = await supabase.matchChunk(embedding, topK)
    const content = chunks.map(chunk => chunk.content).join('\n')
    return content
  }
  console.log('currentMessages', currentMessages)
  const messages: Array<ChatCompletionMessageParam> =
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
    tool_choice: 'auto' // auto is default, but we'll be explicit
  })

  const responseMessage = response.choices[0].message

  // Step 2: check if the model wanted to call a function
  const toolCalls = responseMessage.tool_calls || []
  if (responseMessage.tool_calls) {
    // Step 3: call the function
    // Note: the JSON response may not always be valid; be sure to handle errors
    const availableFunctions = {
      matchChunk: matchChunk
    } // only one function in this example, but you can have multiple
    messages.push(responseMessage) // extend conversation with assistant's reply
    for (const toolCall of toolCalls) {
      const functionName = toolCall.function.name
      // @ts-ignore
      const functionToCall = availableFunctions[functionName]
      const functionArgs = JSON.parse(toolCall.function.arguments)
      const functionResponse = await functionToCall(functionArgs)
      messages.push({
        tool_call_id: toolCall.id,
        role: 'tool',
        // @ts-ignore
        name: functionName,
        content: functionResponse
      }) // extend conversation with function response
    }
    const response = await openai.chat.completions.create({
      model: 'gpt-3.5-turbo-0125',
      messages: messages,
      stream: true
    })
    return response
    // get a new response from the model where it can see the function response
  }
  return await openai.chat.completions.create({
    model: 'gpt-3.5-turbo-0125',
    messages: messages,
    stream: true
  })
}

export { runConversation }
