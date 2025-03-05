import sys
import os
import asyncio
import nest_asyncio
import streamlit as st
from langchain_groq import ChatGroq

# 1. CONFIGURATION
GROQ_API_KEY = "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"

# 2. STRONG, STRUCTURED SYSTEM PROMPT WITH CONDITIONAL RESPONSE INSTRUCTIONS
DEFAULT_SYSTEM_PROMPT = """
You are a strong mathematics assistant with expertise in providing both concise and detailed explanations. When the user asks a question, follow these guidelines:
1. If the user requests a minimal response, provide a brief, clear answer.
2. If the user requests a detailed or step-by-step explanation, provide a clear, step-by-step solution, labeling each step as "Step 1", "Step 2", etc.
3. Enclose any math expressions in LaTeX using $$ ... $$.
4. Conclude with a section labeled "Final Answer" that contains the result in LaTeX.
5. Provide strong external knowledge and proper formatting when needed.
6. Maintain a professional and instructive tone.

Example Format for Detailed Answers:
Step 1: Explanation here with $$ \\text{{LaTeX}} $$ if needed.
Step 2: Explanation here with $$ \\text{{LaTeX}} $$ if needed.
...
Final Answer:
$$ \\text{{Answer in LaTeX form}} $$

Question: {user_query}
"""

# 3. APPLY ASYNC PATCH (to support nested event loops)
nest_asyncio.apply()

def main():
    st.set_page_config(page_title="Strong Mathematics Chatbot", layout="wide")

    # -------- UI STYLING --------
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }
    body {
        background: linear-gradient(135deg, #00c9ff 0%, #92fe9d 100%);
        margin: 0; padding: 0;
    }
    header, footer { display: none; }

    /* Main chat container */
    .chat-container {
        max-width: 900px;
        margin: 40px auto;
        background: rgba(255,255,255,0.85);
        border-radius: 16px;
        padding: 25px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    }

    /* Title and subtitle styling */
    .chat-title {
        text-align: center;
        color: #333333;
        font-size: 2.4rem;
        font-weight: 600;
        margin-bottom: 5px;
    }
    .chat-subtitle {
        text-align: center;
        color: #555555;
        margin-top: 0;
        margin-bottom: 20px;
        font-size: 1.1rem;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: #34495e !important;
        color: #ecf0f1 !important;
    }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #e67e22 !important;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #ecf0f1 !important;
    }
    [data-testid="stSidebar"] .stButton>button {
        background: #e67e22 !important;
        color: #fff !important;
        font-weight: 600;
        border: none;
        border-radius: 6px;
        transition: background 0.3s;
    }
    [data-testid="stSidebar"] .stButton>button:hover {
        background: #d35400 !important;
    }

    /* Chat input styling */
    .stChatInput {
        position: sticky;
        bottom: 0;
        background: #ffffff;
        backdrop-filter: blur(6px);
        padding: 10px;
        margin-top: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .stChatInput>div>div>input {
        background-color: #f0f0f0;
        color: #333333;
        font-weight: 500;
        border-radius: 8px;
        border: 1px solid #ccc;
        padding: 10px;
    }
    .stChatInput>div>div>input:focus {
        outline: 2px solid #4CAF50;
    }
    </style>
    """, unsafe_allow_html=True)

    # -------- SIDEBAR --------
    with st.sidebar:
        st.header("About")
        st.markdown("""
**Strong Mathematics Assistant**  
- Provides both concise and detailed step-by-step solutions  
- Uses LaTeX for math expressions  
- Incorporates strong external knowledge  
- Professional & user-friendly tone
        """)
        st.markdown("---")
        st.header("How to Use")
        st.markdown("""
1. **Ask** a math question in the chat box below.  
2. **Receive** either a brief answer or a detailed, step-by-step solution.  
3. **Review** the final answer in LaTeX format.  
4. **Click** "New Chat" to start over.
        """)
        st.markdown("---")
        st.header("Conversation History")
        if st.button("New Chat"):
            st.session_state.pop("chat_history", None)
            st.success("New conversation started! 🆕")
        if "chat_history" in st.session_state and st.session_state["chat_history"]:
            for i, item in enumerate(st.session_state["chat_history"], 1):
                st.markdown(f"{i}. **You**: {item['question']}")
        else:
            st.info("No conversation history yet.")

    # -------- MAIN CHAT AREA --------
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    st.markdown("<h1 class='chat-title'>Strong Mathematics Chatbot</h1>", unsafe_allow_html=True)
    st.markdown("<p class='chat-subtitle'>Ask your math questions and get concise or detailed step-by-step, LaTeX-enhanced solutions.</p>", unsafe_allow_html=True)

    # Initialize session state for chat history
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Display existing conversation
    for msg in st.session_state["chat_history"]:
        with st.chat_message("user"):
            st.markdown(msg["question"])
        with st.chat_message("assistant"):
            st.markdown(msg["answer"])
    st.markdown("</div>", unsafe_allow_html=True)

    # -------- CHAT INPUT --------
    user_query = st.chat_input("Type your math question here... (Press Enter)")
    if user_query is not None and user_query.strip() != "":
        # Append the user's question to the conversation history
        st.session_state["chat_history"].append({"question": user_query, "answer": ""})
        with st.chat_message("user"):
            st.markdown(user_query)
        with st.spinner("Solving your problem..."):
            # Ensure the user query is safe and non-empty
            safe_user_query = user_query.strip()
            prompt = DEFAULT_SYSTEM_PROMPT.format(user_query=safe_user_query)
            
            llm = ChatGroq(
                temperature=0.7,
                groq_api_key=GROQ_API_KEY,
                model_name="mixtral-8x7b-32768"
            )
            try:
                # Invoke the language model asynchronously
                response = asyncio.run(llm.ainvoke([{"role": "user", "content": prompt}]))
                bot_answer = response.content
            except Exception as e:
                bot_answer = f"An error occurred while processing your request: {str(e)}"
        
        st.session_state["chat_history"][-1]["answer"] = bot_answer
        with st.chat_message("assistant"):
            st.markdown(bot_answer)

if __name__ == "__main__":
    main()
