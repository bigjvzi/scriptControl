import streamlit as st
import subprocess

def run_script(script_path):
    result = subprocess.run(["python3", script_path], capture_output=True, text=True)
    return result.stdout

st.title("Python Script Manager")

if st.button("Run Script 1"):
    output = run_script("/path/to/script1.py")
    st.write(output)

if st.button("Run Script 2"):
    output = run_script("/path/to/script2.py")
    st.write(output)
