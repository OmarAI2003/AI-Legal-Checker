import streamlit as st

# Set the title for the app
st.title("🖼️ Chat with your legal AI contract validator")

# Initialize chat history in session state if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize uploaded image in session state
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

# --- UI Components ---

# Sidebar for image upload
with st.sidebar:
    st.header("Upload Your Contract Image down here 📄")
    # File uploader allows user to add an image
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "png", "jpeg"])
    if uploaded_file is not None:
        # Store the uploaded file in session state
        st.session_state.uploaded_image = uploaded_file
        st.success("Image uploaded successfully!")
        st.image(st.session_state.uploaded_image, caption="Uploaded Image")

# Display existing chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Chat Input and Logic ---

# The chat_input widget waits for the user to enter a message
if prompt := st.chat_input("What is your question?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response (placeholder logic)
    with st.chat_message("assistant"):
        response = f"Echo: You asked about the image, '{prompt}'"
        st.markdown(response)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})