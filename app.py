from flask import Flask, request, jsonify
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from transformers import pipeline
from openai import OpenAI
from dotenv import load_dotenv

import streamlit as st
from openai import OpenAI


import os

# --- CONFIG ---
load_dotenv()
#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key = st.secrets["OPENAI_API_KEY"])
sentiment_analyzer = pipeline("sentiment-analysis")

# --- LLM Call ---
def call_openai_llm(prompt):
    response = client.chat.completions.create(
        model="o4-mini",
        messages=[
            {"role": "system", "content": "You are TheraBot, an empathetic mental health chatbot."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

# --- Nodes ---
def analyze_sentiment(state):
    user_input = state["user_input"]
    sentiment = sentiment_analyzer(user_input)[0]
    state["sentiment"] = sentiment["label"]
    return state

def manage_state(state):
    history = state.get("history", [])
    history.append({"role": "user", "content": state["user_input"]})
    state["history"] = history
    return state

def generate_response(state):
    sentiment = state["sentiment"]
    user_input = state["user_input"]
    name = state.get("user_name", "friend")

    prompt = (
        f"You are TheraBot, a warm, empathetic friend of {name}. "
        f"The user seems {sentiment.lower()} based on their message. "
        f"Reply with:\n"
        f"1. A supportive, caring message addressing them by name\n"
        f"2. A short helpful mental health resource, encouragement, or activity suggestion\n\n"
        f"{name}: {user_input}"
    )

    response = call_openai_llm(prompt)
    # Split response intelligently if needed (e.g., with a delimiter like "---" or based on structure)
    parts = response.split("\n2. ", 1)
    support_message = parts[0].replace("1. ", "").strip()
    resource = parts[1].strip() if len(parts) > 1 else ""

    state["bot_response"] = support_message
    state["resource"] = resource
    state["history"].append({"role": "assistant", "content": support_message})
    return state


def route_resources(state):
    sentiment = state["sentiment"]
    prompt = f"Based on the user's sentiment of {sentiment.lower()}, suggest a brief, helpful mental health resource, activity, or encouragement. Keep it short."
    resource = call_openai_llm(prompt)
    state["resource"] = resource
    return state

# --- Define State ---
from typing import TypedDict

class ChatState(TypedDict):
    user_input: str
    sentiment: str
    bot_response: str
    resource: str
    history: list
    user_name: str

# --- Build Graph ---
graph = StateGraph(ChatState)
graph.add_node("analyze_sentiment", analyze_sentiment)
graph.add_node("manage_state", manage_state)
graph.add_node("generate_response", generate_response)
graph.add_node("route_resources", route_resources)

graph.set_entry_point("analyze_sentiment")
graph.add_edge("analyze_sentiment", "manage_state")
graph.add_edge("manage_state", "generate_response")
graph.add_edge("generate_response", "route_resources")
graph.add_edge("route_resources", END)

therabot = graph.compile()
from flask_cors import CORS

# --- Flask App ---
app = Flask(__name__)



CORS(app)
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_input = data.get("user_input", "")
    user_name = data.get("user_name", "")
    history = data.get("history", [])

    state = {
        "user_input": user_input,
        "user_name": user_name,
        "history": history
    }

    result = therabot.invoke(state)

    return jsonify({
        "response": result["bot_response"],
        "resource": result["resource"],
        "history": result["history"]
    })


@app.route("/healthcheck", methods=["GET"])
def health():
   return jsonify({"status": "TheraBot is running"}), 200



if __name__ == "__main__":
    app.run(debug=True, port=2300)