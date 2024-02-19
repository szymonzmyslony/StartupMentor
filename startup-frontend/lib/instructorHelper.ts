import Instructor from '@instructor-ai/instructor'
import OpenAI from 'openai'
import { z } from 'zod'

const QueryTypeSchema = z.enum(['SINGLE', 'MERGE_MULTIPLE_RESPONSES'])

const QuerySchema = z.object({
  id: z.number(),
  question: z.string(),
  dependencies: z.array(z.number()).optional(),
  node_type: QueryTypeSchema.default('SINGLE')
})

const QueryPlanSchema = z.object({
  query_graph: z.array(QuerySchema)
})
