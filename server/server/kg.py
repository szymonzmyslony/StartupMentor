# import os
# from pydantic import BaseModel, Field
# from typing import Dict, List, Optional
# from openai import OpenAI
# import instructor
# from dotenv import load_dotenv
# from graphviz import Digraph
# from server import (
#     match_chunks_within_documents,
#     matchChunksWithinDocument,
#     matchDocument,
# )


# load_dotenv()


# class Node(BaseModel):
#     id: int
#     label: str
#     color: str


# class Edge(BaseModel):
#     source: int
#     target: int
#     label: str
#     color: str = "black"


# # class KnowledgeGraph(BaseModel):
# #     nodes: Optional[List[Node]] = Field(..., default_factory=list)
# #     edges: Optional[List[Edge]] = Field(..., default_factory=list)

# #     def update(self, other: "KnowledgeGraph") -> "KnowledgeGraph":
# #         node_map: Dict[int, Node] = {
# #             node.id: node for node in self.nodes
# #         }  # Existing nodes by id
# #         edge_map: Dict[tuple, Edge] = {
# #             (edge.source, edge.target): edge for edge in self.edges
# #         }  # Existing edges by source-target tuple

# #         # Update nodes, avoiding duplicates
# #         for node in other.nodes:
# #             if node.id not in node_map:
# #                 self.nodes.append(node)
# #                 node_map[node.id] = node

# #         # Update edges, avoiding duplicates
# #         for edge in other.edges:
# #             edge_key = (edge.source, edge.target)
# #             if edge_key not in edge_map:
# #                 self.edges.append(edge)
# #                 edge_map[edge_key] = edge

# #         return self

# #     def draw(self, prefix: str = None):
# #         dot = Digraph(comment="Knowledge Graph")

# #         for node in self.nodes:
# #             dot.node(str(node.id), node.label, color=node.color)

# #         for edge in self.edges:
# #             dot.edge(
# #                 str(edge.source), str(edge.target), label=edge.label, color=edge.color
# #             )
# #         dot.render(prefix, format="png", view=True)


# # Adds response_model to ChatCompletion
# # # Allows the return of Pydantic model rather than raw JSON


# # def generate_graph(input: List[str]) -> KnowledgeGraph:
# #     cur_state = KnowledgeGraph()
# #     num_iterations = len(input)
# #     for i, inp in enumerate(input):
# #         new_updates = client.chat.completions.create(
# #             model="gpt-3.5-turbo-16k",
# #             messages=[
# #                 {
# #                     "role": "system",
# #                     "content": """You are an iterative knowledge graph builder.
# #                     You are given the current state of the graph, and you must append the nodes and edges
# #                     to it Do not procide any duplcates and try to reuse nodes as much as possible.""",
# #                 },
# #                 {
# #                     "role": "user",
# #                     "content": f"""Extract any new nodes and edges from the following:
# #                     # Part {i}/{num_iterations} of the input:

# #                     {inp}""",
# #                 },
# #                 {
# #                     "role": "user",
# #                     "content": f"""Here is the current state of the graph:
# #                     {cur_state.model_dump_json(indent=2)}""",
# #                 },
# #             ],
# #             response_model=KnowledgeGraph,
# #         )  # type: ignore

# #         # Update the current state
# #         cur_state = cur_state.update(new_updates)
# #         cur_state.draw(prefix=f"iteration_{i}")
# #     return cur_state


# # def visualize_knowledge_graph(kg: KnowledgeGraph):
# #     dot = Digraph(comment="Knowledge Graph")

# #     # Add nodes
# #     for node in kg.nodes:
# #         dot.node(str(node.id), node.label, color=node.color)

# #     # Add edges
# #     for edge in kg.edges:
# #         dot.edge(str(edge.source), str(edge.target), label=edge.label, color=edge.color)

# #     # Render the graph
# #     dot.render("knowledge_graph.gv", view=True)


# # async def process_seed_fundraising():
# #     supabase = get_supabase()
# #     seed_fundraising = await supabase.get_chunk_contents(717)
# #     graph: KnowledgeGraph = generate_graph(seed_fundraising)
# #     graph.draw(prefix="final")


# import asyncio


# async def test():
#     query = "how to start a startup"
#     documents = await match_chunks_within_documents(query)
#     # ids = [doc["id"] for doc in documents]  # type: ignore
#     # result = await matchChunksWithinDocument(ids[0], query)
#     print(documents["chunks_array"])
