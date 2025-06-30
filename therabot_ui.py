import streamlit as st
import requests

# Streamlit page setup
st.set_page_config(page_title="TheraBot Chat", layout="centered")
st.title("🧠 TheraBot - Mental Health Companion")

# Input form
with st.form("chat_form"):
    user_name = st.text_input("Your Name", value="Friend")
    user_input = st.text_area("How are you feeling today?")
    submitted = st.form_submit_button("Send")

# Session history to retain chat
if "history" not in st.session_state:
    st.session_state["history"] = []

# On submit
if submitted and user_input.strip():
    payload = {
        "user_input": user_input.strip(),
        "user_name": user_name.strip(),
        "history": st.session_state["history"]
    }

    try:
        # Change the port if your Flask server runs on a different one
        
        url = "https://therabot-hft29jtzx5zypt5rbcgnyz.streamlit.app/chat"
        # "http://127.0.0.1:2300/chat
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            st.session_state["history"] = data["history"]

            st.markdown("### 🤖 TheraBot's Reply:")
            st.success(data["response"])

            st.markdown("#### 🌱 Resource or Tip:")
            st.info(data["resource"])
        else:
            st.error(f"Error from TheraBot: {response.status_code}")
    except Exception as e:
        st.error(f"Failed to connect to TheraBot: {str(e)}")

# Show chat history
if st.session_state["history"]:
    st.markdown("---")
    st.markdown("### 🗂 Chat History")
    for msg in st.session_state["history"]:
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            st.markdown(f"**🧍‍♂️ {user_name}:** {content}")
        else:
            st.markdown(f"**🤖 TheraBot:** {content}")
