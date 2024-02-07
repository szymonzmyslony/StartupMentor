// utils/agent.ts

import { getEmbedding, createChatCompletion } from '@/lib/openAIUtils'
import getSupabase from '@/lib/supabase'

export const generateAgentResponse = async (
  messages: Array<{ role: string; content: string }>
) => {
  console.log(`Incoming message are ${messages.length}`)
  const userMessage = messages[messages.length - 1]
  console.log(`User message is ${JSON.stringify(userMessage)}`)

  const system_message = {
    role: 'system',
    content:
      'You are a start-up mentor and provide a great advice to a founder. Answer based on the context provided but do not assume that founder is a person from that context. Consider first principle thinking, tend to provide solution or problem frameworks rather than straight yes or no answers. Leverage  examples to explain the thinking.   Use simple and concise language like a silicon valley person would. Ask for more information if needed.'
  }

  const supabase = getSupabase()

  const embedding = await getEmbedding(userMessage.content)

  const chunks = await supabase.matchChunk(embedding)

  const retrieved_chunks =
    chunks.length > 0
      ? chunks.map(chunk => chunk.content).join('\n')
      : 'No relevant information found.'

  const new_message = ` Context information is below: ${retrieved_chunks}. Query: ${userMessage}. Answer:`
  const new_prompt = { role: 'user', content: new_message }
  const final_instructions =
    messages.length === 1
      ? [system_message, new_prompt]
      : [...messages, new_prompt]
  console.log(
    `Final instructions length are ${JSON.stringify(final_instructions)}`
  )
  const completion = await createChatCompletion(final_instructions)
  return completion
}
