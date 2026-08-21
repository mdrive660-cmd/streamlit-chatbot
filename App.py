import streamlit as st

# Display a large title
st.title("Hello World!")

# Display a simple text description
st.write("Welcome to your very first Streamlit web application.")

# Optional: Add an interactive button widget
if st.button("Click Me"):
    st.success("You clicked the button! 🎉")
