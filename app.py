import streamlit as st
from PIL import Image

st.set_page_config(
    page_title="Image to 3D Studio",
    page_icon="🎨",
    layout="wide"
)

st.title("✨ Image to 3D Studio")
st.write("Upload an image and start your 3D journey!")

st.markdown("---")

uploaded_file = st.file_uploader(
    "📸 Upload your image",
    type=["png", "jpg", "jpeg", "webp"]
)

if uploaded_file:
    image = Image.open(uploaded_file)

    st.subheader("🖼️ Your Uploaded Image")
    st.image(image, use_container_width=True)

    st.success("Image uploaded successfully!")

    if st.button("🚀 Prepare 3D Model"):
        st.info(
            "Your image is ready! "
            "Next, connect an AI 3D generation service "
            "to create a real 3D model."
        )

st.markdown("---")
st.caption("Free Image to 3D Studio | Python Project")