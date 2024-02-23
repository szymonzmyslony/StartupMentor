class Agent:
    def __init__(self, llm, tools, task_description):
        self.llm = llm  # Large Language Model instance
        self.tools = (
            tools  # Array of tools available for the agent (e.g., browser, dalle)
        )
        self.task_description = (
            task_description  # Description of the task this agent is specialized in
        )

    def perform_task(self, task_input) -> str:
        # Implement the logic to perform the task using the LLM and tools
        return ""


class CoordinatorAgent:
    def __init__(self):
        self.agents = []  # List to hold all registered agents

    def register_agent(self, agent):
        self.agents.append(agent)

    def delegate_task(self, task_description, task_input):
        # Logic to find the appropriate agent based on the task_description
        # and delegate the task_input to that agent's perform_task method
        for agent in self.agents:
            if agent.task_description == task_description:
                return agent.perform_task(task_input)
        raise ValueError("No suitable agent found for this task")
