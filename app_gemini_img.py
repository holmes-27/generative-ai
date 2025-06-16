# pip install streamlit google-genai, pillow
import streamlit as st
import base64
import httpx
from google import genai
from google.genai import types
from PIL import Image
import io

st.set_page_config(page_title="ChatBot with Images")

# Gemini API key
apiKey = ""
model_name="gemini-2.0-flash"
client = genai.Client(api_key=apiKey)
generate_content_config = types.GenerateContentConfig(
    response_mime_type="text/plain",
)

# Initialize session state
if "chats1" not in st.session_state:
    st.session_state.chats1 = []
if "chats2" not in st.session_state:
    st.session_state.chats2 = []

# Encode local image for Gemini
def encode_image(image):
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return {
        "mime_type": "image/jpeg",
        "data": base64.b64encode(buffer.getvalue()).decode("utf-8")
    }

# Fetch and encode image from URL
def fetch_and_encode_image(image_url):
    response = httpx.get(image_url)
    if response.status_code == 200:
        return {'mime_type': 'image/jpeg', 'data': base64.b64encode(response.content).decode('utf-8')}
    return None

# Generate response using Gemini
def output(query, cho, paths):
    inputs = []

    if cho == "Attach image":
        images = [encode_image(Image.open(img)) for img in paths]
        inputs.extend(images)
    elif cho == "Paste the image link":
        images = [fetch_and_encode_image(url) for url in paths if fetch_and_encode_image(url)]
        inputs.extend(images)

    parts = []
    for img in inputs:
        parts.append(types.Part.from_bytes(mime_type=img["mime_type"], data=base64.b64decode(img["data"])))
    parts.append(types.Part.from_text(text=query))

    response_text = ""
    for chunk in client.models.generate_content_stream(
        model=model_name,
        contents=[types.Content(role="user", parts=parts)],
        config=generate_content_config
    ):
        response_text += chunk.text

    return response_text


# Sidebar selection
cho = st.sidebar.selectbox("Select", ["None", "Attach image", "Paste the image link"])

# Handling local image uploads
if cho == "Attach image":
    img_list = st.sidebar.file_uploader("Upload the image(s)", accept_multiple_files=True, type=["png", "jpg", "jpeg"])
    
    if img_list:
        st.image(img_list, width=200)
        
        for message in st.session_state.chats1:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        if retriever_query1 := st.chat_input("Enter the query"):
            st.session_state.chats1.append({"role": "user", "content": retriever_query1})
            with st.chat_message("user"):
                st.markdown(retriever_query1)

            with st.chat_message("assistant"):
                results1 = output(retriever_query1, cho, img_list)
                st.markdown(results1)

            st.session_state.chats1.append({"role": "assistant", "content": results1})
    else:
        st.session_state.chats1 = []

# Handling image links
if cho == "Paste the image link":
    img_link = st.text_area("Paste the image link here")
    
    if img_link:
        img_link_list = img_link.split()
        st.image(img_link_list, width=200)
        
        for message in st.session_state.chats2:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        if retriever_query2 := st.chat_input("Enter the query"):
            st.session_state.chats2.append({"role": "user", "content": retriever_query2})
            with st.chat_message("user"):
                st.markdown(retriever_query2)

            with st.chat_message("assistant"):
                results2 = output(retriever_query2, cho, img_link_list)
                st.markdown(results2)

            st.session_state.chats2.append({"role": "assistant", "content": results2})
    else:
        st.session_state.chats2 = []
