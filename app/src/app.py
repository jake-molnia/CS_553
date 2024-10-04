import gradio as gr
from huggingface_hub import InferenceClient
import torch
from transformers import pipeline

# Inference client setup
client = InferenceClient("meta-llama/Meta-Llama-3-8B-Instruct")
pipe = pipeline("text-generation", "microsoft/Phi-3.5-mini-instruct", torch_dtype=torch.bfloat16, device_map="auto")

# Global flag to handle cancellation
stop_inference = False

def respond(
    message,
    history: list[tuple[str, str]],
    system_message="You are a friendly Chatbot. Your job is to assist users in emergencies so reply fast but accuratly.",
    max_tokens=2048,
    temperature=0.7,
    top_p=0.95,
    use_local_model=False,
):
    global stop_inference
    stop_inference = False  # Reset cancellation flag

    # Initialize history if it's None
    if history is None:
        history = []

    if use_local_model:
        # local inference 
        messages = [{"role": "system", "content": system_message}]
        for val in history:
            if val[0]:
                messages.append({"role": "user", "content": val[0]})
            if val[1]:
                messages.append({"role": "assistant", "content": val[1]})
        messages.append({"role": "user", "content": message})

        response = ""
        for output in pipe(
            messages,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=True,
            top_p=top_p,
        ):
            if stop_inference:
                response = "Inference cancelled."
                yield history + [(message, response)]
                return
            token = output['generated_text'][-1]['content']
            response += token
            yield history + [(message, response)]  # Yield history + new response

    else:
        # API-based inference 
        messages = [{"role": "system", "content": system_message}]
        for val in history:
            if val[0]:
                messages.append({"role": "user", "content": val[0]})
            if val[1]:
                messages.append({"role": "assistant", "content": val[1]})
        messages.append({"role": "user", "content": message})

        response = ""
        for message_chunk in client.chat_completion(
            messages,
            max_tokens=max_tokens,
            stream=True,
            temperature=temperature,
            top_p=top_p,
        ):
            if stop_inference:
                response = "Inference cancelled."
                yield history + [(message, response)]
                return
            if stop_inference:
                response = "Inference cancelled."
                break
            token = message_chunk.choices[0].delta.content
            response += token
            yield history + [(message, response)]  # Yield history + new response


def cancel_inference():
    global stop_inference
    stop_inference = True

def clear_conversation():
    return None

# Custom CSS for an enhanced look
custom_css = """
body {
    font-family: 'Roboto', sans-serif;
    background-color: #f5f7fa;
}
#main-container {
    max-width: 900px;
    margin: 0 auto;
    padding: 20px;
    background: white;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    border-radius: 15px;
}
.gradio-container {
    margin-top: 20px;
}
.gr-button {
    background-color: #4a90e2;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 10px 20px;
    cursor: pointer;
    transition: all 0.3s ease;
    font-weight: bold;
}
.gr-button:hover {
    background-color: #357abd;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}
.gr-button.secondary {
    background-color: #f0f0f0;
    color: #333;
}
.gr-button.secondary:hover {
    background-color: #e0e0e0;
}
.gr-button.cancel {
    background-color: #e74c3c;
}
.gr-button.cancel:hover {
    background-color: #c0392b;
}
.gr-form {
    border: 1px solid #e0e0e0;
    padding: 15px;
    border-radius: 10px;
    background-color: #f9f9f9;
}
.gr-box {
    border-radius: 8px;
    border: 1px solid #e0e0e0;
}
.gr-padded {
    padding: 15px;
}
.gr-chat {
    font-size: 16px;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    overflow: hidden;
}
.gr-chat .message {
    padding: 10px 15px;
    border-bottom: 1px solid #f0f0f0;
}
.gr-chat .user {
    background-color: #e8f0fe;
}
.gr-chat .bot {
    background-color: #ffffff;
}
#title {
    text-align: center;
    font-size: 2.5em;
    margin-bottom: 20px;
    color: #2c3e50;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
}
"""

# Define the interface
with gr.Blocks(css=custom_css) as demo:
    gr.Markdown("<h1 id='title'>🤖 EMERGENCY RESPONSE BOT 🚀</h1>")
    gr.Markdown("Engage in a conversation with our AI chatbot using customizable settings. \n It's a demo bot for a emergency response system. \n NOTE: This bot was made for educational purposes only and should not be used in real emergencies.")

    with gr.Row():
        with gr.Column(scale=2):
            chat_history = gr.Chatbot(label="Chat", height=500)
            user_input = gr.Textbox(show_label=False, placeholder="Type your message here...", lines=2)
            with gr.Row():
                submit_button = gr.Button("Send", variant="primary")
                cancel_button = gr.Button("Cancel", variant="stop")
                clear_button = gr.Button("Clear Chat", variant="secondary")
        
        with gr.Column(scale=1):
            with gr.Accordion("Advanced Settings", open=False):
                system_message = gr.Textbox(value="You are a friendly Chatbot.", label="System message", interactive=True)
                use_local_model = gr.Checkbox(label="Use Local Model", value=False)
                max_tokens = gr.Slider(minimum=1, maximum=2048, value=512, step=1, label="Max new tokens")
                temperature = gr.Slider(minimum=0.1, maximum=4.0, value=0.7, step=0.1, label="Temperature")
                top_p = gr.Slider(minimum=0.1, maximum=1.0, value=0.95, step=0.05, label="Top-p (nucleus sampling)")
            
            with gr.Accordion("Chat Information", open=True):
                message_count = gr.Number(label="Messages in Conversation", value=0, interactive=False)
                word_count = gr.Number(label="Total Words", value=0, interactive=False)

    # Event handlers
    submit_button.click(respond, 
                        [user_input, chat_history, system_message, max_tokens, temperature, top_p, use_local_model], 
                        [chat_history])
    user_input.submit(respond, 
                      [user_input, chat_history, system_message, max_tokens, temperature, top_p, use_local_model], 
                      [chat_history])
    cancel_button.click(cancel_inference)
    clear_button.click(clear_conversation, outputs=[chat_history])

    # Update chat information
    def update_chat_info(history):
        if history is None:
            return 0, 0
        message_count = len(history)
        word_count = sum(len(msg[0].split()) + len(msg[1].split()) for msg in history)
        return message_count, word_count

    chat_history.change(update_chat_info, inputs=[chat_history], outputs=[message_count, word_count])

if __name__ == "__main__":
    demo.launch(share=False)  # Remove share=True because it's not supported on HF Spaces