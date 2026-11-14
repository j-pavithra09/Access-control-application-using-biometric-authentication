import streamlit as st
from decide import decide

st.set_page_config(
    page_title="HID Access Control",
    page_icon="🔐",
    layout="centered"
)

st.title("🔐 Campus Access Control")
st.subheader("AI-Powered Biometric Authentication")

st.info("Demo mode: Testing decision logic")

person = st.selectbox(
    "Select Student",
    ["riya", "arjun", "unknown"]
)

photo = st.camera_input("Capture your photograph")

if photo:

    st.image(photo, caption="Captured Photograph")

    st.success("Photograph captured successfully!")

    # Temporary simulated score for testing
    score = st.slider(
        "Simulated Face Similarity Score",
        0, 100, 95
    )

    if st.button("Verify Identity"):

        decision, reason = decide(person, score)

        st.subheader("Verification Result")

        st.metric("Face Similarity", f"{score}%")

        if decision == "ALLOW":
            st.success("ACCESS ALLOWED")

        elif decision == "DENY":
            st.error("ACCESS DENIED")

        else:
            st.warning("MANUAL REVIEW REQUIRED")

        st.write("Reason:", reason)