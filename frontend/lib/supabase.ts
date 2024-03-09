import { Database } from "@/database.types";
import { SupabaseClient, createClient } from "@supabase/supabase-js";
import { getEmbedding } from "./openaiutils";

class Supabase {
  client: SupabaseClient<Database>;
  constructor() {
    // @ts-ignore
    const supabaseUrl: string = process.env.NEXT_PUBLIC_SUPABASE_URL;
    // @ts-ignore
    const supabaseAnonKey: string = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
    this.client = createClient<Database>(supabaseUrl, supabaseAnonKey);
  }

  // Match chunks based on query embedding
  matchChunks = async (queries: Array<string>, topK = 5) => {
    const embeddings = await getEmbedding(queries);
    const queryEmbeddings = embeddings.map((embedding) =>
      JSON.stringify(embedding.embedding)
    );

    try {
      const { data, error } = await this.client.rpc("match_multiple_chunks", {
        query_embeddings: queryEmbeddings,
        top_k: topK,
        match_threshold: 0.0,
      });

      if (error) throw new Error(error.message);
      const key_points = data
        ?.map((chunk) => chunk.chunk_key_points)
        .join("\n");

      return key_points;
    } catch (error) {
      console.error("Error in matchChunk:", error);
      throw error;
    }
  };

  // Match chunks within a specific document based on query embedding
  // matchChunkWithinDocument = async (
  //   documentId: number,
  //   queryEmbedding: Array<number>,
  //   topK = 10,
  //   matchThreshold = 0.0
  // ) => {
  //   try {
  //     const { data, error } = await this.client.rpc(
  //       "match_chunk_within_document",
  //       {
  //         p_document_id: documentId,
  //         query_embedding: JSON.stringify(queryEmbedding),
  //         top_k: topK,
  //         match_threshold: matchThreshold,
  //       }
  //     );

  //     if (error) throw new Error(error.message);
  //     return data;
  //   } catch (error) {
  //     console.error("Error in matchChunkWithinDocument:", error);
  //     throw error;
  //   }
  // };

  // Match documents based on query embedding
  // matchDocument = async (
  //   queryEmbedding: Array<number>,
  //   topK = 10,
  //   matchThreshold = 0.0
  // ) => {
  //   try {
  //     const { data, error } = await this.client.rpc("match_document", {
  //       query_embedding: JSON.stringify(queryEmbedding),
  //       top_k: topK,
  //       match_threshold: matchThreshold,
  //     });

  //     if (error) throw new Error(error.message);
  //     return data;
  //   } catch (error) {
  //     console.error("Error in matchDocument:", error);
  //     throw error;
  //   }
  // };
}

// Get child chunks of a document
const supabase = new Supabase();

const getSupabase = () => supabase;

export default getSupabase;
