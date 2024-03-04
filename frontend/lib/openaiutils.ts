import OpenAI from "openai";
import { Embedding } from "openai/resources/embeddings.mjs";

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export const getEmbedding = async (
  texts: Array<string>
): Promise<Embedding[]> => {
  const response = await openai.embeddings.create({
    model: "text-embedding-3-small",
    input: texts,
  });
  return response.data; // Adjust based on the actual structure of the response
};
