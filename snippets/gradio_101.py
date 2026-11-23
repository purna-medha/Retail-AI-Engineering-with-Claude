import os

import gradio as gr # Gradio builds simple web UIs
from anthropic import Anthropic # Anthropic is a Python client for accessing IP Protected Claude Model from their own Datacenter
from dotenv import load_dotenv

load_dotenv()
client = Anthropic(api_key=os.environ["CLAUDE_API_KEY"])

def ask_claude(question):
    response = client.messages.create(
        model="claude-haiku-5-5",
        max_tokens=256,
        messages=[{"role": "user", "content": question}],
    )
    return response.content[0].text

if __name__ == "__main__":
    demo = gr.Interface(fn= ask_claude, inputs="textbox", outputs="textbox")
    demo.launch(server_name="127.0.0.1", share=True)

# uv run gradio_101.py
# …gineering/snippets   (master +*%) > uv run gradio_101.py 
# * Running on local URL:  http://127.0.0.1:7860
# * To create a public link, set `share=True` in `launch()`.

