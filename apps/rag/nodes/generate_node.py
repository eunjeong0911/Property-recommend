from common.state import RAGState

def generate(state: RAGState) -> RAGState:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    question = state["question"]
    graph_results = state.get("graph_results", [])
    
    # Simple generation using LLM
    llm = ChatOpenAI(model="gpt-5-nano", temperature=0)
    
    prompt = ChatPromptTemplate.from_template(
        """
        Answer the question based on the following context:
        {context}
        
        Question: {question}
        """
    )
    
    chain = prompt | llm | StrOutputParser()
    
    answer = chain.invoke({"question": question, "context": graph_results})
    
    state["answer"] = answer
    return state
