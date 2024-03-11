
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

CREATE EXTENSION IF NOT EXISTS "pgsodium" WITH SCHEMA "pgsodium";

CREATE SCHEMA IF NOT EXISTS "public";

ALTER SCHEMA "public" OWNER TO "pg_database_owner";

COMMENT ON SCHEMA "public" IS 'standard public schema';

CREATE SCHEMA IF NOT EXISTS "vecs";

ALTER SCHEMA "vecs" OWNER TO "postgres";

CREATE EXTENSION IF NOT EXISTS "pg_graphql" WITH SCHEMA "graphql";

CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";

CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";

CREATE EXTENSION IF NOT EXISTS "pgjwt" WITH SCHEMA "extensions";

CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";

CREATE EXTENSION IF NOT EXISTS "vector" WITH SCHEMA "public";

CREATE TYPE "public"."chunk_details" AS (
	"content" "text",
	"order_index" integer,
	"title" "text",
	"url" "text",
	"summary" "text",
	"chunks_count" integer
);

ALTER TYPE "public"."chunk_details" OWNER TO "postgres";

CREATE TYPE "public"."match_result" AS (
	"content" "text",
	"chunk_key_points" "text"[],
	"document_key_points" "text"[],
	"title" "text",
	"url" "text"
);

ALTER TYPE "public"."match_result" OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."documents_by_key_points"("search_term" "text") RETURNS TABLE("title" "text")
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    formatted_search_term TEXT;
BEGIN
    -- Replace spaces with '&' to construct a valid tsquery
    formatted_search_term := REPLACE(search_term, ' ', ' & ');

    RETURN QUERY
    SELECT documents.title
    FROM documents
    WHERE to_tsvector(array_to_string(documents.key_points, ' ')) @@ to_tsquery(formatted_search_term)
       OR to_tsvector(documents.title) @@ to_tsquery(formatted_search_term);
END;
$$;

ALTER FUNCTION "public"."documents_by_key_points"("search_term" "text") OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."documents_by_key_questions"("search_term" "text") RETURNS TABLE("title" "text")
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    formatted_search_term TEXT;
BEGIN
    -- Replace spaces with '&' to construct a valid tsquery
    formatted_search_term := REPLACE(search_term, ' ', ' & ');

    RETURN QUERY
    SELECT documents.title
    FROM documents
    WHERE to_tsvector(array_to_string(documents.key_questions, ' ')) @@ to_tsquery(formatted_search_term)
       OR to_tsvector(documents.title) @@ to_tsquery(formatted_search_term);
END;
$$;

ALTER FUNCTION "public"."documents_by_key_questions"("search_term" "text") OWNER TO "postgres";

SET default_tablespace = '';

SET default_table_access_method = "heap";

CREATE TABLE IF NOT EXISTS "public"."chunks" (
    "id" integer NOT NULL,
    "document_id" integer NOT NULL,
    "title" "text",
    "content" "text",
    "order_index" integer,
    "embedding" "public"."vector"(1536),
    "key_questions" "text"[],
    "key_points" "text"[],
    "similar_docs" integer[],
    "similar_chunks" integer[]
);

ALTER TABLE "public"."chunks" OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."get_child_chunks"("parent_id" integer) RETURNS SETOF "public"."chunks"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    RETURN QUERY
    SELECT *
    FROM chunks
    WHERE document_id = parent_id
    ORDER BY order_index;
END;
$$;

ALTER FUNCTION "public"."get_child_chunks"("parent_id" integer) OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."get_chunk_contents"("document_id_arg" integer) RETURNS "text"[]
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    RETURN (
        SELECT ARRAY_AGG(content ORDER BY order_index)
        FROM chunks
        WHERE document_id = document_id_arg
    );
END;
$$;

ALTER FUNCTION "public"."get_chunk_contents"("document_id_arg" integer) OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."get_chunks_by_document"("document_id_arg" integer) RETURNS TABLE("content" "text", "id" integer)
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    RETURN QUERY
    SELECT chunks.content, chunks.id
    FROM chunks
    WHERE document_id = document_id_arg
    ORDER BY order_index;
END;
$$;

ALTER FUNCTION "public"."get_chunks_by_document"("document_id_arg" integer) OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."get_neighboring_chunks"("chunk_id" integer) RETURNS "json"
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    prev_chunk JSON;
    next_chunk JSON;
BEGIN
    SELECT row_to_json(chunks) INTO prev_chunk
    FROM chunks
    WHERE order_index < (SELECT order_index FROM chunks WHERE id = chunk_id)
    ORDER BY order_index DESC
    LIMIT 1;

    SELECT row_to_json(chunks) INTO next_chunk
    FROM chunks
    WHERE order_index > (SELECT order_index FROM chunks WHERE id = chunk_id)
    ORDER BY order_index ASC
    LIMIT 1;

    RETURN json_build_object('previous', prev_chunk, 'next', next_chunk);
END;
$$;

ALTER FUNCTION "public"."get_neighboring_chunks"("chunk_id" integer) OWNER TO "postgres";

CREATE TABLE IF NOT EXISTS "public"."documents" (
    "id" integer NOT NULL,
    "title" "text",
    "summary" "text",
    "url" "text",
    "meta" "jsonb",
    "embedding" "public"."vector"(1536),
    "key_questions" "text"[],
    "key_points" "text"[],
    "similar_docs" integer[],
    "similar_chunks" integer[]
);

ALTER TABLE "public"."documents" OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."get_parent_document"("chunk_id" integer) RETURNS SETOF "public"."documents"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    RETURN QUERY
    SELECT d.*
    FROM documents d
    JOIN chunks c ON c.document_id = d.id
    WHERE c.id = chunk_id;
END;
$$;

ALTER FUNCTION "public"."get_parent_document"("chunk_id" integer) OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."insert_document_with_chunks"("doc_title" "text", "doc_summary" "text", "doc_url" "text", "doc_meta" "jsonb", "doc_embedding" "public"."vector", "chunk_data" "jsonb") RETURNS integer
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    doc_id INTEGER;
    chunk RECORD;
    status_code INTEGER DEFAULT 0;  -- Assume success by default
BEGIN
    -- Insert the document
    INSERT INTO documents (title, summary, url, meta, embedding)
    VALUES (doc_title, doc_summary, doc_url, doc_meta, doc_embedding)
    RETURNING id INTO doc_id;

    -- Iterate over the chunks JSON array and insert each chunk
    FOR chunk IN SELECT * FROM jsonb_array_elements(chunk_data)
    LOOP
        INSERT INTO chunks (document_id, title, content, order_index, embedding)
        VALUES (doc_id, chunk->>'title', chunk->>'content', (chunk->>'order_index')::INTEGER, chunk->>'embedding');
    END LOOP;

    -- If the function completes without errors, the transaction will be automatically committed
    RETURN status_code;

EXCEPTION WHEN OTHERS THEN
    -- If an error occurs, the transaction will be automatically rolled back
    -- Set status code to SQLSTATE code (an error code string)
    status_code := SQLSTATE::INTEGER;  -- Convert SQLSTATE to integer for return value
    RETURN status_code;  -- Return the error code
END;
$$;

ALTER FUNCTION "public"."insert_document_with_chunks"("doc_title" "text", "doc_summary" "text", "doc_url" "text", "doc_meta" "jsonb", "doc_embedding" "public"."vector", "chunk_data" "jsonb") OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."match_chunk"("query_embedding" "public"."vector", "top_k" integer DEFAULT 10, "match_threshold" double precision DEFAULT 0.0) RETURNS SETOF "public"."chunk_details"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
  RETURN QUERY
  SELECT
    c.content,
    c.order_index,
    c.key_points,
    d.key_points,
    d.title,
    d.url,
    d.summary,
    (SELECT COUNT(*)::integer FROM public.chunks WHERE document_id = c.document_id) AS chunks_count
  FROM public.chunks c
  JOIN public.documents d ON c.document_id = d.id
  WHERE (c.embedding <#> query_embedding) * -1 > match_threshold
  ORDER BY (c.embedding <#> query_embedding) * -1 DESC
  LIMIT top_k;
END;
$$;

ALTER FUNCTION "public"."match_chunk"("query_embedding" "public"."vector", "top_k" integer, "match_threshold" double precision) OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."match_chunk_within_document"("p_document_id" integer, "query_embedding" "public"."vector", "top_k" integer DEFAULT 10, "match_threshold" double precision DEFAULT 0.0) RETURNS SETOF "public"."chunks"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
  RETURN QUERY
  SELECT
    c.*,
    (SELECT COUNT(*) FROM public.chunks WHERE document_id = c.document_id) AS chunks_count
  FROM public.chunks c
  WHERE c.document_id = p_document_id
    AND (c.embedding <#> query_embedding) * -1 > match_threshold
  ORDER BY (c.embedding <#> query_embedding) * -1 DESC
  LIMIT top_k;
END;
$$;

ALTER FUNCTION "public"."match_chunk_within_document"("p_document_id" integer, "query_embedding" "public"."vector", "top_k" integer, "match_threshold" double precision) OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."match_chunks_within_documents"("query_embedding" "public"."vector", "k" integer, "n" integer, "match_threshold" double precision DEFAULT 0.0) RETURNS TABLE("chunks_array" "public"."chunk_details"[])
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    doc RECORD;
BEGIN
    -- Loop through each document returned by match_document
    FOR doc IN SELECT * FROM match_document(query_embedding, k, match_threshold)
    LOOP
        -- For each document, aggregate the matching chunks into an array
        RETURN QUERY SELECT ARRAY(
            SELECT (ROW(c.content, c.order_index, doc.title, doc.url, doc.summary, 
                (SELECT COUNT(*) FROM public.chunks WHERE document_id = doc.id)::integer)::chunk_details)
            FROM public.chunks c
            WHERE c.document_id = doc.id
            AND (c.embedding <#> query_embedding) * -1 > match_threshold
            ORDER BY (c.embedding <#> query_embedding) * -1 DESC
            LIMIT n
        );
    END LOOP;
END;
$$;

ALTER FUNCTION "public"."match_chunks_within_documents"("query_embedding" "public"."vector", "k" integer, "n" integer, "match_threshold" double precision) OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."match_document"("query_embedding" "public"."vector", "top_k" integer DEFAULT 10, "match_threshold" double precision DEFAULT 0.0) RETURNS SETOF "public"."documents"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
  RETURN QUERY
  SELECT
    documents.*
  FROM public.documents
  WHERE (documents.embedding <#> query_embedding) * -1 > match_threshold
  ORDER BY (documents.embedding <#> query_embedding) * -1 DESC
  LIMIT top_k;
END;
$$;

ALTER FUNCTION "public"."match_document"("query_embedding" "public"."vector", "top_k" integer, "match_threshold" double precision) OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."match_multiple_chunks"("query_embeddings" "public"."vector"[], "top_k" integer, "match_threshold" numeric) RETURNS SETOF "public"."match_result"
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    i integer;
BEGIN
    -- Loop through each query embedding in the input array
    FOR i IN 1..array_upper(query_embeddings, 1) LOOP
        -- Execute the query for each embedding and return the results
        RETURN QUERY
        SELECT
            c.content,
            c.key_points AS chunk_key_points,
            d.key_points as document_key_points,
            d.title,
            d.url
        FROM
            public.chunks c
            JOIN public.documents d ON c.document_id = d.id
        WHERE
            (c.embedding <#> query_embeddings[i]) * -1 > match_threshold
        ORDER BY
            (c.embedding <#> query_embeddings[i]) * -1 DESC
        LIMIT top_k;
    END LOOP;
    RETURN;
END;
$$;

ALTER FUNCTION "public"."match_multiple_chunks"("query_embeddings" "public"."vector"[], "top_k" integer, "match_threshold" numeric) OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."update_similarity"() RETURNS "void"
    LANGUAGE "plpgsql"
    AS $_$
DECLARE
    doc RECORD;
    chunk RECORD;
    similar_docs_ids INT4[];
    similar_chunks_ids INT4[];
BEGIN
    FOR doc IN SELECT id, embedding FROM documents LOOP
        -- Get the 5 most similar documents for each document
        EXECUTE 'SELECT array_agg(id) FROM (SELECT id FROM documents WHERE id != $1 ORDER BY (embedding <-> $2) ASC LIMIT 5) as subquery'
        INTO similar_docs_ids
        USING doc.id, doc.embedding;

        -- Update the similar_docs field for the document
        UPDATE documents SET similar_docs = similar_docs_ids WHERE id = doc.id;

        -- Get the 5 most similar chunks for each document
        EXECUTE 'SELECT array_agg(id) FROM (SELECT id FROM chunks ORDER BY (embedding <-> $1) ASC LIMIT 5) as subquery'
        INTO similar_chunks_ids
        USING doc.embedding;

        -- Update the similar_chunks field for the document
        UPDATE documents SET similar_chunks = similar_chunks_ids WHERE id = doc.id;
    END LOOP;

    FOR chunk IN SELECT id, embedding FROM chunks LOOP
        -- Get the 5 most similar documents for each chunk
        EXECUTE 'SELECT array_agg(id) FROM (SELECT id FROM documents ORDER BY (embedding <-> $1) ASC LIMIT 5) as subquery'
        INTO similar_docs_ids
        USING chunk.embedding;

        -- Update the similar_docs field for the chunk
        UPDATE chunks SET similar_docs = similar_docs_ids WHERE id = chunk.id;

        -- Get the 5 most similar chunks for each chunk
        EXECUTE 'SELECT array_agg(id) FROM (SELECT id FROM chunks WHERE id != $1 ORDER BY (embedding <-> $2) ASC LIMIT 5) as subquery'
        INTO similar_chunks_ids
        USING chunk.id, chunk.embedding;

        -- Update the similar_chunks field for the chunk
        UPDATE chunks SET similar_chunks = similar_chunks_ids WHERE id = chunk.id;
    END LOOP;
END;
$_$;

ALTER FUNCTION "public"."update_similarity"() OWNER TO "postgres";

CREATE SEQUENCE IF NOT EXISTS "public"."chunks_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE "public"."chunks_id_seq" OWNER TO "postgres";

ALTER SEQUENCE "public"."chunks_id_seq" OWNED BY "public"."chunks"."id";

CREATE SEQUENCE IF NOT EXISTS "public"."documents_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE "public"."documents_id_seq" OWNER TO "postgres";

ALTER SEQUENCE "public"."documents_id_seq" OWNED BY "public"."documents"."id";

ALTER TABLE ONLY "public"."chunks" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."chunks_id_seq"'::"regclass");

ALTER TABLE ONLY "public"."documents" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."documents_id_seq"'::"regclass");

ALTER TABLE ONLY "public"."chunks"
    ADD CONSTRAINT "chunks_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "public"."documents"
    ADD CONSTRAINT "documents_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "public"."chunks"
    ADD CONSTRAINT "unique_order_within_document" UNIQUE ("document_id", "order_index");

ALTER TABLE ONLY "public"."chunks"
    ADD CONSTRAINT "chunks_document_id_fkey" FOREIGN KEY ("document_id") REFERENCES "public"."documents"("id") ON DELETE CASCADE;

GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";

GRANT ALL ON FUNCTION "public"."vector_in"("cstring", "oid", integer) TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_in"("cstring", "oid", integer) TO "anon";
GRANT ALL ON FUNCTION "public"."vector_in"("cstring", "oid", integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_in"("cstring", "oid", integer) TO "service_role";

GRANT ALL ON FUNCTION "public"."vector_out"("public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_out"("public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_out"("public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_out"("public"."vector") TO "service_role";

GRANT ALL ON FUNCTION "public"."vector_recv"("internal", "oid", integer) TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_recv"("internal", "oid", integer) TO "anon";
GRANT ALL ON FUNCTION "public"."vector_recv"("internal", "oid", integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_recv"("internal", "oid", integer) TO "service_role";

GRANT ALL ON FUNCTION "public"."vector_send"("public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_send"("public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_send"("public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_send"("public"."vector") TO "service_role";

GRANT ALL ON FUNCTION "public"."vector_typmod_in"("cstring"[]) TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_typmod_in"("cstring"[]) TO "anon";
GRANT ALL ON FUNCTION "public"."vector_typmod_in"("cstring"[]) TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_typmod_in"("cstring"[]) TO "service_role";

GRANT ALL ON FUNCTION "public"."array_to_vector"(real[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_vector"(real[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_vector"(real[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_vector"(real[], integer, boolean) TO "service_role";

GRANT ALL ON FUNCTION "public"."array_to_vector"(double precision[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_vector"(double precision[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_vector"(double precision[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_vector"(double precision[], integer, boolean) TO "service_role";

GRANT ALL ON FUNCTION "public"."array_to_vector"(integer[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_vector"(integer[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_vector"(integer[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_vector"(integer[], integer, boolean) TO "service_role";

GRANT ALL ON FUNCTION "public"."array_to_vector"(numeric[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_vector"(numeric[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_vector"(numeric[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_vector"(numeric[], integer, boolean) TO "service_role";

GRANT ALL ON FUNCTION "public"."vector_to_float4"("public"."vector", integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_to_float4"("public"."vector", integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."vector_to_float4"("public"."vector", integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_to_float4"("public"."vector", integer, boolean) TO "service_role";

GRANT ALL ON FUNCTION "public"."vector"("public"."vector", integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."vector"("public"."vector", integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."vector"("public"."vector", integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector"("public"."vector", integer, boolean) TO "service_role";

GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."vector", "public"."vector") TO "service_role";

GRANT ALL ON FUNCTION "public"."documents_by_key_points"("search_term" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."documents_by_key_points"("search_term" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."documents_by_key_points"("search_term" "text") TO "service_role";

GRANT ALL ON FUNCTION "public"."documents_by_key_questions"("search_term" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."documents_by_key_questions"("search_term" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."documents_by_key_questions"("search_term" "text") TO "service_role";

GRANT ALL ON TABLE "public"."chunks" TO "anon";
GRANT ALL ON TABLE "public"."chunks" TO "authenticated";
GRANT ALL ON TABLE "public"."chunks" TO "service_role";

GRANT ALL ON FUNCTION "public"."get_child_chunks"("parent_id" integer) TO "anon";
GRANT ALL ON FUNCTION "public"."get_child_chunks"("parent_id" integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_child_chunks"("parent_id" integer) TO "service_role";

GRANT ALL ON FUNCTION "public"."get_chunk_contents"("document_id_arg" integer) TO "anon";
GRANT ALL ON FUNCTION "public"."get_chunk_contents"("document_id_arg" integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_chunk_contents"("document_id_arg" integer) TO "service_role";

GRANT ALL ON FUNCTION "public"."get_chunks_by_document"("document_id_arg" integer) TO "anon";
GRANT ALL ON FUNCTION "public"."get_chunks_by_document"("document_id_arg" integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_chunks_by_document"("document_id_arg" integer) TO "service_role";

GRANT ALL ON FUNCTION "public"."get_neighboring_chunks"("chunk_id" integer) TO "anon";
GRANT ALL ON FUNCTION "public"."get_neighboring_chunks"("chunk_id" integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_neighboring_chunks"("chunk_id" integer) TO "service_role";

GRANT ALL ON TABLE "public"."documents" TO "anon";
GRANT ALL ON TABLE "public"."documents" TO "authenticated";
GRANT ALL ON TABLE "public"."documents" TO "service_role";

GRANT ALL ON FUNCTION "public"."get_parent_document"("chunk_id" integer) TO "anon";
GRANT ALL ON FUNCTION "public"."get_parent_document"("chunk_id" integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_parent_document"("chunk_id" integer) TO "service_role";

GRANT ALL ON FUNCTION "public"."hnswhandler"("internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."hnswhandler"("internal") TO "anon";
GRANT ALL ON FUNCTION "public"."hnswhandler"("internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."hnswhandler"("internal") TO "service_role";

GRANT ALL ON FUNCTION "public"."inner_product"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."inner_product"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."inner_product"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."inner_product"("public"."vector", "public"."vector") TO "service_role";

GRANT ALL ON FUNCTION "public"."insert_document_with_chunks"("doc_title" "text", "doc_summary" "text", "doc_url" "text", "doc_meta" "jsonb", "doc_embedding" "public"."vector", "chunk_data" "jsonb") TO "anon";
GRANT ALL ON FUNCTION "public"."insert_document_with_chunks"("doc_title" "text", "doc_summary" "text", "doc_url" "text", "doc_meta" "jsonb", "doc_embedding" "public"."vector", "chunk_data" "jsonb") TO "authenticated";
GRANT ALL ON FUNCTION "public"."insert_document_with_chunks"("doc_title" "text", "doc_summary" "text", "doc_url" "text", "doc_meta" "jsonb", "doc_embedding" "public"."vector", "chunk_data" "jsonb") TO "service_role";

GRANT ALL ON FUNCTION "public"."ivfflathandler"("internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."ivfflathandler"("internal") TO "anon";
GRANT ALL ON FUNCTION "public"."ivfflathandler"("internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."ivfflathandler"("internal") TO "service_role";

GRANT ALL ON FUNCTION "public"."l1_distance"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."l1_distance"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."l1_distance"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."l1_distance"("public"."vector", "public"."vector") TO "service_role";

GRANT ALL ON FUNCTION "public"."l2_distance"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."l2_distance"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."l2_distance"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."l2_distance"("public"."vector", "public"."vector") TO "service_role";

GRANT ALL ON FUNCTION "public"."match_chunk"("query_embedding" "public"."vector", "top_k" integer, "match_threshold" double precision) TO "anon";
GRANT ALL ON FUNCTION "public"."match_chunk"("query_embedding" "public"."vector", "top_k" integer, "match_threshold" double precision) TO "authenticated";
GRANT ALL ON FUNCTION "public"."match_chunk"("query_embedding" "public"."vector", "top_k" integer, "match_threshold" double precision) TO "service_role";

GRANT ALL ON FUNCTION "public"."match_chunk_within_document"("p_document_id" integer, "query_embedding" "public"."vector", "top_k" integer, "match_threshold" double precision) TO "anon";
GRANT ALL ON FUNCTION "public"."match_chunk_within_document"("p_document_id" integer, "query_embedding" "public"."vector", "top_k" integer, "match_threshold" double precision) TO "authenticated";
GRANT ALL ON FUNCTION "public"."match_chunk_within_document"("p_document_id" integer, "query_embedding" "public"."vector", "top_k" integer, "match_threshold" double precision) TO "service_role";

GRANT ALL ON FUNCTION "public"."match_chunks_within_documents"("query_embedding" "public"."vector", "k" integer, "n" integer, "match_threshold" double precision) TO "anon";
GRANT ALL ON FUNCTION "public"."match_chunks_within_documents"("query_embedding" "public"."vector", "k" integer, "n" integer, "match_threshold" double precision) TO "authenticated";
GRANT ALL ON FUNCTION "public"."match_chunks_within_documents"("query_embedding" "public"."vector", "k" integer, "n" integer, "match_threshold" double precision) TO "service_role";

GRANT ALL ON FUNCTION "public"."match_document"("query_embedding" "public"."vector", "top_k" integer, "match_threshold" double precision) TO "anon";
GRANT ALL ON FUNCTION "public"."match_document"("query_embedding" "public"."vector", "top_k" integer, "match_threshold" double precision) TO "authenticated";
GRANT ALL ON FUNCTION "public"."match_document"("query_embedding" "public"."vector", "top_k" integer, "match_threshold" double precision) TO "service_role";

GRANT ALL ON FUNCTION "public"."match_multiple_chunks"("query_embeddings" "public"."vector"[], "top_k" integer, "match_threshold" numeric) TO "anon";
GRANT ALL ON FUNCTION "public"."match_multiple_chunks"("query_embeddings" "public"."vector"[], "top_k" integer, "match_threshold" numeric) TO "authenticated";
GRANT ALL ON FUNCTION "public"."match_multiple_chunks"("query_embeddings" "public"."vector"[], "top_k" integer, "match_threshold" numeric) TO "service_role";

GRANT ALL ON FUNCTION "public"."update_similarity"() TO "anon";
GRANT ALL ON FUNCTION "public"."update_similarity"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_similarity"() TO "service_role";

GRANT ALL ON FUNCTION "public"."vector_accum"(double precision[], "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_accum"(double precision[], "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_accum"(double precision[], "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_accum"(double precision[], "public"."vector") TO "service_role";

GRANT ALL ON FUNCTION "public"."vector_add"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_add"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_add"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_add"("public"."vector", "public"."vector") TO "service_role";

GRANT ALL ON FUNCTION "public"."vector_avg"(double precision[]) TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_avg"(double precision[]) TO "anon";
GRANT ALL ON FUNCTION "public"."vector_avg"(double precision[]) TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_avg"(double precision[]) TO "service_role";

GRANT ALL ON FUNCTION "public"."vector_cmp"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_cmp"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_cmp"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_cmp"("public"."vector", "public"."vector") TO "service_role";

GRANT ALL ON FUNCTION "public"."vector_combine"(double precision[], double precision[]) TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_combine"(double precision[], double precision[]) TO "anon";
GRANT ALL ON FUNCTION "public"."vector_combine"(double precision[], double precision[]) TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_combine"(double precision[], double precision[]) TO "service_role";

GRANT ALL ON FUNCTION "public"."vector_dims"("public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_dims"("public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_dims"("public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_dims"("public"."vector") TO "service_role";

GRANT ALL ON FUNCTION "public"."vector_eq"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_eq"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_eq"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_eq"("public"."vector", "public"."vector") TO "service_role";

GRANT ALL ON FUNCTION "public"."vector_ge"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_ge"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_ge"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_ge"("public"."vector", "public"."vector") TO "service_role";

GRANT ALL ON FUNCTION "public"."vector_gt"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_gt"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_gt"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_gt"("public"."vector", "public"."vector") TO "service_role";

GRANT ALL ON FUNCTION "public"."vector_l2_squared_distance"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_l2_squared_distance"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_l2_squared_distance"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_l2_squared_distance"("public"."vector", "public"."vector") TO "service_role";

GRANT ALL ON FUNCTION "public"."vector_le"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_le"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_le"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_le"("public"."vector", "public"."vector") TO "service_role";

GRANT ALL ON FUNCTION "public"."vector_lt"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_lt"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_lt"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_lt"("public"."vector", "public"."vector") TO "service_role";

GRANT ALL ON FUNCTION "public"."vector_mul"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_mul"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_mul"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_mul"("public"."vector", "public"."vector") TO "service_role";

GRANT ALL ON FUNCTION "public"."vector_ne"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_ne"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_ne"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_ne"("public"."vector", "public"."vector") TO "service_role";

GRANT ALL ON FUNCTION "public"."vector_negative_inner_product"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_negative_inner_product"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_negative_inner_product"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_negative_inner_product"("public"."vector", "public"."vector") TO "service_role";

GRANT ALL ON FUNCTION "public"."vector_norm"("public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_norm"("public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_norm"("public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_norm"("public"."vector") TO "service_role";

GRANT ALL ON FUNCTION "public"."vector_spherical_distance"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_spherical_distance"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_spherical_distance"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_spherical_distance"("public"."vector", "public"."vector") TO "service_role";

GRANT ALL ON FUNCTION "public"."vector_sub"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_sub"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_sub"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_sub"("public"."vector", "public"."vector") TO "service_role";

GRANT ALL ON FUNCTION "public"."avg"("public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."avg"("public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."avg"("public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."avg"("public"."vector") TO "service_role";

GRANT ALL ON FUNCTION "public"."sum"("public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."sum"("public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."sum"("public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."sum"("public"."vector") TO "service_role";

GRANT ALL ON SEQUENCE "public"."chunks_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."chunks_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."chunks_id_seq" TO "service_role";

GRANT ALL ON SEQUENCE "public"."documents_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."documents_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."documents_id_seq" TO "service_role";

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
