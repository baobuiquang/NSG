from pkg.VDOCR.VDOCR import Process_VDOCR
from pkg.LLM.LLM import Process_LLM
import pkg.UTILS.UTILS as UTILS
import gradio as gr
import csv
import re

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================

def llm_1_extract_gr_donhang_json(gr_vdocrtext):
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
{gr_vdocrtext.strip()}
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

def llm_2_edit_gr_donhang_json(gr_donhang_json, gr_usertext):
    prompt_2 = f"""
Bạn sẽ được cung cấp: (1) JSON dữ liệu, và (2) Yêu cầu của người dùng.
Nhiệm vụ của bạn là: (3) Chỉnh sửa JSON dữ liệu theo yêu cầu của người dùng.

### (1) JSON dữ liệu:
```
{UTILS.dict2str(gr_donhang_json)}
```

### (2) Yêu cầu của người dùng:
\"\"\"
{gr_usertext}
\"\"\"

### (3) Nhiệm vụ:
Chỉnh sửa JSON dữ liệu theo yêu cầu của người dùng một cách chính xác và trả về JSON dữ liệu đã được chỉnh sửa.
Nếu bạn không hiểu yêu cầu của người dùng, chỉ cần trả về JSON dữ liệu gốc.
Định dạng kết quả: Không giải thích, không bình luận, không văn bản thừa. Chỉ trả về kết quả JSON hợp lệ. Bắt đầu bằng "{{", kết thúc bằng "}}".
"""
    return UTILS.str2dict_advanced(Process_LLM(prompt_2))

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================

with open('static/knowledge_sanphams.csv', mode='r', newline='', encoding='utf-8') as f:
    KNOWLEDGE_SANPHAMS = [e for e in csv.DictReader(f)]

def add_possible_manoibos(gr_donhang_json):
    def stringinfo2possiblemanoibos(stringinfo):
        # Example: "D8VASCB240T -1" -> ['VAS8C', 'VAS8C4']
        stringinfo = stringinfo.lower()
        # vattu_info
        vattu_info = { "macthep": None, "duongkinh": None, "hinhdang": None, "xuatxu": None }
        for e in list(set([e['macthep'].lower() for e in KNOWLEDGE_SANPHAMS])):
            if e in stringinfo:
                vattu_info['macthep'] = e
        for e in list(set([e['duongkinh'].lower() for e in KNOWLEDGE_SANPHAMS])):
            if e in stringinfo:
                vattu_info['duongkinh'] = e
        for e in list(set([e['hinhdang'].lower() for e in KNOWLEDGE_SANPHAMS])):
            if e in stringinfo:
                vattu_info['hinhdang'] = e
        for e1 in list(set([e['xuatxu'].lower() for e in KNOWLEDGE_SANPHAMS])):
            for e2 in e1.split(" | "):
                if e2 in stringinfo:
                    vattu_info['xuatxu'] = e1
        # Filter knowledge_sanphams by vattu_info
        possible_sanphams = []
        for e in KNOWLEDGE_SANPHAMS:
            if e['macthep'].lower()==vattu_info['macthep'] or vattu_info['macthep']==None:
                if e['duongkinh'].lower()==vattu_info['duongkinh'] or vattu_info['duongkinh']==None:
                    if e['hinhdang'].lower()==vattu_info['hinhdang'] or vattu_info['hinhdang']==None:
                        if e['xuatxu'].lower()==vattu_info['xuatxu'] or vattu_info['xuatxu']==None:
                            possible_sanphams.append(e)
        possiblemanoibos = [e['manoibo'] for e in possible_sanphams]
        return possiblemanoibos
    for i, vattu in enumerate(gr_donhang_json['Danh sách vật tư']):
        stringinfo = f"{vattu['Vật tư']} {vattu['Xuất xứ']}"
        possiblemanoibos = stringinfo2possiblemanoibos(stringinfo)
        gr_donhang_json['Danh sách vật tư'][i]['possiblemanoibos'] = possiblemanoibos
        if len(possiblemanoibos) == 1:
            gr_donhang_json['Danh sách vật tư'][i]['manoibo'] = possiblemanoibos[0]
        else:
            gr_donhang_json['Danh sách vật tư'][i]['manoibo'] = None
    return gr_donhang_json

def gr_donhang_json_2_gr_donhang_table(gr_donhang_json):
    gr_donhang_table = [[e['manoibo'], e['Vật tư'], e['Xuất xứ'], e['Khối lượng - Số lượng']['Giá trị'], e['Khối lượng - Số lượng']['Đơn vị'], e['Ghi chú vật tư']] for e in gr_donhang_json['Danh sách vật tư']]
    gr_donhang_header = f"""
### Thông tin đơn hàng
- **Khách hàng:** {gr_donhang_json['Khách hàng']['Tên']}
- **Ghi chú chung:** {gr_donhang_json['Ghi chú chung']}
"""
    return gr_donhang_table, gr_donhang_header

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================

theme = gr.themes.Base(
    primary_hue="teal", secondary_hue="neutral", neutral_hue="neutral",
    font=[gr.themes.GoogleFont('Inter')], font_mono=[gr.themes.GoogleFont('JetBrains Mono')],
    radius_size=gr.themes.sizes.radius_lg
)
head = """
<link rel="icon" href="https://cdn.jsdelivr.net/gh/OneLevelStudio/CORE/static/favicon.png">
"""
css = """
* { -ms-overflow-style: none; scrollbar-width: none; }
*::-webkit-scrollbar { display: none; }
footer { display: none !important; }
#gr_column_mid { height: 70vh !important; }
#gr_history    { flex-grow: 1 !important; }
#gr_message textarea { font-size: 1rem !important; }




#gr_message button.submit-button, #gr_message button.upload-button {
    height: 32px !important;
    width: 32px !important;
    border-radius: 8px !important;
}
#gr_history .message {
    padding: 12px 16px;
    box-shadow: none;
    margin-top: 8px;
}

#gr_history .options button.option {
    font-size: 1rem;
    font-weight: 600;
    padding: 12px 0;
    border: none;
    color: var(--button-primary-text-color);
    background: var(--button-primary-background-fill);
}
#gr_history .options button.option:hover {
    background: var(--button-primary-background-fill-hover);
}

.toast-body.info { background: white; }
"""

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================

def fn_upload_1(gr_history, gr_userfile):
    gr_preview_1 = gr.Image(visible=False)
    gr_preview_2 = gr.TextArea(visible=False)
    if UTILS.split_filepath(gr_userfile)['extension'] in UTILS.FILE_EXTENSION_IMG:
        gr_preview_1 = gr.Image(gr_userfile, visible=True)
    elif UTILS.split_filepath(gr_userfile)['extension'] in UTILS.FILE_EXTENSION_PDF:
        from pymupdf import Document as Document_Parser_PDF
        PDF2IMG_ZOOM = 4.0
        with Document_Parser_PDF(gr_userfile) as PDF_document:
            if len(PDF_document) > 1:
                raise ValueError("⚠️ VDOCR > Multiple-pages PDF not supported yet")
            else:
                page = PDF_document[0]
                img_pil = page.get_pixmap(dpi=int(72*PDF2IMG_ZOOM)).pil_image()
        gr_preview_1 = gr.Image(img_pil, visible=True)
    elif UTILS.split_filepath(gr_userfile)['extension'] in UTILS.FILE_EXTENSION_TXT + UTILS.FILE_EXTENSION_DOC + UTILS.FILE_EXTENSION_XLS:
        gr_preview_2 = gr.TextArea(Process_VDOCR(gr_userfile), visible=True)
    gr_history += [{"role": "user", "content": gr.File(gr_userfile)}]
    gr_history += [{"role": "assistant", "content": "⏳ Đang đọc văn bản..."}]
    return gr_history, gr_preview_1, gr_preview_2

def fn_upload_2(gr_history, gr_userfile):
    gr_vdocrtext = Process_VDOCR(gr_userfile)
    gr_history += [{"role": "assistant", "content": "✔️ Đã hoàn thành đọc văn bản"}]
    gr_history += [{"role": "assistant", "content": "⏳ Đang trích xuất thông tin đơn hàng..."}]
    return gr_history, gr_vdocrtext

def fn_upload_3(gr_history, gr_vdocrtext):
    gr_donhang_json = llm_1_extract_gr_donhang_json(gr_vdocrtext)
    gr_donhang_json = add_possible_manoibos(gr_donhang_json)
    gr_donhang_table, gr_donhang_header = gr_donhang_json_2_gr_donhang_table(gr_donhang_json)
    gr_history += [{"role": "assistant", "content": "✔️ Đã hoàn thành trích xuất thông tin đơn hàng"}]
    return gr_history, gr_donhang_json, gr_donhang_table, gr_donhang_header

def fn_upload_4():
    return ""

def fn_chat_1(gr_history, gr_message, gr_donhang_json):
    gr_history += [{"role": "user", "content": gr_message['text']}]
    if gr_donhang_json == None:
        gr_chat_next = "FALSE"
        gr_history += [{"role": "assistant", "content": "📤 Mời bạn tải lên tập tin (IMG, PDF, DOCX, XLSX, TXT)"}]
    else:
        gr_chat_next = "TRUE"
    return gr_history, "", gr_message['text'].strip(), gr_chat_next

def fn_chat_2(gr_history, gr_chat_next, gr_donhang_json, gr_donhang_table, gr_donhang_header, gr_manoibo_edit_id, gr_usertext):
    if gr_chat_next == "FALSE":
        pass
    elif gr_chat_next == "TRUE":
        if gr_manoibo_edit_id != -6969:
            gr_chat_next = "FALSE"
            gr_donhang_json['Danh sách vật tư'][gr_manoibo_edit_id]['manoibo'] = gr_usertext
            gr_donhang_table, gr_donhang_header = gr_donhang_json_2_gr_donhang_table(gr_donhang_json)
            gr_manoibo_edit_id = -6969
    else:
        raise ValueError("⚠️ > fn_chat_2 > gr_chat_next is not TRUE/FALSE")
    return gr_history, gr_chat_next, gr_donhang_json, gr_donhang_table, gr_donhang_header, gr_manoibo_edit_id

def fn_chat_3(gr_history, gr_chat_next, gr_manoibo_edit_id, gr_donhang_json):
    if gr_donhang_json != None:
        _flag_full_manoibo = True
        for i, vattu in enumerate(gr_donhang_json['Danh sách vật tư']):
            if vattu['manoibo'] == None:
                gr_chat_next = "FALSE"
                _flag_full_manoibo = False
                gr_manoibo_edit_id = i
                _content = f"## 📋\nMã nội bộ của vật tư thứ {i+1} ({vattu['Vật tư']}) là gì?"
                _options = [{"label": e, "value": f"gr_donhang_json['Danh sách vật tư'][{i}]['manoibo'] = '{e}'"} for e in vattu['possiblemanoibos']]
                gr_history += [{"role": "assistant", "content": _content, "options": _options}]
                break
        if _flag_full_manoibo == True:
            if gr_chat_next == "FALSE":
                gr_history += [{"role": "assistant", "content": "## 💬\nBạn có muốn chỉnh sửa gì thêm?"}]
    return gr_history, gr_chat_next, gr_manoibo_edit_id

def fn_chat_4(gr_history, gr_chat_next, gr_donhang_json, gr_donhang_table, gr_donhang_header, gr_usertext):
    if gr_chat_next == "FALSE":
        pass
    elif gr_chat_next == "TRUE":
        if gr_usertext != "":
            gr_chat_next = "COMPLETED"
            gr_donhang_json["Danh sách vật tư"] = [{k: v for k, v in item.items() if k != "possiblemanoibos"} for item in gr_donhang_json["Danh sách vật tư"]] # Remove key "possiblemanoibos"
            gr_donhang_json_new = llm_2_edit_gr_donhang_json(gr_donhang_json, gr_usertext)
            if gr_donhang_json == gr_donhang_json_new:
                gr_history += [{"role": "assistant", "content": "📄 Chưa có chỉnh sửa mới"}]
                gr_history += [{"role": "assistant", "content": "## 💬\nBạn có muốn chỉnh sửa gì thêm?"}]
            else:
                gr_history += [{"role": "assistant", "content": "📝 Chỉnh sửa hoàn thành"}]
                gr_history += [{"role": "assistant", "content": "## 💬\nBạn có muốn chỉnh sửa gì thêm?"}]
            gr_donhang_json = gr_donhang_json_new
            gr_donhang_table, gr_donhang_header = gr_donhang_json_2_gr_donhang_table(gr_donhang_json)
        else:
            gr_history += [{"role": "assistant", "content": "## 💬\nBạn có muốn chỉnh sửa gì thêm?"}]
    else:
        raise ValueError("⚠️ > fn_chat_4 > gr_chat_next is not TRUE/FALSE")
    return gr_history, gr_chat_next, gr_donhang_json, gr_donhang_table, gr_donhang_header

# Select option
def fn_select_manoibo(gr_history, gr_chat_next, gr_donhang_json, gr_donhang_table, gr_donhang_header, gr_manoibo_edit_id, evt: gr.SelectData):
    gr_chat_next = "FALSE"
    exec(evt.value)
    gr_donhang_table, gr_donhang_header = gr_donhang_json_2_gr_donhang_table(gr_donhang_json)
    gr_manoibo_edit_id = -6969
    gr_history += [{"role": "user", "content": re.search(r"'([^']*)'$", evt.value).group(1)}] # "gr_donhang_json['Danh sách vật tư'][0]['manoibo'] = 'VAS6C4'" -> "VAS6C4"
    return gr_history, gr_chat_next, gr_donhang_json, gr_donhang_table, gr_donhang_header, gr_manoibo_edit_id

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================

with gr.Blocks(title="NSG", theme=theme, head=head, css=css, analytics_enabled=False, fill_height=True, fill_width=True) as demo:
    with gr.Row():
        with gr.Column(scale=2):
            gr_userfile  = gr.File(file_count="single", label="Tải lên tập tin")
            gr_chat_next = gr.Textbox(max_lines=1, interactive=False, visible=False, label="gr_chat_next")
            gr_manoibo_edit_id = gr.Number(interactive=False, visible=False, label="gr_manoibo_edit_id", value=-6969)
            gr_usertext  = gr.Textbox(max_lines=1, interactive=False, visible=False, label="gr_usertext")
            gr_vdocrtext = gr.Textbox(max_lines=1, interactive=False, visible=False, label="gr_vdocrtext")
            gr_preview_1 = gr.Image(interactive=False, visible=False, label="Tập tin")
            gr_preview_2 = gr.TextArea(interactive=False, visible=False, label="Tập tin", lines=20)
        with gr.Column(scale=3, elem_id="gr_column_mid"):
            gr_history = gr.Chatbot(
                elem_id="gr_history", type="messages", group_consecutive_messages=False, container=True, label="Chatbot hỗ trợ tạo đơn hàng",
                value=[{"role": "assistant", "content": """Hello"""}]
            )
            gr_message = gr.MultimodalTextbox(
                elem_id="gr_message", file_count="single", placeholder="Nhập tin nhắn", submit_btn=True, autofocus=True, autoscroll=True, container=False
            )
        with gr.Column(scale=3):
            with gr.Column(variant="panel"):
                gr_donhang_header = gr.Markdown("### Thông tin đơn hàng")
                gr_donhang_table  = gr.DataFrame(headers=['Mã nội bộ', 'Vật tư', 'Xuất xứ', 'Giá trị', 'Đơn vị', 'Ghi chú'], show_row_numbers=True, interactive=False)
            gr_send_button        = gr.Button("Tạo đơn hàng", variant="primary", size="lg")
            gr_donhang_json       = gr.JSON(open=True, height="300px", visible=False, label="Thông tin đơn hàng (JSON)")

    gr.on(
        triggers=gr_userfile.upload,
        fn=fn_upload_1,
        inputs=[gr_history, gr_userfile],
        outputs=[gr_history, gr_preview_1, gr_preview_2],
        show_progress="hidden"
    ).then(
        fn=fn_upload_2,
        inputs=[gr_history, gr_userfile],
        outputs=[gr_history, gr_vdocrtext],
        show_progress="hidden"
    ).then(
        fn=fn_upload_3,
        inputs=[gr_history, gr_vdocrtext],
        outputs=[gr_history, gr_donhang_json, gr_donhang_table, gr_donhang_header],
        show_progress="hidden"
    ).then(
        fn=fn_upload_4,
        inputs=[],
        outputs=[gr_usertext],
        show_progress="hidden"
    ).then(
        fn=fn_chat_1,
        inputs=[gr_history, gr_message, gr_donhang_json],
        outputs=[gr_history, gr_message, gr_usertext, gr_chat_next],
        show_progress="hidden"
    ).then(
        fn=fn_chat_2,
        inputs=[gr_history, gr_chat_next, gr_donhang_json, gr_donhang_table, gr_donhang_header, gr_manoibo_edit_id, gr_usertext],
        outputs=[gr_history, gr_chat_next, gr_donhang_json, gr_donhang_table, gr_donhang_header, gr_manoibo_edit_id],
        show_progress="hidden"
    ).then(
        fn=fn_chat_3,
        inputs=[gr_history, gr_chat_next, gr_manoibo_edit_id, gr_donhang_json],
        outputs=[gr_history, gr_chat_next, gr_manoibo_edit_id],
        show_progress="hidden"
    ).then(
        fn=fn_chat_4,
        inputs=[gr_history, gr_chat_next, gr_donhang_json, gr_donhang_table, gr_donhang_header, gr_usertext],
        outputs=[gr_history, gr_chat_next, gr_donhang_json, gr_donhang_table, gr_donhang_header],
        show_progress="hidden"
    )

    gr.on(
        triggers=gr_message.submit,
        fn=fn_chat_1,
        inputs=[gr_history, gr_message, gr_donhang_json],
        outputs=[gr_history, gr_message, gr_usertext, gr_chat_next],
        show_progress="hidden"
    ).then(
        fn=fn_chat_2,
        inputs=[gr_history, gr_chat_next, gr_donhang_json, gr_donhang_table, gr_donhang_header, gr_manoibo_edit_id, gr_usertext],
        outputs=[gr_history, gr_chat_next, gr_donhang_json, gr_donhang_table, gr_donhang_header, gr_manoibo_edit_id],
        show_progress="hidden"
    ).then(
        fn=fn_chat_3,
        inputs=[gr_history, gr_chat_next, gr_manoibo_edit_id, gr_donhang_json],
        outputs=[gr_history, gr_chat_next, gr_manoibo_edit_id],
        show_progress="hidden"
    ).then(
        fn=fn_chat_4,
        inputs=[gr_history, gr_chat_next, gr_donhang_json, gr_donhang_table, gr_donhang_header, gr_usertext],
        outputs=[gr_history, gr_chat_next, gr_donhang_json, gr_donhang_table, gr_donhang_header],
        show_progress="hidden"
    )

    # Select option
    gr.on(
        triggers=gr_history.option_select,
        fn=fn_select_manoibo,
        inputs=[gr_history, gr_chat_next, gr_donhang_json, gr_donhang_table, gr_donhang_header, gr_manoibo_edit_id],
        outputs=[gr_history, gr_chat_next, gr_donhang_json, gr_donhang_table, gr_donhang_header, gr_manoibo_edit_id],
        show_progress="hidden"
    ).then(
        fn=fn_chat_3,
        inputs=[gr_history, gr_chat_next, gr_manoibo_edit_id, gr_donhang_json],
        outputs=[gr_history, gr_chat_next, gr_manoibo_edit_id],
        show_progress="hidden"
    ).then(
        fn=fn_chat_4,
        inputs=[gr_history, gr_chat_next, gr_donhang_json, gr_donhang_table, gr_donhang_header, gr_usertext],
        outputs=[gr_history, gr_chat_next, gr_donhang_json, gr_donhang_table, gr_donhang_header],
        show_progress="hidden"
    )

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================

if __name__ == "__main__":
    print("> http://localhost:1759")
    demo.launch(server_name="0.0.0.0", server_port=1759)