import gradio as gr
import random
import time

def on_select(chatbot, evt: gr.SelectData):
    chatbot += [{"role": "assistant", "content": f"You selected {evt.value} at {evt.index} from {evt.target}"}]
    return chatbot

with gr.Blocks() as demo:
    chatbot = gr.Chatbot(type="messages")
    msg = gr.Textbox()
    clear = gr.ClearButton([msg, chatbot])

    def respond(message, chat_history):
        chat_history.append({"role": "user", "content": message})
        chat_history.append({"role": "assistant", "content": "OPTIONS", "options": [{"value": "AAAAA1", "label": "AAAAA2"}, {"value": "BBBBB1", "label": "BBBBB2"}]})
        time.sleep(0.5)
        return "", chat_history

    msg.submit(respond, [msg, chatbot], [msg, chatbot])

    chatbot.option_select(
        fn=on_select,
        inputs=[chatbot],
        outputs=[chatbot]
    )

if __name__ == "__main__":
    demo.launch()