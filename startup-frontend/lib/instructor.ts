// import OpenAI from 'openai'
// import { z } from 'zod'
// import Instructor from '@instructor-ai/instructor'

// const QueryTypeSchema = z.enum(['SINGLE', 'MERGE_MULTIPLE_RESPONSES'])

// const oai = new OpenAI({
//   apiKey: process.env.OPENAI_API_KEY
// })
// type QueryPlan = {
//   query_graph: Query[]
// }

// type Query = {
//   id: number
//   question: string
//   dependencies?: number[]
//   node_type: 'SINGLE' | 'MERGE_MULTIPLE_RESPONSES'
// }
// const QuerySchema = z.object({
//   id: z.number(),
//   question: z.string(),
//   dependencies: z.array(z.number()).optional(),
//   node_type: QueryTypeSchema.default('SINGLE')
// })

// const QueryPlanSchema = z.object({
//   query_graph: z.array(QuerySchema)
// })

// const client = Instructor({
//   client: oai,
//   mode: 'TOOLS'
// })

// const createQueryPlan = async (
//   question: string
// ): Promise<QueryPlan | undefined> => {
//   const extractionStream = await client.chat.completions.create({
//     messages: [{ role: 'user', content: textBlock }],
//     model: 'gpt-4-1106-preview',
//     response_model: {
//       schema: ExtractionValuesSchema,
//       name: 'value extraction'
//     },
//     max_retries: 3,
//     stream: true,
//     seed: 1
//   })

//   for await (const result of extractionStream) {
//     try {
//       console.clear()
//       console.log(result)
//     } catch (e) {
//       console.log(e)
//       break
//     }
//   }

//   const queryPlan: QueryPlan = await client.chat.completions.create({
//     messages: [
//       {
//         role: 'system',
//         content:
//           'You are a world class query planning algorithm capable of breaking apart questions into its dependency queries such that the answers can be used to inform the parent question. Do not answer the questions, simply provide a correct compute graph with good specific questions to ask and relevant dependencies. Before you call the function, think step-by-step to get a better understanding of the problem.',
//         query_graph: [] // Add an empty query_graph array
//       },
//       {
//         role: 'user',
//         content: `Consider: ${question}\nGenerate the correct query plan.`
//       }
//     ],
//     model: 'gpt-4-1106-preview',
//     response_model: { name: 'query-plan', schema: QueryPlanSchema },
//     max_tokens: 1000,
//     temperature: 0.0,
//     max_retries: 2
//   })

//   return queryPlan || undefined
// }

// const getQueryPlan = (query: string) => createQueryPlan(query)
// export default getQueryPlan
