export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  public: {
    Tables: {
      chunks: {
        Row: {
          content: string | null
          document_id: number
          embedding: string | null
          id: number
          key_points: string[] | null
          key_questions: string[] | null
          order_index: number | null
          similar_chunks: number[] | null
          similar_docs: number[] | null
          title: string | null
        }
        Insert: {
          content?: string | null
          document_id: number
          embedding?: string | null
          id?: number
          key_points?: string[] | null
          key_questions?: string[] | null
          order_index?: number | null
          similar_chunks?: number[] | null
          similar_docs?: number[] | null
          title?: string | null
        }
        Update: {
          content?: string | null
          document_id?: number
          embedding?: string | null
          id?: number
          key_points?: string[] | null
          key_questions?: string[] | null
          order_index?: number | null
          similar_chunks?: number[] | null
          similar_docs?: number[] | null
          title?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "chunks_document_id_fkey"
            columns: ["document_id"]
            isOneToOne: false
            referencedRelation: "documents"
            referencedColumns: ["id"]
          }
        ]
      }
      documents: {
        Row: {
          embedding: string | null
          id: number
          key_points: string[] | null
          key_questions: string[] | null
          meta: Json | null
          similar_chunks: number[] | null
          similar_docs: number[] | null
          summary: string | null
          title: string | null
          url: string | null
        }
        Insert: {
          embedding?: string | null
          id?: number
          key_points?: string[] | null
          key_questions?: string[] | null
          meta?: Json | null
          similar_chunks?: number[] | null
          similar_docs?: number[] | null
          summary?: string | null
          title?: string | null
          url?: string | null
        }
        Update: {
          embedding?: string | null
          id?: number
          key_points?: string[] | null
          key_questions?: string[] | null
          meta?: Json | null
          similar_chunks?: number[] | null
          similar_docs?: number[] | null
          summary?: string | null
          title?: string | null
          url?: string | null
        }
        Relationships: []
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      documents_by_key_points: {
        Args: {
          search_term: string
        }
        Returns: {
          title: string
        }[]
      }
      documents_by_key_questions: {
        Args: {
          search_term: string
        }
        Returns: {
          title: string
        }[]
      }
      get_child_chunks: {
        Args: {
          parent_id: number
        }
        Returns: {
          content: string | null
          document_id: number
          embedding: string | null
          id: number
          key_points: string[] | null
          key_questions: string[] | null
          order_index: number | null
          similar_chunks: number[] | null
          similar_docs: number[] | null
          title: string | null
        }[]
      }
      get_chunk_contents: {
        Args: {
          document_id_arg: number
        }
        Returns: unknown
      }
      get_chunks_by_document: {
        Args: {
          document_id_arg: number
        }
        Returns: {
          content: string
          id: number
        }[]
      }
      get_neighboring_chunks: {
        Args: {
          chunk_id: number
        }
        Returns: Json
      }
      get_parent_document: {
        Args: {
          chunk_id: number
        }
        Returns: {
          embedding: string | null
          id: number
          key_points: string[] | null
          key_questions: string[] | null
          meta: Json | null
          similar_chunks: number[] | null
          similar_docs: number[] | null
          summary: string | null
          title: string | null
          url: string | null
        }[]
      }
      hnswhandler: {
        Args: {
          "": unknown
        }
        Returns: unknown
      }
      insert_document_with_chunks: {
        Args: {
          doc_title: string
          doc_summary: string
          doc_url: string
          doc_meta: Json
          doc_embedding: string
          chunk_data: Json
        }
        Returns: number
      }
      ivfflathandler: {
        Args: {
          "": unknown
        }
        Returns: unknown
      }
      match_chunk: {
        Args: {
          query_embedding: string
          top_k?: number
          match_threshold?: number
        }
        Returns: Database["public"]["CompositeTypes"]["chunk_details"][]
      }
      match_chunk_within_document: {
        Args: {
          p_document_id: number
          query_embedding: string
          top_k?: number
          match_threshold?: number
        }
        Returns: {
          content: string | null
          document_id: number
          embedding: string | null
          id: number
          key_points: string[] | null
          key_questions: string[] | null
          order_index: number | null
          similar_chunks: number[] | null
          similar_docs: number[] | null
          title: string | null
        }[]
      }
      match_chunks_within_documents: {
        Args: {
          query_embedding: string
          k: number
          n: number
          match_threshold?: number
        }
        Returns: {
          chunks_array: Database["public"]["CompositeTypes"]["chunk_details"][]
        }[]
      }
      match_document: {
        Args: {
          query_embedding: string
          top_k?: number
          match_threshold?: number
        }
        Returns: {
          embedding: string | null
          id: number
          key_points: string[] | null
          key_questions: string[] | null
          meta: Json | null
          similar_chunks: number[] | null
          similar_docs: number[] | null
          summary: string | null
          title: string | null
          url: string | null
        }[]
      }
      match_multiple_chunks: {
        Args: {
          query_embeddings: string[]
          top_k: number
          match_threshold: number
        }
        Returns: Database["public"]["CompositeTypes"]["match_result"][]
      }
      update_similarity: {
        Args: Record<PropertyKey, never>
        Returns: undefined
      }
      vector_avg: {
        Args: {
          "": number[]
        }
        Returns: string
      }
      vector_dims: {
        Args: {
          "": string
        }
        Returns: number
      }
      vector_norm: {
        Args: {
          "": string
        }
        Returns: number
      }
      vector_out: {
        Args: {
          "": string
        }
        Returns: unknown
      }
      vector_send: {
        Args: {
          "": string
        }
        Returns: string
      }
      vector_typmod_in: {
        Args: {
          "": unknown[]
        }
        Returns: number
      }
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      chunk_details: {
        content: string
        order_index: number
        title: string
        url: string
        summary: string
        chunks_count: number
      }
      match_result: {
        content: string
        chunk_key_points: unknown
        document_key_points: unknown
        title: string
        url: string
      }
    }
  }
}

export type Tables<
  PublicTableNameOrOptions extends
    | keyof (Database["public"]["Tables"] & Database["public"]["Views"])
    | { schema: keyof Database },
  TableName extends PublicTableNameOrOptions extends { schema: keyof Database }
    ? keyof (Database[PublicTableNameOrOptions["schema"]]["Tables"] &
        Database[PublicTableNameOrOptions["schema"]]["Views"])
    : never = never
> = PublicTableNameOrOptions extends { schema: keyof Database }
  ? (Database[PublicTableNameOrOptions["schema"]]["Tables"] &
      Database[PublicTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : PublicTableNameOrOptions extends keyof (Database["public"]["Tables"] &
      Database["public"]["Views"])
  ? (Database["public"]["Tables"] &
      Database["public"]["Views"])[PublicTableNameOrOptions] extends {
      Row: infer R
    }
    ? R
    : never
  : never

export type TablesInsert<
  PublicTableNameOrOptions extends
    | keyof Database["public"]["Tables"]
    | { schema: keyof Database },
  TableName extends PublicTableNameOrOptions extends { schema: keyof Database }
    ? keyof Database[PublicTableNameOrOptions["schema"]]["Tables"]
    : never = never
> = PublicTableNameOrOptions extends { schema: keyof Database }
  ? Database[PublicTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : PublicTableNameOrOptions extends keyof Database["public"]["Tables"]
  ? Database["public"]["Tables"][PublicTableNameOrOptions] extends {
      Insert: infer I
    }
    ? I
    : never
  : never

export type TablesUpdate<
  PublicTableNameOrOptions extends
    | keyof Database["public"]["Tables"]
    | { schema: keyof Database },
  TableName extends PublicTableNameOrOptions extends { schema: keyof Database }
    ? keyof Database[PublicTableNameOrOptions["schema"]]["Tables"]
    : never = never
> = PublicTableNameOrOptions extends { schema: keyof Database }
  ? Database[PublicTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : PublicTableNameOrOptions extends keyof Database["public"]["Tables"]
  ? Database["public"]["Tables"][PublicTableNameOrOptions] extends {
      Update: infer U
    }
    ? U
    : never
  : never

export type Enums<
  PublicEnumNameOrOptions extends
    | keyof Database["public"]["Enums"]
    | { schema: keyof Database },
  EnumName extends PublicEnumNameOrOptions extends { schema: keyof Database }
    ? keyof Database[PublicEnumNameOrOptions["schema"]]["Enums"]
    : never = never
> = PublicEnumNameOrOptions extends { schema: keyof Database }
  ? Database[PublicEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : PublicEnumNameOrOptions extends keyof Database["public"]["Enums"]
  ? Database["public"]["Enums"][PublicEnumNameOrOptions]
  : never
