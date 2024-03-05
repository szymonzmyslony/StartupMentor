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
      cart_items: {
        Row: {
          id: number
          product_id: number
          quantity: number
          user_id: string
        }
        Insert: {
          id?: number
          product_id: number
          quantity: number
          user_id: string
        }
        Update: {
          id?: number
          product_id?: number
          quantity?: number
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "cart_items_product_id_fkey"
            columns: ["product_id"]
            isOneToOne: false
            referencedRelation: "products"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "cart_items_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          }
        ]
      }
      customers: {
        Row: {
          id: string
          stripe_customer_id: string | null
        }
        Insert: {
          id: string
          stripe_customer_id?: string | null
        }
        Update: {
          id?: string
          stripe_customer_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "customers_id_fkey"
            columns: ["id"]
            isOneToOne: true
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          }
        ]
      }
      locations: {
        Row: {
          address: string
          city: string | null
          id: number
          label: string | null
          postal_code: string
        }
        Insert: {
          address: string
          city?: string | null
          id?: number
          label?: string | null
          postal_code: string
        }
        Update: {
          address?: string
          city?: string | null
          id?: number
          label?: string | null
          postal_code?: string
        }
        Relationships: []
      }
      order_items: {
        Row: {
          id: number
          order_id: number
          price: number
          product_id: number
          quantity: number
          user_id: string
        }
        Insert: {
          id?: number
          order_id: number
          price: number
          product_id: number
          quantity: number
          user_id: string
        }
        Update: {
          id?: number
          order_id?: number
          price?: number
          product_id?: number
          quantity?: number
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "order_items_order_id_fkey"
            columns: ["order_id"]
            isOneToOne: false
            referencedRelation: "orders"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "order_items_product_id_fkey"
            columns: ["product_id"]
            isOneToOne: false
            referencedRelation: "products"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "order_items_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          }
        ]
      }
      orders: {
        Row: {
          created_at: string
          id: number
          location_id: number | null
          status: Database["public"]["Enums"]["order_status"]
          stripe_payment_id: string | null
          total: number
          user_address_id: number | null
          user_id: string
        }
        Insert: {
          created_at?: string
          id?: number
          location_id?: number | null
          status?: Database["public"]["Enums"]["order_status"]
          stripe_payment_id?: string | null
          total: number
          user_address_id?: number | null
          user_id: string
        }
        Update: {
          created_at?: string
          id?: number
          location_id?: number | null
          status?: Database["public"]["Enums"]["order_status"]
          stripe_payment_id?: string | null
          total?: number
          user_address_id?: number | null
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "orders_location_id_fkey"
            columns: ["location_id"]
            isOneToOne: false
            referencedRelation: "locations"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "orders_user_address_id_fkey"
            columns: ["user_address_id"]
            isOneToOne: false
            referencedRelation: "user_addresses"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "orders_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          }
        ]
      }
      products: {
        Row: {
          active: boolean | null
          description: string | null
          id: number
          image_link: string | null
          name: string
          price: number
          priority: number
          unit_description: string
          vendor_id: number
        }
        Insert: {
          active?: boolean | null
          description?: string | null
          id?: number
          image_link?: string | null
          name: string
          price: number
          priority?: number
          unit_description: string
          vendor_id: number
        }
        Update: {
          active?: boolean | null
          description?: string | null
          id?: number
          image_link?: string | null
          name?: string
          price?: number
          priority?: number
          unit_description?: string
          vendor_id?: number
        }
        Relationships: [
          {
            foreignKeyName: "products_vendor_id_fkey"
            columns: ["vendor_id"]
            isOneToOne: false
            referencedRelation: "vendors"
            referencedColumns: ["id"]
          }
        ]
      }
      profiles: {
        Row: {
          avatar_url: string | null
          full_name: string | null
          id: string
          updated_at: string | null
          website: string | null
        }
        Insert: {
          avatar_url?: string | null
          full_name?: string | null
          id: string
          updated_at?: string | null
          website?: string | null
        }
        Update: {
          avatar_url?: string | null
          full_name?: string | null
          id?: string
          updated_at?: string | null
          website?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "profiles_id_fkey"
            columns: ["id"]
            isOneToOne: true
            referencedRelation: "users"
            referencedColumns: ["id"]
          }
        ]
      }
      user_addresses: {
        Row: {
          city: string | null
          country: string | null
          created_at: string
          id: number
          label: string | null
          latitude: number | null
          longitude: number | null
          place_id: string | null
          postal_code: string | null
          state: string | null
          street_address: string
          updated_at: string
          user_id: string
        }
        Insert: {
          city?: string | null
          country?: string | null
          created_at?: string
          id?: number
          label?: string | null
          latitude?: number | null
          longitude?: number | null
          place_id?: string | null
          postal_code?: string | null
          state?: string | null
          street_address: string
          updated_at?: string
          user_id: string
        }
        Update: {
          city?: string | null
          country?: string | null
          created_at?: string
          id?: number
          label?: string | null
          latitude?: number | null
          longitude?: number | null
          place_id?: string | null
          postal_code?: string | null
          state?: string | null
          street_address?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "user_addresses_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          }
        ]
      }
      vendor_profiles: {
        Row: {
          created_at: string
          updated_at: string | null
          user_id: string
          vendor_id: number
        }
        Insert: {
          created_at?: string
          updated_at?: string | null
          user_id: string
          vendor_id: number
        }
        Update: {
          created_at?: string
          updated_at?: string | null
          user_id?: string
          vendor_id?: number
        }
        Relationships: [
          {
            foreignKeyName: "vendor_profiles_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "vendor_profiles_vendor_id_fkey"
            columns: ["vendor_id"]
            isOneToOne: false
            referencedRelation: "vendors"
            referencedColumns: ["id"]
          }
        ]
      }
      vendors: {
        Row: {
          description: string
          id: number
          location: string | null
          name: string
          picture: string | null
          stripe_vendor_id: string | null
          user_id: string | null
        }
        Insert: {
          description: string
          id?: number
          location?: string | null
          name: string
          picture?: string | null
          stripe_vendor_id?: string | null
          user_id?: string | null
        }
        Update: {
          description?: string
          id?: number
          location?: string | null
          name?: string
          picture?: string | null
          stripe_vendor_id?: string | null
          user_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "vendors_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          }
        ]
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      add_address_and_set_order: {
        Args: {
          p_order_id: number
          _street_address: string
          _postal_code: string
        }
        Returns: {
          created_at: string
          id: number
          location_id: number | null
          status: Database["public"]["Enums"]["order_status"]
          stripe_payment_id: string | null
          total: number
          user_address_id: number | null
          user_id: string
        }
      }
      cart_items_to_order_items: {
        Args: {
          p_user_id: string
          p_order_id: number
        }
        Returns: undefined
      }
      create_single_order: {
        Args: {
          p_total_value: number
          p_items: Json
        }
        Returns: {
          created_at: string
          id: number
          location_id: number | null
          status: Database["public"]["Enums"]["order_status"]
          stripe_payment_id: string | null
          total: number
          user_address_id: number | null
          user_id: string
        }
      }
      current_user_id: {
        Args: Record<PropertyKey, never>
        Returns: string
      }
      finalize_order: {
        Args: {
          p_user_id: string
          p_order_id: number
        }
        Returns: {
          created_at: string
          id: number
          location_id: number | null
          status: Database["public"]["Enums"]["order_status"]
          stripe_payment_id: string | null
          total: number
          user_address_id: number | null
          user_id: string
        }
      }
      get_cart_total: {
        Args: Record<PropertyKey, never>
        Returns: number
      }
      get_non_zero_cart_items: {
        Args: Record<PropertyKey, never>
        Returns: {
          id: number
          product_id: number
          quantity: number
          user_id: string
        }[]
      }
      get_orders_by_status: {
        Args: {
          status_filter: Database["public"]["Enums"]["order_status"]
        }
        Returns: {
          created_at: string
          id: number
          location_id: number | null
          status: Database["public"]["Enums"]["order_status"]
          stripe_payment_id: string | null
          total: number
          user_address_id: number | null
          user_id: string
        }[]
      }
      get_recommended_products: {
        Args: Record<PropertyKey, never>
        Returns: {
          active: boolean | null
          description: string | null
          id: number
          image_link: string | null
          name: string
          price: number
          priority: number
          unit_description: string
          vendor_id: number
        }[]
      }
      get_total_number_of_items_in_the_cart: {
        Args: Record<PropertyKey, never>
        Returns: number
      }
      modify_cart: {
        Args: {
          pid: number
          qty: number
        }
        Returns: Database["public"]["CompositeTypes"]["modify_cart_result"]
      }
      orders_available_locations_for_order: {
        Args: {
          p_order: unknown
        }
        Returns: {
          address: string
          city: string | null
          id: number
          label: string | null
          postal_code: string
        }[]
      }
      orders_get_current_location: {
        Args: {
          o: unknown
        }
        Returns: {
          label: string
          street_address: string
          postal_code: string
        }[]
      }
      orders_get_saved_user_address: {
        Args: {
          o: unknown
        }
        Returns: {
          city: string | null
          country: string | null
          created_at: string
          id: number
          label: string | null
          latitude: number | null
          longitude: number | null
          place_id: string | null
          postal_code: string | null
          state: string | null
          street_address: string
          updated_at: string
          user_id: string
        }
      }
      products_cart_item: {
        Args: {
          p: unknown
        }
        Returns: {
          id: number
          product_id: number
          quantity: number
          user_id: string
        }
      }
      set_order_address: {
        Args: {
          p_order_id: number
          p_user_address_id: number
        }
        Returns: undefined
      }
      update_cart: {
        Args: {
          p_items: Json
        }
        Returns: undefined
      }
      update_order_location: {
        Args: {
          p_order_id: number
          p_location_id: number
        }
        Returns: {
          created_at: string
          id: number
          location_id: number | null
          status: Database["public"]["Enums"]["order_status"]
          stripe_payment_id: string | null
          total: number
          user_address_id: number | null
          user_id: string
        }
      }
      upsert_user_address: {
        Args: {
          _street_address: string
          _postal_code: string
        }
        Returns: number
      }
      vendors_get_active_products: {
        Args: {
          v: unknown
        }
        Returns: {
          active: boolean | null
          description: string | null
          id: number
          image_link: string | null
          name: string
          price: number
          priority: number
          unit_description: string
          vendor_id: number
        }[]
      }
    }
    Enums: {
      order_status:
        | "order_created"
        | "payment_collected"
        | "ready"
        | "successful"
        | "cancelled"
    }
    CompositeTypes: {
      modify_cart_result: {
        cart_item: unknown
        total: number
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
