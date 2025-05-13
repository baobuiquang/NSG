# VDOCR - Vietnamese Document OCR

# ----- Usage -----
# from pkg.VDOCR.VDOCR import Process_VDOCR
# filepath = "_test/img_0.jpg"
# filepath = "_test/pdf_1.pdf"
# filepath = "_test/docx_1.docx"
# filepath = "_test/xlsx_1.xlsx"
# filepath = "_test/txt_1.txt"
# print(Process_VDOCR(filepath))

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================

from pkg.VDOCR.TDET.TDET import Process_TDET
from pkg.VDOCR.POCR.POCR import Process_POCR
from pkg.VDOCR.VOCR.VOCR import Process_VOCR
import pkg.UTILS.UTILS as UTILS
import cv2

from pymupdf import Document as Document_Parser_PDF
from openpyxl import load_workbook as Document_Parser_XLS
from docx import Document as Document_Parser_DOC

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================

# bb1: The inside bbox - bb2: The outside bbox
def VDOCR_bbox_in_bbox_ratio(bb1, bb2):
    def bbox_area(bb):
        return (bb[2] - bb[0]) * (bb[3] - bb[1])
    def bbox_overlap(bb1, bb2):
        x1 = max(bb1[0], bb2[0])
        y1 = max(bb1[1], bb2[1])
        x2 = min(bb1[2], bb2[2])
        y2 = min(bb1[3], bb2[3])
        if x1>=x2 or y1>=y2:
            return 0
        else:
            return bbox_area((x1, y1, x2, y2))
    if bb1[0]>=bb2[0] and bb1[2]<=bb2[2] and bb1[1]>=bb2[1] and bb1[3]<=bb2[3]:
        return 1.0
    if (bb1[0]>bb2[0] and bb1[0]>bb2[2] and bb1[2]>bb2[0] and bb1[2]>bb2[2]) or (bb1[0]<bb2[0] and bb1[0]<bb2[2] and bb1[2]<bb2[0] and bb1[2]<bb2[2]):
        return 0.0
    if (bb1[1]>bb2[1] and bb1[1]>bb2[3] and bb1[3]>bb2[1] and bb1[3]>bb2[3]) or (bb1[1]<bb2[1] and bb1[1]<bb2[3] and bb1[3]<bb2[1] and bb1[3]<bb2[3]):
        return 0.0
    return bbox_overlap(bb1, bb2) / bbox_area(bb1)
# bb1: The text bbox - bb2: The table cell bbox
def VDOCR_get_bbox_cut_from_overlap(bb1, bb2):
    return (max(bb1[0],bb2[0]), max(bb1[1],bb2[1]), min(bb1[2],bb2[2]), min(bb1[3],bb2[3]))
def VDOCR_bboxes_2_rowclusters(texts_bboxes):
    if texts_bboxes == []:
        return []
    else:
        def VDOCR_clustering_idx(ls, max_distance=5):
            import numpy as np
            # ls: a list of numbers
            # max_distance: max distance between 2 numbers in 1 cluster
            # Return clusters, each cluster contains indexs of the numbers in original list
            ls = np.array(ls)
            sorted_indices = np.argsort(ls)
            split_points = np.where(np.diff(ls[sorted_indices]) > max_distance)[0] + 1
            clusters = np.split(sorted_indices, split_points)
            return clusters
        # Cluster the text boxes based on their row indexes
        texts_bboxes_clusters = [[texts_bboxes[idx] for idx in row_cluster_idxs] for row_cluster_idxs in VDOCR_clustering_idx([text_bbox[1] for text_bbox in texts_bboxes])]
        # Sort each cluster left-to-right (by x-coordinate)
        texts_bboxes_clusters = [sorted(cluster, key=lambda e1: e1[0]) for cluster in texts_bboxes_clusters]
        # Sort clusters top-to-bottom (by y-coordinate of the first element in each cluster)
        texts_bboxes_clusters.sort(key=lambda cluster: cluster[0][1])
        # Return
        return texts_bboxes_clusters
def VDOCR_get_bg_color(img_ocv, groups=25):
    import numpy as np
    import cv2
    try:
        gray = cv2.cvtColor(img_ocv, cv2.COLOR_BGR2GRAY)
        hist = cv2.calcHist([gray], [0], None, [groups], [0, 256])
        dominant_group = np.argmax(hist)
        background_brightness = int((dominant_group + 0.5) * (256 / groups))
        return (background_brightness,) * 3
    except Exception as error:
        print(f"⚠️ VDOCR > VDOCR_get_bg_color > Error: {error}")
        return (250, 250, 250)
def VDOCR_add_blank_margin(img_ocv, margin_ratio=0.1):
    import math
    import cv2
    h, w = img_ocv.shape[:2]
    padding = math.ceil(h * margin_ratio)
    padding_color = VDOCR_get_bg_color(img_ocv)
    return cv2.copyMakeBorder(img_ocv, padding, padding, padding, padding, cv2.BORDER_CONSTANT, value=padding_color)

def Process_VOCR_with_blank_margin(img_ocv, bbox, PDF_parser_support):
    if PDF_parser_support == None:
        x1,y1,x2,y2 = bbox
        return Process_VOCR(VDOCR_add_blank_margin(img_ocv[y1:y2,x1:x2]))
    else:
        res = []
        for e in PDF_parser_support:
            if VDOCR_bbox_in_bbox_ratio(e['bbox'], bbox) > 0.66:
                res.append(e['text'])
        return " ".join(res)

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================

def VDOCR_TXT(filepath):
    txt_content = ""
    with open(filepath, 'r', encoding='utf-8') as f:
        txt_content = f.read()
    return txt_content.strip()

def VDOCR_XLS(filepath):
    workbook = Document_Parser_XLS(filepath)
    xlsx_content = []
    try:
        sheet = workbook.active
        for row in sheet.iter_rows(values_only=True):
            sheet_row = []
            for col in row:
                sheet_row.append(str(col) if col else "")
            xlsx_content.append(sheet_row)
        for e in sheet.merged_cells.ranges:
            c1,r1,c2,r2 = e.bounds[0]-1, e.bounds[1]-1, e.bounds[2]-1, e.bounds[3]-1
            merged_text = xlsx_content[r1][c1]
            tmp_h = len(list(set([e_tmp for e_tmp in xlsx_content[r1] if e_tmp != ""])))
            tmp_v = len(list(set([e_tmp[c1] for e_tmp in xlsx_content if e_tmp[c1] != ""])))
            fill_merged_cells = True
            if c1==c2:
                if tmp_v == 1:
                    fill_merged_cells = False
            elif r1==r2:
                if tmp_h == 1:
                    fill_merged_cells = False
            else:
                if tmp_h == 1 and tmp_v == 1:
                    fill_merged_cells = False
            if fill_merged_cells:
                for r in range(r1,r2+1):
                    for c in range(c1,c2+1):
                        xlsx_content[r][c] = merged_text
    finally:
        workbook.close()
    final_text = ""
    for row in xlsx_content:
        final_text += "| " + " | ".join(row) + " |\n"
    return final_text.strip()

def VDOCR_DOC(filepath):
    docx_content = []
    with open(filepath, 'rb') as file:
        doc = Document_Parser_DOC(file)
        # Extract tables
        for table in doc.tables:
            table_data = []
            for row in table.rows:
                row_data = []
                for cell in row.cells:
                    row_data.append(cell.text.strip())
                table_data.append(row_data)
            docx_content.append(table_data)
        # Extract paragraphs
        for para in doc.paragraphs:
            if para.text.strip():
                docx_content.append(para.text)
    final_text = ""
    for e in docx_content:
        if isinstance(e, list): # Table
            final_text += "\n"
            for row in e:
                final_text += "| " + " | ".join(row) + " |\n"
            final_text += "\n"
        elif isinstance(e, str): # Paragraph
            final_text += e + "\n"
    return final_text.strip()

def VDOCR_IMG_PDF(filepath):
    # -------------------- img_ocv & PDF_parser_support
    PDF_parser_support = None
    if UTILS.split_filepath(filepath)['extension'] in UTILS.FILE_EXTENSION_PDF:
        PDF2IMG_ZOOM = 4.0
        with Document_Parser_PDF(filepath) as PDF_document:
            if len(PDF_document) > 1:
                raise ValueError("⚠️ VDOCR > Multiple-pages PDF not supported yet")
            else:
                page = PDF_document[0]
                words = page.get_text("words")
                img_ocv = UTILS.pil_2_ocv(page.get_pixmap(dpi=int(72*PDF2IMG_ZOOM)).pil_image())
                # Case 1: PDF is digital
                if len(words) > 9: # <----- Should change this number or use another approach
                    PDF_parser_support = [{
                        "text": w[4],
                        "bbox": (int(w[0]*PDF2IMG_ZOOM), int(w[1]*PDF2IMG_ZOOM), int(w[2]*PDF2IMG_ZOOM), int(w[3]*PDF2IMG_ZOOM))
                    } for w in words]
                # Case 2: PDF is image
                else:
                    print(f"⚠️ VDOCR > Warning: PDF is not digital > Force OCR")
                    PDF_parser_support = None
    elif UTILS.split_filepath(filepath)['extension'] in UTILS.FILE_EXTENSION_IMG:
        img_ocv = cv2.imread(filepath)
        img_ocv = UTILS.preprocess_document_image(img_ocv)
    else:
        raise ValueError(f"⚠️ VDOCR_IMG_PDF > *.{UTILS.split_filepath(filepath)['extension']} > File type not supported")
    # -------------------- tables & texts_bboxes
    if PDF_parser_support == None:
        texts_bboxes = Process_POCR(img_ocv)
    else:
        texts_bboxes = [e['bbox'] for e in PDF_parser_support]
    tables = Process_TDET(img_ocv)
    for i1, tbl in enumerate(tables):
        for i2, cell in enumerate(tbl):
            tables[i1][i2]['text_bboxes'] = []
    # -------------------- rowclusters_table (inside tables)
    texts_bboxes_nontable = []
    for pdf_parser_support in texts_bboxes:
        _flag_inside_table = False
        for i1, tbl in enumerate(tables):
            for i2, cell in enumerate(tbl):
                cell_bbox = cell['bbox']
                if VDOCR_bbox_in_bbox_ratio(pdf_parser_support, cell_bbox) > 0.25:
                    _flag_inside_table = True
                    tables[i1][i2]['text_bboxes'].append(VDOCR_get_bbox_cut_from_overlap(pdf_parser_support, cell_bbox))
        if _flag_inside_table == False:
            texts_bboxes_nontable.append(pdf_parser_support)

    for i1, tbl in enumerate(tables):
        for i2, cell in enumerate(tbl):
            tables[i1][i2]['rowclusters'] = VDOCR_bboxes_2_rowclusters(cell['text_bboxes'])
    # -------------------- rowclusters_nontable
    rowclusters_nontable = VDOCR_bboxes_2_rowclusters(texts_bboxes_nontable)
    # -------------------- ocr_tables
    ocr_tables = []
    for tbl in tables:
        n_rows = max(e['row_id'] for e in tbl) + 1
        n_cols = max(e['col_id'] for e in tbl) + 1
        tbl_text = [[[] for _ in range(n_cols)] for _ in range(n_rows)]
        for cell in tbl:
            row_id = cell['row_id']
            col_id = cell['col_id']
            row_span = cell['row_span']
            col_span = cell['col_span']
            cell_text = []
            for rowcluster in cell['rowclusters']:
                for x1,y1,x2,y2 in rowcluster:
                    cell_text.append(Process_VOCR_with_blank_margin(img_ocv, (x1,y1,x2,y2), PDF_parser_support))
            for i1r in range(row_span):
                for i1c in range(col_span):
                    tbl_text[row_id+i1r][col_id+i1c] = cell_text
        ocr_tables.append({
            "text": "\n".join(["| "+" | ".join([" ".join([e for e in col]) for col in row])+" |" for row in tbl_text]),
            "y1": min(e['bbox'][1] for e in tbl)
        })
    # -------------------- ocr_nontables
    ocr_nontables = []
    for rowcluster in rowclusters_nontable:
        row_content = []
        for x1,y1,x2,y2 in rowcluster:
            row_content.append(Process_VOCR_with_blank_margin(img_ocv, (x1,y1,x2,y2), PDF_parser_support))
        ocr_nontables.append({
            "text": " ".join(row_content),
            "y1": min(e[1] for e in rowcluster)
        })
    # -------------------- ocr_all
    ocr_all = sorted(ocr_tables + ocr_nontables, key=lambda e: e['y1'])
    ocr_text = "\n".join([e['text'] for e in ocr_all])
    return ocr_text.strip()

    # # # ---------------------------------------------------------------------------------------------------- Just to visualize
    # img_tmp = img_ocv.copy()
    # for tbl in tables:
    #     for cell in tbl:
    #         for i1, rowcluster in enumerate(cell['rowclusters']):
    #             for i2, (x1,y1,x2,y2) in enumerate(rowcluster):
    #                 cv2.rectangle(img_tmp, (x1,y1), (x2,y2), (0,0,255), 2)
    #                 cv2.putText(img_tmp, f"{i1}-{i2}", (x2,y1), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
    # for i1, rowcluster in enumerate(rowclusters_nontable):
    #     for i2, (x1,y1,x2,y2) in enumerate(rowcluster):
    #         cv2.rectangle(img_tmp, (x1,y1), (x2,y2), (255,0,0), 2)
    #         cv2.putText(img_tmp, f"{i1}-{i2}", (x2,y1), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 2)
    # UTILS.show_ocv(img_tmp)
    # # # ----------------------------------------------------------------------------------------------------

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================

def Process_VDOCR(filepath):
    if UTILS.split_filepath(filepath)['extension'] in UTILS.FILE_EXTENSION_PDF:
        return VDOCR_IMG_PDF(filepath)
    elif UTILS.split_filepath(filepath)['extension'] in UTILS.FILE_EXTENSION_IMG:
        return VDOCR_IMG_PDF(filepath)
    elif UTILS.split_filepath(filepath)['extension'] in UTILS.FILE_EXTENSION_TXT:
        return VDOCR_TXT(filepath)
    elif UTILS.split_filepath(filepath)['extension'] in UTILS.FILE_EXTENSION_DOC:
        return VDOCR_DOC(filepath)
    elif UTILS.split_filepath(filepath)['extension'] in UTILS.FILE_EXTENSION_XLS:
        return VDOCR_XLS(filepath)
    else:
        raise ValueError(f"⚠️ VDOCR > *.{UTILS.split_filepath(filepath)['extension']} > File type not supported")

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================