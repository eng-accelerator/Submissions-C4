-------------------------------------------------------------------------------------------------
Assignment - 2 [Custome Chat GPT] - START (In Progrss)
-------------------------------------------------------------------------------------------------
# Run streamlit run web_ui.py to view app on browser 
import streamlit as st

# This runs every time the app loads or user interacts
st.title("Hey! How are you!")

st.write("Enter the topic you want to learn about.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

#Chat input box
user_input = st.chat_input("Type your message...")

if user_input:
    # Save user message
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)

    # Dummy response (replace with AI later)
    jarvis_reply = f"You said: {user_input}"

    # Save response
    st.session_state.messages.append({"role": "assistant", "content": jarvis_reply})

    # Display bot response
    with st.chat_message("assistant"):
        st.markdown(jarvis_reply)
-------------------------------------------------------------------------------------------------
Assignment - 2 [Custome Chat GPT] - END
-------------------------------------------------------------------------------------------------
