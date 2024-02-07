// utils/openAIUtils.ts

import OpenAI from 'openai'

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
})

export const getEmbedding = async (text: string): Promise<number[]> => {
  const response = await openai.embeddings.create({
    model: 'text-embedding-3-small',
    input: text
  })
  return response.data[0].embedding // Adjust based on the actual structure of the response
}

export const createChatCompletion = async (
  messages: any[],
  model: string = 'gpt-3.5-turbo-0125',
  temperature: number = 0.7
) => {
  return await openai.chat.completions.create({
    model,
    messages,
    temperature,
    stream: true
  })
}
