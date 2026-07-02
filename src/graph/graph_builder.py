from langgraph.graph import StateGraph
from src.state.state import State
from langgraph.graph import START,END
from langgraph.prebuilt import tools_condition


class GraphBuilder:
    def __init__(self,model):
        self.llm=model
        self.graph_builder=StateGraph(State)


    def job_search_build_graph(self):
        """
        Builds the Job Search Agent pipeline using JobState and custom nodes.
        """
        from src.state.job_state import JobState
        from src.nodes.job_analyzer_node import JobAnalyzerNode
        from src.nodes.job_retriever_node import JobRetrieverNode
        from src.nodes.job_matcher_node import JobMatcherNode

        # Use separate builder for JobState
        self.job_graph_builder = StateGraph(JobState)

        analyzer = JobAnalyzerNode(self.llm)
        retriever = JobRetrieverNode()
        matcher = JobMatcherNode(self.llm)

        self.job_graph_builder.add_node("analyze_input", analyzer.process)
        self.job_graph_builder.add_node("fetch_jobs", retriever.process)
        self.job_graph_builder.add_node("match_jobs", matcher.process)

        self.job_graph_builder.add_edge(START, "analyze_input")
        self.job_graph_builder.add_edge("analyze_input","fetch_jobs")
        self.job_graph_builder.add_edge("fetch_jobs", "match_jobs")
        self.job_graph_builder.add_edge("match_jobs", END)

        return self.job_graph_builder.compile()

    def setup_graph(self):
        """
        Sets up the graph.
        """

        return self.job_search_build_graph()

