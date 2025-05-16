import gradio as gr

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================

theme = gr.themes.Base(
    primary_hue="teal", secondary_hue="neutral", neutral_hue="neutral",
    font=[gr.themes.GoogleFont('Inter')], font_mono=[gr.themes.GoogleFont('Ubuntu Mono')]
)
head = """
<link rel="icon" href="https://cdn.jsdelivr.net/gh/OneLevelStudio/CORE/static/favicon.png">
"""
css = """
footer { display: none !important; }
"""

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================

def fn_chat_1(gr_history, gr_message):
    gr_history += [{"role": "user", "content": str(gr_message)}]
    gr_history += [{"role": "assistant", "content": str(gr_message)}]
    gr_history += [{"role": "user", "content": str(gr_message)}]
    gr_history += [{"role": "assistant", "content": str(gr_message)}]
    return gr_history

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================

with gr.Blocks(title="NSG", theme=theme, head=head, css=css, analytics_enabled=False, fill_height=True, fill_width=True) as demo:
    with gr.Row():
        with gr.Column(scale=3):
            gr_vdocrtext   = gr.Textbox(max_lines=5, interactive=False, visible=True, label="gr_vdocrtext")
            gr_usermessage = gr.Textbox(max_lines=1, interactive=False, visible=True, label="gr_usermessage")
        with gr.Column(scale=3, elem_id="gr_column_mid"):
            gr_history = gr.Chatbot(
                elem_id="gr_history", type="messages", group_consecutive_messages=False, container=True, label="Chatbot hỗ trợ tạo đơn hàng"
            )
            gr_message = gr.MultimodalTextbox(
                elem_id="gr_message", file_count="single", placeholder="Nhập tin nhắn", submit_btn=True, autofocus=True, autoscroll=True, container=False
            )
        with gr.Column(scale=3):
            gr_donhang_table = gr.DataFrame(headers=['Vật tư', 'Xuất xứ', 'Giá trị', 'Đơn vị', 'Ghi chú'], show_row_numbers=True)
            gr_donhang_json  = gr.JSON(height="300px", label="Thông tin đơn hàng")

    gr.on(
        triggers=[gr_message.submit],
        fn=fn_chat_1,
        inputs=[gr_history, gr_message],
        outputs=[gr_history]
    )

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================

if __name__ == "__main__":
    print("> http://localhost:1759")
    demo.launch(server_name="0.0.0.0", server_port=1759)