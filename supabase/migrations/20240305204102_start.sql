
SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

CREATE EXTENSION IF NOT EXISTS "pg_net" WITH SCHEMA "extensions";

CREATE EXTENSION IF NOT EXISTS "pgsodium" WITH SCHEMA "pgsodium";

CREATE SCHEMA IF NOT EXISTS "public";

ALTER SCHEMA "public" OWNER TO "pg_database_owner";

COMMENT ON SCHEMA "public" IS 'standard public schema';

CREATE EXTENSION IF NOT EXISTS "pg_graphql" WITH SCHEMA "graphql";

CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";

CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";

CREATE EXTENSION IF NOT EXISTS "pgjwt" WITH SCHEMA "extensions";

CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";

SET default_tablespace = '';

SET default_table_access_method = "heap";

CREATE TABLE IF NOT EXISTS "public"."cart_items" (
    "id" integer NOT NULL,
    "user_id" "uuid" NOT NULL,
    "product_id" integer NOT NULL,
    "quantity" integer NOT NULL
);

ALTER TABLE "public"."cart_items" OWNER TO "postgres";

CREATE TYPE "public"."modify_cart_result" AS (
	"cart_item" "public"."cart_items",
	"total" numeric
);

ALTER TYPE "public"."modify_cart_result" OWNER TO "postgres";

CREATE TYPE "public"."order_status" AS ENUM (
    'order_created',
    'payment_collected',
    'ready',
    'successful',
    'cancelled'
);

ALTER TYPE "public"."order_status" OWNER TO "postgres";

CREATE TABLE IF NOT EXISTS "public"."orders" (
    "id" integer NOT NULL,
    "user_id" "uuid" NOT NULL,
    "created_at" timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "stripe_payment_id" character varying(255),
    "status" "public"."order_status" DEFAULT 'order_created'::"public"."order_status" NOT NULL,
    "total" numeric(10,2) NOT NULL,
    "user_address_id" integer,
    "location_id" integer,
    CONSTRAINT "orders_check" CHECK ((("user_address_id" IS NULL) <> ("location_id" IS NULL)))
);

ALTER TABLE "public"."orders" OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."add_address_and_set_order"("p_order_id" integer, "_street_address" "text", "_postal_code" character varying) RETURNS "public"."orders"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$  -- Here the function returns 'orders' type
DECLARE
    v_address_id INTEGER;
    v_order orders%ROWTYPE;  -- Declare a variable of type 'orders'
BEGIN
    -- Use the upsert_user_address function to insert the address
    v_address_id := upsert_user_address(_street_address, _postal_code);

    -- Use the set_order_address function to set the address for the order
    PERFORM set_order_address(p_order_id, v_address_id);

    -- Fetch the updated order into the variable
    SELECT * INTO v_order FROM orders WHERE id = p_order_id;
    
    -- Return the updated order
    RETURN v_order;
END;
$$;

ALTER FUNCTION "public"."add_address_and_set_order"("p_order_id" integer, "_street_address" "text", "_postal_code" character varying) OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."cart_items_to_order_items"("p_user_id" "uuid", "p_order_id" integer) RETURNS "void"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
    v_cart_items RECORD;
BEGIN
    FOR v_cart_items IN 
        SELECT cart_items.*, products.price AS product_price
        FROM cart_items
        INNER JOIN products ON cart_items.product_id = products.id
        WHERE cart_items.user_id = p_user_id
    LOOP
        -- Insert each cart item into order_items and associate it with the new order
        INSERT INTO order_items (order_id, product_id, user_id, quantity, price)
        VALUES (p_order_id, v_cart_items.product_id, v_cart_items.user_id, v_cart_items.quantity, v_cart_items.product_price);
    END LOOP;
END;
$$;

ALTER FUNCTION "public"."cart_items_to_order_items"("p_user_id" "uuid", "p_order_id" integer) OWNER TO "postgres";



CREATE OR REPLACE FUNCTION "public"."create_single_order"("p_total_value" numeric, "p_items" "jsonb") RETURNS "public"."orders"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
    v_new_order orders;
    v_location_id INTEGER;
    v_user_id UUID;
BEGIN
    -- Fetch the current user ID using a hypothetical function
    PERFORM update_cart(p_items);

    v_user_id := current_user_id();

    -- Fetch the ID of the first location from the locations table
    SELECT id INTO v_location_id FROM locations LIMIT 1;

    -- Insert a new order with the fetched location_id and set total_value to p_total_value
    INSERT INTO orders(user_id, location_id, total)
    VALUES (v_user_id, v_location_id, p_total_value)
    RETURNING * INTO v_new_order;

    -- Use the cart_items_to_order_items function to handle cart items
    PERFORM cart_items_to_order_items(v_user_id, v_new_order.id);

    RETURN v_new_order;
END;
$$;

ALTER FUNCTION "public"."create_single_order"("p_total_value" numeric, "p_items" "jsonb") OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."current_user_id"() RETURNS "uuid"
    LANGUAGE "plpgsql" STABLE
    AS $$
BEGIN
    RETURN current_setting('jwt.claims.user_id')::uuid;
EXCEPTION
    WHEN OTHERS THEN
        -- If the setting does not exist or is not a uuid, return null
        RETURN NULL;
END;
$$;

ALTER FUNCTION "public"."current_user_id"() OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."finalize_order"("p_user_id" "uuid", "p_order_id" integer) RETURNS "public"."orders"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
    v_order orders%ROWTYPE;
BEGIN
    -- Update the order status to 'payment_collected' and capture the updated order
    UPDATE orders
    SET status = 'payment_collected'
    WHERE id = p_order_id AND user_id = p_user_id
    RETURNING * INTO v_order;
    
    DELETE FROM cart_items
    WHERE user_id = p_user_id;

    -- Return the updated order
    RETURN v_order;
END;
$$;

ALTER FUNCTION "public"."finalize_order"("p_user_id" "uuid", "p_order_id" integer) OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."get_cart_total"() RETURNS numeric
    LANGUAGE "plpgsql" STABLE SECURITY DEFINER
    AS $$
BEGIN
    RETURN (
        SELECT SUM(p.price * ci.quantity)
        FROM cart_items ci
        JOIN products p ON ci.product_id = p.id
        WHERE ci.user_id = current_user_id() AND ci.quantity <> 0
    );
END;
$$;

ALTER FUNCTION "public"."get_cart_total"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_non_zero_cart_items"() RETURNS SETOF "public"."cart_items"
    LANGUAGE "plpgsql" STABLE SECURITY DEFINER
    AS $$
BEGIN
    RETURN QUERY 
    SELECT *
    FROM cart_items
    WHERE user_id = current_user_id() AND quantity <> 0;
END;
$$;

ALTER FUNCTION "public"."get_non_zero_cart_items"() OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."get_orders_by_status"("status_filter" "public"."order_status") RETURNS SETOF "public"."orders"
    LANGUAGE "plpgsql" STABLE SECURITY DEFINER
    AS $$
DECLARE
    _user_id UUID := current_user_id();
BEGIN
  RETURN QUERY
  SELECT * FROM orders 
  WHERE status != status_filter AND user_id = _user_id
  ORDER BY created_at DESC; -- Sorting by the creation timestamp, newest first
END;
$$;

ALTER FUNCTION "public"."get_orders_by_status"("status_filter" "public"."order_status") OWNER TO "postgres";

CREATE TABLE IF NOT EXISTS "public"."products" (
    "id" integer NOT NULL,
    "vendor_id" integer NOT NULL,
    "price" numeric(10,2) NOT NULL,
    "image_link" character varying(255),
    "description" "text",
    "name" character varying(255) NOT NULL,
    "unit_description" character varying(255) NOT NULL,
    "priority" integer DEFAULT 3 NOT NULL,
    "active" boolean DEFAULT false
);

ALTER TABLE "public"."products" OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."get_recommended_products"() RETURNS SETOF "public"."products"
    LANGUAGE "sql" STABLE SECURITY DEFINER
    AS $$
  SELECT * FROM products
  WHERE active = true
  ORDER BY priority * RANDOM() DESC;
$$;

ALTER FUNCTION "public"."get_recommended_products"() OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."get_total_number_of_items_in_the_cart"() RETURNS integer
    LANGUAGE "plpgsql" STABLE SECURITY DEFINER
    AS $$
DECLARE
  total_quantity INT;
BEGIN
    SELECT SUM(quantity) INTO total_quantity
    FROM cart_items
    WHERE user_id = current_user_id() AND quantity > 0;

    RETURN COALESCE(total_quantity, 0);
END;
$$;

ALTER FUNCTION "public"."get_total_number_of_items_in_the_cart"() OWNER TO "postgres";




CREATE OR REPLACE FUNCTION "public"."handle_new_user"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
begin
  insert into public.profiles (id, full_name)
  values (new.id, new.raw_user_meta_data->>'name');
  return new;
end;
$$;

ALTER FUNCTION "public"."handle_new_user"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."modify_cart"("pid" integer, "qty" integer) RETURNS "public"."modify_cart_result"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
    v_cart_item cart_items%ROWTYPE;
    v_total DECIMAL;
BEGIN
    -- First, we attempt to update the quantity of an existing record.
    UPDATE cart_items
    SET quantity = qty
    WHERE product_id = pid AND user_id = current_user_id()
    RETURNING * INTO v_cart_item;

    -- If the update found a row (i.e., the product already existed in the cart),
    -- it will update the quantity. If not, it will insert a new row.
    IF NOT FOUND THEN
        INSERT INTO cart_items (product_id, user_id, quantity)
        VALUES (pid, current_user_id(), qty)
        RETURNING * INTO v_cart_item;
    END IF;

    -- Get the new cart total
    v_total := get_cart_total();

    -- Return the new cart item and the new total
    RETURN (v_cart_item, v_total)::modify_cart_result;
END;
$$;

ALTER FUNCTION "public"."modify_cart"("pid" integer, "qty" integer) OWNER TO "postgres";

CREATE TABLE IF NOT EXISTS "public"."locations" (
    "id" integer NOT NULL,
    "address" "text" NOT NULL,
    "postal_code" character varying(10) NOT NULL,
    "city" character varying(255),
    "label" character varying(255)
);

ALTER TABLE "public"."locations" OWNER TO "postgres";




CREATE OR REPLACE FUNCTION "public"."orders_available_locations_for_order"("p_order" "public"."orders") RETURNS SETOF "public"."locations"
    LANGUAGE "plpgsql" STABLE SECURITY DEFINER
    AS $$
BEGIN
    RETURN QUERY SELECT * FROM locations;
END;
$$;

ALTER FUNCTION "public"."orders_available_locations_for_order"("p_order" "public"."orders") OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."orders_get_current_location"("o" "public"."orders") RETURNS TABLE("label" character varying, "street_address" "text", "postal_code" character varying)
    LANGUAGE "plpgsql" STABLE SECURITY DEFINER
    AS $$
BEGIN
    -- If the order has a location_id, fetch data from the locations table
    IF o.location_id IS NOT NULL THEN
        RETURN QUERY 
        SELECT l.label::VARCHAR(255), l.address AS street_address, l.postal_code
        FROM locations l
        WHERE l.id = o.location_id;
    END IF;

    -- Else if the order has a user_address_id, fetch data from the user_addresses table
    IF o.user_address_id IS NOT NULL THEN
        RETURN QUERY 
        SELECT 'Twój własny adres'::VARCHAR(255) AS label, ua.street_address, ua.postal_code
        FROM user_addresses ua
        WHERE ua.id = o.user_address_id;
    END IF;
END;
$$;

ALTER FUNCTION "public"."orders_get_current_location"("o" "public"."orders") OWNER TO "postgres";

CREATE TABLE IF NOT EXISTS "public"."user_addresses" (
    "id" integer NOT NULL,
    "user_id" "uuid" NOT NULL,
    "label" character varying(255),
    "street_address" "text" NOT NULL,
    "city" character varying(255),
    "state" character varying(255),
    "postal_code" character varying(10),
    "country" character varying(255),
    "place_id" character varying(255),
    "latitude" numeric(9,6),
    "longitude" numeric(9,6),
    "created_at" timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at" timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);

ALTER TABLE "public"."user_addresses" OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."orders_get_saved_user_address"("o" "public"."orders") RETURNS "public"."user_addresses"
    LANGUAGE "plpgsql" STABLE SECURITY DEFINER
    AS $$
DECLARE
    _user_id UUID := current_user_id();
    _result user_addresses;
BEGIN
    SELECT * INTO _result
    FROM user_addresses
    WHERE user_id = _user_id
    LIMIT 1;

    RETURN _result;
END;
$$;

ALTER FUNCTION "public"."orders_get_saved_user_address"("o" "public"."orders") OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."products_cart_item"("p" "public"."products") RETURNS "public"."cart_items"
    LANGUAGE "sql" STABLE SECURITY DEFINER
    AS $$
  select *
  from cart_items
  where cart_items.product_id = p.id
  and cart_items.user_id = current_user_id();
$$;

ALTER FUNCTION "public"."products_cart_item"("p" "public"."products") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."set_order_address"("p_order_id" integer, "p_user_address_id" integer) RETURNS "void"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM user_addresses WHERE id = p_user_address_id) THEN
        UPDATE orders
        SET user_address_id = p_user_address_id,
            location_id = NULL  -- Set location_id to NULL to maintain the CHECK constraint
        WHERE id = p_order_id;
    ELSE
        RAISE EXCEPTION 'User Address ID % does not exist.', p_user_address_id;
    END IF;
END;
$$;

ALTER FUNCTION "public"."set_order_address"("p_order_id" integer, "p_user_address_id" integer) OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."update_cart"("p_items" "jsonb") RETURNS "void"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
  v_product_id INTEGER;
  v_quantity INTEGER;
  v_user_id UUID := current_user_id(); -- Replace with your actual function to get current user ID
  rec RECORD;
BEGIN
  -- Check if p_items is a JSONB object
  IF jsonb_typeof(p_items) != 'object' THEN
    RAISE EXCEPTION 'Invalid input: p_items must be a JSONB object';
  END IF;

  RAISE NOTICE 'Function Called. User ID: %', v_user_id;

  -- Step 1: Clear existing cart items for the user
  DELETE FROM cart_items WHERE user_id = v_user_id;

  -- Step 2: Insert new cart items
  FOR rec IN SELECT * FROM jsonb_each_text(p_items)
  LOOP
    v_product_id := rec.key::INTEGER;
    v_quantity := rec.value::INTEGER;

    RAISE NOTICE 'Inserting Product ID: %, Quantity: %', v_product_id, v_quantity;

    INSERT INTO cart_items (user_id, product_id, quantity)
    VALUES (v_user_id, v_product_id, v_quantity);
  END LOOP;
END;
$$;

ALTER FUNCTION "public"."update_cart"("p_items" "jsonb") OWNER TO "postgres";




CREATE OR REPLACE FUNCTION "public"."update_order_location"("p_order_id" integer, "p_location_id" integer) RETURNS "public"."orders"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
    v_updated_order orders;
BEGIN
    UPDATE orders
    SET location_id = p_location_id,
    user_address_id = NULL -- Set user_address_id to NULL to maintain the CHECK constraint
    WHERE id = p_order_id
    RETURNING * INTO v_updated_order;

    RETURN v_updated_order;
END;
$$;

ALTER FUNCTION "public"."update_order_location"("p_order_id" integer, "p_location_id" integer) OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."upsert_user_address"("_street_address" "text", "_postal_code" character varying) RETURNS integer
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$  -- returns the ID of the newly created address
DECLARE
    v_address_id INTEGER;
BEGIN
  INSERT INTO user_addresses(user_id, street_address, postal_code)
    VALUES(current_user_id(), _street_address, _postal_code)  -- Use current_user_id() function
    ON CONFLICT(user_id, street_address, postal_code)
    DO UPDATE 
    SET street_address = EXCLUDED.street_address,
        postal_code = EXCLUDED.postal_code
    RETURNING id INTO v_address_id;

    RETURN v_address_id;
END;
$$;

ALTER FUNCTION "public"."upsert_user_address"("_street_address" "text", "_postal_code" character varying) OWNER TO "postgres";

CREATE TABLE IF NOT EXISTS "public"."vendors" (
    "id" integer NOT NULL,
    "name" character varying(255) NOT NULL,
    "picture" character varying(500),
    "location" character varying(255),
    "description" character varying(1000) NOT NULL,
    "user_id" "uuid",
    "stripe_vendor_id" "text"
);

ALTER TABLE "public"."vendors" OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."vendors_get_active_products"("v" "public"."vendors") RETURNS SETOF "public"."products"
    LANGUAGE "sql" STABLE SECURITY DEFINER
    AS $$
  SELECT * FROM products
  WHERE active = true AND vendor_id = v.id;
$$;

ALTER FUNCTION "public"."vendors_get_active_products"("v" "public"."vendors") OWNER TO "postgres";

CREATE SEQUENCE IF NOT EXISTS "public"."cart_items_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE "public"."cart_items_id_seq" OWNER TO "postgres";

ALTER SEQUENCE "public"."cart_items_id_seq" OWNED BY "public"."cart_items"."id";

CREATE TABLE IF NOT EXISTS "public"."customers" (
    "id" "uuid" NOT NULL,
    "stripe_customer_id" "text"
);

ALTER TABLE "public"."customers" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."locations_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE "public"."locations_id_seq" OWNER TO "postgres";

ALTER SEQUENCE "public"."locations_id_seq" OWNED BY "public"."locations"."id";

CREATE TABLE IF NOT EXISTS "public"."order_items" (
    "id" integer NOT NULL,
    "order_id" integer NOT NULL,
    "product_id" integer NOT NULL,
    "user_id" "uuid" NOT NULL,
    "quantity" integer NOT NULL,
    "price" numeric(10,2) NOT NULL
);

ALTER TABLE "public"."order_items" OWNER TO "postgres";

CREATE SEQUENCE IF NOT EXISTS "public"."order_items_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE "public"."order_items_id_seq" OWNER TO "postgres";

ALTER SEQUENCE "public"."order_items_id_seq" OWNED BY "public"."order_items"."id";

CREATE SEQUENCE IF NOT EXISTS "public"."orders_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE "public"."orders_id_seq" OWNER TO "postgres";

ALTER SEQUENCE "public"."orders_id_seq" OWNED BY "public"."orders"."id";

CREATE SEQUENCE IF NOT EXISTS "public"."products_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE "public"."products_id_seq" OWNER TO "postgres";

ALTER SEQUENCE "public"."products_id_seq" OWNED BY "public"."products"."id";

CREATE TABLE IF NOT EXISTS "public"."profiles" (
    "id" "uuid" NOT NULL,
    "updated_at" timestamp with time zone,
    "full_name" "text",
    "avatar_url" "text",
    "website" "text"
);

ALTER TABLE "public"."profiles" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."user_addresses_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE "public"."user_addresses_id_seq" OWNER TO "postgres";

ALTER SEQUENCE "public"."user_addresses_id_seq" OWNED BY "public"."user_addresses"."id";

CREATE TABLE IF NOT EXISTS "public"."vendor_profiles" (
    "user_id" "uuid" NOT NULL,
    "vendor_id" integer NOT NULL,
    "created_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at" timestamp with time zone
);

ALTER TABLE "public"."vendor_profiles" OWNER TO "postgres";

CREATE SEQUENCE IF NOT EXISTS "public"."vendors_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE "public"."vendors_id_seq" OWNER TO "postgres";

ALTER SEQUENCE "public"."vendors_id_seq" OWNED BY "public"."vendors"."id";

ALTER TABLE ONLY "public"."cart_items" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."cart_items_id_seq"'::"regclass");


ALTER TABLE ONLY "public"."locations" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."locations_id_seq"'::"regclass");

ALTER TABLE ONLY "public"."order_items" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."order_items_id_seq"'::"regclass");

ALTER TABLE ONLY "public"."orders" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."orders_id_seq"'::"regclass");

ALTER TABLE ONLY "public"."products" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."products_id_seq"'::"regclass");


ALTER TABLE ONLY "public"."user_addresses" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."user_addresses_id_seq"'::"regclass");

ALTER TABLE ONLY "public"."vendors" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."vendors_id_seq"'::"regclass");

ALTER TABLE ONLY "public"."cart_items"
    ADD CONSTRAINT "cart_items_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "public"."customers"
    ADD CONSTRAINT "customers_pkey" PRIMARY KEY ("id");


ALTER TABLE ONLY "public"."locations"
    ADD CONSTRAINT "locations_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "public"."order_items"
    ADD CONSTRAINT "order_items_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "public"."orders"
    ADD CONSTRAINT "orders_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "public"."products"
    ADD CONSTRAINT "products_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "public"."profiles"
    ADD CONSTRAINT "profiles_pkey" PRIMARY KEY ("id");


ALTER TABLE ONLY "public"."user_addresses"
    ADD CONSTRAINT "unique_address_for_user" UNIQUE ("user_id", "street_address", "postal_code");

ALTER TABLE ONLY "public"."user_addresses"
    ADD CONSTRAINT "user_addresses_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "public"."vendor_profiles"
    ADD CONSTRAINT "vendor_profiles_pkey" PRIMARY KEY ("user_id", "vendor_id");

ALTER TABLE ONLY "public"."vendors"
    ADD CONSTRAINT "vendors_pkey" PRIMARY KEY ("id");

CREATE INDEX "cart_items_product_id_idx" ON "public"."cart_items" USING "btree" ("product_id");

CREATE INDEX "cart_items_user_id_idx" ON "public"."cart_items" USING "btree" ("user_id");


CREATE INDEX "order_items_order_id_idx" ON "public"."order_items" USING "btree" ("order_id");

CREATE INDEX "order_items_product_id_idx" ON "public"."order_items" USING "btree" ("product_id");

CREATE INDEX "order_items_user_id_idx" ON "public"."order_items" USING "btree" ("user_id");


CREATE INDEX "orders_location_id_idx" ON "public"."orders" USING "btree" ("location_id");

CREATE INDEX "orders_user_address_id_idx" ON "public"."orders" USING "btree" ("user_address_id");

CREATE INDEX "orders_user_id_idx" ON "public"."orders" USING "btree" ("user_id");

CREATE INDEX "products_vendor_id_idx" ON "public"."products" USING "btree" ("vendor_id");


ALTER TABLE ONLY "public"."cart_items"
    ADD CONSTRAINT "cart_items_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."products"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."cart_items"
    ADD CONSTRAINT "cart_items_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."profiles"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."customers"
    ADD CONSTRAINT "customers_id_fkey" FOREIGN KEY ("id") REFERENCES "public"."profiles"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."order_items"
    ADD CONSTRAINT "order_items_order_id_fkey" FOREIGN KEY ("order_id") REFERENCES "public"."orders"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."order_items"
    ADD CONSTRAINT "order_items_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."products"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."order_items"
    ADD CONSTRAINT "order_items_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."profiles"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."orders"
    ADD CONSTRAINT "orders_location_id_fkey" FOREIGN KEY ("location_id") REFERENCES "public"."locations"("id");

ALTER TABLE ONLY "public"."orders"
    ADD CONSTRAINT "orders_user_address_id_fkey" FOREIGN KEY ("user_address_id") REFERENCES "public"."user_addresses"("id") ON DELETE SET NULL;

ALTER TABLE ONLY "public"."orders"
    ADD CONSTRAINT "orders_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."profiles"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."products"
    ADD CONSTRAINT "products_vendor_id_fkey" FOREIGN KEY ("vendor_id") REFERENCES "public"."vendors"("id");

ALTER TABLE ONLY "public"."profiles"
    ADD CONSTRAINT "profiles_id_fkey" FOREIGN KEY ("id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;


ALTER TABLE ONLY "public"."user_addresses"
    ADD CONSTRAINT "user_addresses_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."profiles"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."vendor_profiles"
    ADD CONSTRAINT "vendor_profiles_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."vendor_profiles"
    ADD CONSTRAINT "vendor_profiles_vendor_id_fkey" FOREIGN KEY ("vendor_id") REFERENCES "public"."vendors"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."vendors"
    ADD CONSTRAINT "vendors_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");

CREATE POLICY "Customers can read only their own customer profiles" ON "public"."customers" FOR SELECT USING (("public"."current_user_id"() = "id"));



CREATE POLICY "Logged users can create new order_items" ON "public"."order_items" FOR INSERT WITH CHECK (("public"."current_user_id"() IS NOT NULL));

CREATE POLICY "Logged users can create orders" ON "public"."orders" FOR INSERT WITH CHECK (("public"."current_user_id"() IS NOT NULL));

CREATE POLICY "Logged users can create user_addresses" ON "public"."user_addresses" FOR INSERT WITH CHECK (("public"."current_user_id"() IS NOT NULL));



CREATE POLICY "Only logged users can create locations" ON "public"."locations" FOR INSERT WITH CHECK (("public"."current_user_id"() IS NOT NULL));

CREATE POLICY "Only logged users can create new cart items" ON "public"."cart_items" FOR INSERT WITH CHECK (("public"."current_user_id"() IS NOT NULL));


CREATE POLICY "Products are viewable by everyone" ON "public"."products" FOR SELECT TO "authenticated", "anon" USING (true);

CREATE POLICY "Public profiles are viewable by everyone." ON "public"."profiles" FOR SELECT USING (true);

CREATE POLICY "Users can insert their own profile." ON "public"."profiles" FOR INSERT WITH CHECK (("public"."current_user_id"() = "id"));

CREATE POLICY "Users can only see their own orders" ON "public"."orders" FOR SELECT USING (("public"."current_user_id"() = "user_id"));

CREATE POLICY "Users can only update their own orders" ON "public"."orders" FOR UPDATE USING (("public"."current_user_id"() = "user_id"));

CREATE POLICY "Users can read only their own cart_items" ON "public"."cart_items" FOR SELECT USING (("public"."current_user_id"() = "user_id"));

CREATE POLICY "Users can read only their own order_items" ON "public"."order_items" FOR SELECT USING (("public"."current_user_id"() = "user_id"));

CREATE POLICY "Users can read only their own user_addresses" ON "public"."user_addresses" FOR SELECT USING (("public"."current_user_id"() = "user_id"));

CREATE POLICY "Users can update own profile." ON "public"."profiles" FOR UPDATE USING (("public"."current_user_id"() = "id"));

CREATE POLICY "Users can update their own addresses" ON "public"."user_addresses" FOR UPDATE USING (("public"."current_user_id"() = "user_id"));

CREATE POLICY "Users can update their own cart_items" ON "public"."cart_items" FOR UPDATE USING (("public"."current_user_id"() = "user_id"));

CREATE POLICY "Vendors are viewable by everyone" ON "public"."vendors" FOR SELECT TO "authenticated", "anon" USING (true);

ALTER TABLE "public"."cart_items" ENABLE ROW LEVEL SECURITY;

ALTER TABLE "public"."customers" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."locations" ENABLE ROW LEVEL SECURITY;

ALTER TABLE "public"."order_items" ENABLE ROW LEVEL SECURITY;

ALTER TABLE "public"."orders" ENABLE ROW LEVEL SECURITY;

ALTER TABLE "public"."products" ENABLE ROW LEVEL SECURITY;

ALTER TABLE "public"."profiles" ENABLE ROW LEVEL SECURITY;

ALTER TABLE "public"."user_addresses" ENABLE ROW LEVEL SECURITY;

ALTER TABLE "public"."vendors" ENABLE ROW LEVEL SECURITY;

GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";

GRANT ALL ON TABLE "public"."cart_items" TO "anon";
GRANT ALL ON TABLE "public"."cart_items" TO "authenticated";
GRANT ALL ON TABLE "public"."cart_items" TO "service_role";

GRANT ALL ON TABLE "public"."orders" TO "anon";
GRANT ALL ON TABLE "public"."orders" TO "authenticated";
GRANT ALL ON TABLE "public"."orders" TO "service_role";

GRANT ALL ON FUNCTION "public"."add_address_and_set_order"("p_order_id" integer, "_street_address" "text", "_postal_code" character varying) TO "anon";
GRANT ALL ON FUNCTION "public"."add_address_and_set_order"("p_order_id" integer, "_street_address" "text", "_postal_code" character varying) TO "authenticated";
GRANT ALL ON FUNCTION "public"."add_address_and_set_order"("p_order_id" integer, "_street_address" "text", "_postal_code" character varying) TO "service_role";

GRANT ALL ON FUNCTION "public"."cart_items_to_order_items"("p_user_id" "uuid", "p_order_id" integer) TO "anon";
GRANT ALL ON FUNCTION "public"."cart_items_to_order_items"("p_user_id" "uuid", "p_order_id" integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."cart_items_to_order_items"("p_user_id" "uuid", "p_order_id" integer) TO "service_role";


GRANT ALL ON FUNCTION "public"."create_single_order"("p_total_value" numeric, "p_items" "jsonb") TO "anon";
GRANT ALL ON FUNCTION "public"."create_single_order"("p_total_value" numeric, "p_items" "jsonb") TO "authenticated";
GRANT ALL ON FUNCTION "public"."create_single_order"("p_total_value" numeric, "p_items" "jsonb") TO "service_role";

GRANT ALL ON FUNCTION "public"."current_user_id"() TO "anon";
GRANT ALL ON FUNCTION "public"."current_user_id"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."current_user_id"() TO "service_role";

GRANT ALL ON FUNCTION "public"."finalize_order"("p_user_id" "uuid", "p_order_id" integer) TO "anon";
GRANT ALL ON FUNCTION "public"."finalize_order"("p_user_id" "uuid", "p_order_id" integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."finalize_order"("p_user_id" "uuid", "p_order_id" integer) TO "service_role";

GRANT ALL ON FUNCTION "public"."get_cart_total"() TO "anon";
GRANT ALL ON FUNCTION "public"."get_cart_total"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_cart_total"() TO "service_role";


GRANT ALL ON FUNCTION "public"."get_non_zero_cart_items"() TO "anon";
GRANT ALL ON FUNCTION "public"."get_non_zero_cart_items"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_non_zero_cart_items"() TO "service_role";

GRANT ALL ON FUNCTION "public"."get_orders_by_status"("status_filter" "public"."order_status") TO "anon";
GRANT ALL ON FUNCTION "public"."get_orders_by_status"("status_filter" "public"."order_status") TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_orders_by_status"("status_filter" "public"."order_status") TO "service_role";

GRANT ALL ON TABLE "public"."products" TO "anon";
GRANT ALL ON TABLE "public"."products" TO "authenticated";
GRANT ALL ON TABLE "public"."products" TO "service_role";

GRANT ALL ON FUNCTION "public"."get_recommended_products"() TO "anon";
GRANT ALL ON FUNCTION "public"."get_recommended_products"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_recommended_products"() TO "service_role";

GRANT ALL ON FUNCTION "public"."get_total_number_of_items_in_the_cart"() TO "anon";
GRANT ALL ON FUNCTION "public"."get_total_number_of_items_in_the_cart"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_total_number_of_items_in_the_cart"() TO "service_role";



GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "anon";
GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "service_role";



GRANT ALL ON FUNCTION "public"."modify_cart"("pid" integer, "qty" integer) TO "anon";
GRANT ALL ON FUNCTION "public"."modify_cart"("pid" integer, "qty" integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."modify_cart"("pid" integer, "qty" integer) TO "service_role";

GRANT ALL ON TABLE "public"."locations" TO "anon";
GRANT ALL ON TABLE "public"."locations" TO "authenticated";
GRANT ALL ON TABLE "public"."locations" TO "service_role";


GRANT ALL ON FUNCTION "public"."orders_available_locations_for_order"("p_order" "public"."orders") TO "anon";
GRANT ALL ON FUNCTION "public"."orders_available_locations_for_order"("p_order" "public"."orders") TO "authenticated";
GRANT ALL ON FUNCTION "public"."orders_available_locations_for_order"("p_order" "public"."orders") TO "service_role";

GRANT ALL ON FUNCTION "public"."orders_get_current_location"("o" "public"."orders") TO "anon";
GRANT ALL ON FUNCTION "public"."orders_get_current_location"("o" "public"."orders") TO "authenticated";
GRANT ALL ON FUNCTION "public"."orders_get_current_location"("o" "public"."orders") TO "service_role";

GRANT ALL ON TABLE "public"."user_addresses" TO "anon";
GRANT ALL ON TABLE "public"."user_addresses" TO "authenticated";
GRANT ALL ON TABLE "public"."user_addresses" TO "service_role";

GRANT ALL ON FUNCTION "public"."orders_get_saved_user_address"("o" "public"."orders") TO "anon";
GRANT ALL ON FUNCTION "public"."orders_get_saved_user_address"("o" "public"."orders") TO "authenticated";
GRANT ALL ON FUNCTION "public"."orders_get_saved_user_address"("o" "public"."orders") TO "service_role";

GRANT ALL ON FUNCTION "public"."products_cart_item"("p" "public"."products") TO "anon";
GRANT ALL ON FUNCTION "public"."products_cart_item"("p" "public"."products") TO "authenticated";
GRANT ALL ON FUNCTION "public"."products_cart_item"("p" "public"."products") TO "service_role";



GRANT ALL ON FUNCTION "public"."set_order_address"("p_order_id" integer, "p_user_address_id" integer) TO "anon";
GRANT ALL ON FUNCTION "public"."set_order_address"("p_order_id" integer, "p_user_address_id" integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."set_order_address"("p_order_id" integer, "p_user_address_id" integer) TO "service_role";

GRANT ALL ON FUNCTION "public"."update_cart"("p_items" "jsonb") TO "anon";
GRANT ALL ON FUNCTION "public"."update_cart"("p_items" "jsonb") TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_cart"("p_items" "jsonb") TO "service_role";


GRANT ALL ON FUNCTION "public"."update_order_location"("p_order_id" integer, "p_location_id" integer) TO "anon";
GRANT ALL ON FUNCTION "public"."update_order_location"("p_order_id" integer, "p_location_id" integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_order_location"("p_order_id" integer, "p_location_id" integer) TO "service_role";

GRANT ALL ON FUNCTION "public"."upsert_user_address"("_street_address" "text", "_postal_code" character varying) TO "anon";
GRANT ALL ON FUNCTION "public"."upsert_user_address"("_street_address" "text", "_postal_code" character varying) TO "authenticated";
GRANT ALL ON FUNCTION "public"."upsert_user_address"("_street_address" "text", "_postal_code" character varying) TO "service_role";

GRANT ALL ON TABLE "public"."vendors" TO "anon";
GRANT ALL ON TABLE "public"."vendors" TO "authenticated";
GRANT ALL ON TABLE "public"."vendors" TO "service_role";

GRANT ALL ON FUNCTION "public"."vendors_get_active_products"("v" "public"."vendors") TO "anon";
GRANT ALL ON FUNCTION "public"."vendors_get_active_products"("v" "public"."vendors") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vendors_get_active_products"("v" "public"."vendors") TO "service_role";

GRANT ALL ON SEQUENCE "public"."cart_items_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."cart_items_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."cart_items_id_seq" TO "service_role";

GRANT ALL ON TABLE "public"."customers" TO "anon";
GRANT ALL ON TABLE "public"."customers" TO "authenticated";
GRANT ALL ON TABLE "public"."customers" TO "service_role";

GRANT ALL ON SEQUENCE "public"."locations_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."locations_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."locations_id_seq" TO "service_role";

GRANT ALL ON TABLE "public"."order_items" TO "anon";
GRANT ALL ON TABLE "public"."order_items" TO "authenticated";
GRANT ALL ON TABLE "public"."order_items" TO "service_role";

GRANT ALL ON SEQUENCE "public"."order_items_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."order_items_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."order_items_id_seq" TO "service_role";

GRANT ALL ON SEQUENCE "public"."orders_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."orders_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."orders_id_seq" TO "service_role";

GRANT ALL ON SEQUENCE "public"."products_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."products_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."products_id_seq" TO "service_role";

GRANT ALL ON TABLE "public"."profiles" TO "anon";
GRANT ALL ON TABLE "public"."profiles" TO "authenticated";
GRANT ALL ON TABLE "public"."profiles" TO "service_role";

GRANT ALL ON SEQUENCE "public"."user_addresses_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."user_addresses_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."user_addresses_id_seq" TO "service_role";

GRANT ALL ON TABLE "public"."vendor_profiles" TO "anon";
GRANT ALL ON TABLE "public"."vendor_profiles" TO "authenticated";
GRANT ALL ON TABLE "public"."vendor_profiles" TO "service_role";

GRANT ALL ON SEQUENCE "public"."vendors_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."vendors_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."vendors_id_seq" TO "service_role";

ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "service_role";

ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "service_role";

ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "service_role";

RESET ALL;
