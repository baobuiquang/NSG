# ====================================================================================================

import pkg.UTILS.UTILS as UTILS
from pkg.VDOCR.VDOCR import Process_VDOCR
from pkg.LLM.LLM import Process_LLM

def llm_1_extract_jsonapi(gr_extracted_vdocr):
    schema_dondathang = """
{
    "type": "object",
    "description": "Đơn đặt hàng",
    "properties": {
        "Khách hàng": {
            "type": "object",
            "description": "Khách hàng, công ty yêu cầu vật tư/hàng hoá/sản phẩm",
            "properties": {
                "Tên": {"type": "string", "description": "Tên công ty, khách hàng"},
                "Địa chỉ": {"type": "string", "description": "Địa chỉ công ty, khách hàng"}
            }
        },
        "Danh sách vật tư": {
            "type": "array",
            "description": "Danh sách vật tư/hàng hoá/sản phẩm",
            "items": {
                "type": "object",
                "description": "Vật tư/hàng hoá/sản phẩm",
                "properties": {
                    "Vật tư": {"type": "string", "description": "Tên vật tư/hàng hoá/sản phẩm + chủng loại + quy cách + tiêu chuẩn + hình dạng + kích thước"},
                    "Xuất xứ": {"type": "string"},
                    "Khối lượng - Số lượng": {"type": "object", "properties": {"Giá trị": {"type": "number"}, "Đơn vị": {"type": "string", "enum": ["kg", "tấn", "cây", "tấm", "bộ", "bó", "cuộn", "-1"]}}},
                    "Ghi chú vật tư": {"type": "string"}
                }
            }
        },
        "Ghi chú chung": {"type": "string"}
    }
}
"""
    prompt_1 = f"""
Bạn là chuyên gia trích xuất dữ liệu.
Bạn sẽ được cung cấp: (1) Tin nhắn văn bản của khách hàng, và (2) Schema cấu trúc của kết quả.
Nhiệm vụ của bạn là: (3) Trích xuất dữ liệu JSON từ tin nhắn văn bản của khách hàng.

### (1) Tin nhắn văn bản của khách hàng:
\"\"\"
{gr_extracted_vdocr.strip()}
\"\"\"

### (2) Schema cấu trúc của kết quả:
```
{schema_dondathang.strip()}
```

### (3) Nhiệm vụ:
Từ tin nhắn văn bản của khách hàng, trích xuất dữ liệu dưới dạng JSON, tuân thủ schema một cách chính xác.
Nếu trường thông tin bị thiếu, không rõ ràng, hoặc không được nhắc đến, thì điền giá trị chuỗi "-1" nếu là string, điền số -1 nếu là number.
Định dạng kết quả: Không giải thích, không bình luận, không văn bản thừa. Chỉ trả về kết quả JSON hợp lệ. Bắt đầu bằng "{{", kết thúc bằng "}}".
""".strip()
    return UTILS.str2dict_advanced(Process_LLM(prompt_1))

def llm_2_edit_jsonapi(gr_user_message, gr_jsonapi):
    prompt_2 = f"""
Bạn sẽ được cung cấp: (1) JSON dữ liệu, và (2) Yêu cầu của người dùng.
Nhiệm vụ của bạn là: (3) Chỉnh sửa JSON dữ liệu theo yêu cầu của người dùng.

### (1) JSON dữ liệu:
```
{UTILS.dict2str(gr_jsonapi)}
```

### (2) Yêu cầu của người dùng:
\"\"\"
{gr_user_message}
\"\"\"

### (3) Nhiệm vụ:
Chỉnh sửa JSON dữ liệu theo yêu cầu của người dùng một cách chính xác và trả về JSON dữ liệu đã được chỉnh sửa.
Nếu bạn không hiểu yêu cầu của người dùng, chỉ cần trả về JSON dữ liệu gốc.
Định dạng kết quả: Không giải thích, không bình luận, không văn bản thừa. Chỉ trả về kết quả JSON hợp lệ. Bắt đầu bằng "{{", kết thúc bằng "}}".
"""
    return UTILS.str2dict_advanced(Process_LLM(prompt_2))

# ====================================================================================================

import gradio as gr

theme = gr.themes.Base(
    primary_hue="neutral", secondary_hue="neutral", neutral_hue="neutral",
    font=[gr.themes.GoogleFont('Inter')], font_mono=[gr.themes.GoogleFont('Ubuntu Mono')]
)
head = """
<link rel="icon" href="https://cdn.jsdelivr.net/gh/OneLevelStudio/CORE/static/favicon.png">
"""
css = """
footer { display: none !important; }
"""

# ====================================================================================================

def scan_jsonapi(gr_jsonapi):
    for i1, e1 in enumerate(gr_jsonapi['Danh sách vật tư']):
        bot_msg = ""
        field_to_edit = ""
        if str(e1['Vật tư']).strip() == "-1":
            bot_msg = f"✍️ Tên của vật tư thứ {i1+1}:"
            field_to_edit = f"gr_jsonapi['Danh sách vật tư'][{i1}]['Vật tư']"
        elif str(e1['Xuất xứ']).strip() == "-1":
            bot_msg = f"✍️ Xuất xứ của vật tư thứ {i1+1} ({e1['Vật tư']}):"
            field_to_edit = f"gr_jsonapi['Danh sách vật tư'][{i1}]['Xuất xứ']"
        elif str(e1['Khối lượng - Số lượng']['Đơn vị']).strip() == "-1":
            bot_msg = f"✍️ Đơn vị của vật tư thứ {i1+1} ({e1['Vật tư']}):"
            field_to_edit = f"gr_jsonapi['Danh sách vật tư'][{i1}]['Khối lượng - Số lượng']['Đơn vị']"
        elif str(e1['Khối lượng - Số lượng']['Giá trị']).strip() == "-1":
            bot_msg = f"✍️ Giá trị của vật tư thứ {i1+1} ({e1['Vật tư']}):"
            field_to_edit = f"gr_jsonapi['Danh sách vật tư'][{i1}]['Khối lượng - Số lượng']['Giá trị']"
        if bot_msg != "":
            break
    return {
        "bot_msg": bot_msg if bot_msg != "" else "💬 Bạn có muốn chỉnh sửa gì thêm?",
        "field_to_edit": field_to_edit
    }

# ====================================================================================================

def fn_upload(gr_history, gr_uploaded_file):
    gr_history += [{"role": "assistant", "content": f"Bạn đã tải lên file:"}]
    gr_history += [{"role": "assistant", "content": gr.File(gr_uploaded_file)}]
    gr_extracted_vdocr = Process_VDOCR(gr_uploaded_file)
    gr_jsonapi = llm_1_extract_jsonapi(gr_extracted_vdocr)
    gr_table = [[e['Vật tư'], e['Xuất xứ'], e['Khối lượng - Số lượng']['Giá trị'], e['Khối lượng - Số lượng']['Đơn vị'], e['Ghi chú vật tư']] for e in gr_jsonapi['Danh sách vật tư']]
    scan_res = scan_jsonapi(gr_jsonapi)
    gr_field_to_edit = scan_res['field_to_edit']
    gr_history += [{"role": "assistant", "content": scan_res['bot_msg']}]
    return gr_history, gr_extracted_vdocr, gr_jsonapi, gr_table, gr_field_to_edit

def fn_chat_1(gr_history, gr_message):
    gr_history += [{"role": "user", "content": gr_message['text']}]
    gr_user_message = gr_message['text']
    gr_message = ""
    return gr_history, gr_message, gr_user_message

def fn_chat_2(gr_history, gr_user_message, gr_jsonapi, gr_field_to_edit):
    # ---------- Case 1: gr_field_to_edit ----------
    if gr_field_to_edit.strip() != "":
        exec(f"{gr_field_to_edit} = '{gr_user_message}'")
        scan_res = scan_jsonapi(gr_jsonapi)
        gr_field_to_edit = scan_res['field_to_edit']
        gr_history += [{"role": "assistant", "content": scan_res['bot_msg']}]
    # ---------- Case 2: gr_field_to_edit is "" ----------
    else:
        gr_jsonapi_new = llm_2_edit_jsonapi(gr_user_message, gr_jsonapi)
        if gr_jsonapi == gr_jsonapi_new:
            gr_history += [{"role": "assistant", "content": "📄 Không chỉnh sửa\n💬 Bạn có muốn chỉnh sửa gì thêm?"}]
        else:
            gr_history += [{"role": "assistant", "content": "📝 Chỉnh sửa hoàn thành\n💬 Bạn có muốn chỉnh sửa gì thêm?"}]
        gr_jsonapi = gr_jsonapi_new
    # ----------------------------------------------------
    gr_table = [[e['Vật tư'], e['Xuất xứ'], e['Khối lượng - Số lượng']['Giá trị'], e['Khối lượng - Số lượng']['Đơn vị'], e['Ghi chú vật tư']] for e in gr_jsonapi['Danh sách vật tư']]
    return gr_history, gr_jsonapi, gr_table, gr_field_to_edit

with gr.Blocks(title="NSG", theme=theme, head=head, css=css, analytics_enabled=False, fill_height=True, fill_width=True) as demo:
    with gr.Row():
        with gr.Column():
            gr_uploaded_file = gr.File()
            gr_extracted_vdocr = gr.Textbox(max_lines=5, interactive=False, label="gr_extracted_vdocr")
            gr_user_message = gr.Textbox(max_lines=1, interactive=False, label="gr_user_message")
            gr_field_to_edit = gr.Textbox(max_lines=1, interactive=False, label="gr_field_to_edit")
        with gr.Column():
            gr_history = gr.Chatbot(type="messages", placeholder="# NSG", group_consecutive_messages=False, container=False)
            gr_message = gr.MultimodalTextbox(file_count="single", placeholder="Nhập tin nhắn", submit_btn=True, autofocus=True, autoscroll=True, container=False)
        with gr.Column():
            gr_table = gr.DataFrame(headers=["Vật tư", "Xuất xứ", "Giá trị", "Đơn vị", "Ghi chú vật tư"], show_row_numbers=True)
            gr_jsonapi = gr.JSON(open=True)

    # Upload file
    gr.on(
        triggers=[gr_uploaded_file.upload],
        fn=fn_upload,
        inputs=[gr_history, gr_uploaded_file],
        outputs=[gr_history, gr_extracted_vdocr, gr_jsonapi, gr_table, gr_field_to_edit],
        show_progress="full"
    )
    # Chat
    gr.on(
        triggers=[gr_message.submit],
        fn=fn_chat_1,
        inputs=[gr_history, gr_message],
        outputs=[gr_history, gr_message, gr_user_message],
        show_progress="hidden"
    ).then(
        fn=fn_chat_2,
        inputs=[gr_history, gr_user_message, gr_jsonapi, gr_field_to_edit],
        outputs=[gr_history, gr_jsonapi, gr_table, gr_field_to_edit],
        show_progress="hidden"
    )

# ====================================================================================================

if __name__ == "__main__":
    demo.launch(server_port=1234)