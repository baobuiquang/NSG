# ====================================================================================================
# ====================================================================================================
# ====================================================================================================

# Folder path -> All relative file paths
def get_all_filepaths(folderpath, extensions=[]):
    import os
    file_paths = []
    for root, dirs, files in os.walk(folderpath):
        for file_name in files:
            full_path = os.path.join(root, file_name)
            extension = os.path.splitext(full_path)[1].lstrip('.')
            if len(extensions) == 0 or extension in extensions:
                file_paths.append(full_path)
    return file_paths

# File path: '_test\\dir1\\subdir\\img_0.jpg' -> {'directory': '_test\\dir1\\subdir', 'filename': 'img_0', 'extension': 'jpg'}
def split_filepath(filepath):
    import os
    directory, file_with_ext = os.path.split(filepath)
    filename, extension = os.path.splitext(file_with_ext)
    extension = extension.lstrip('.')
    return {"directory": directory, "filename": filename, "extension": extension}

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================

# String -> List/Dict/Tuple/etc
def str2pydata(s):
    import ast
    return ast.literal_eval(s)

# JSON File -> Dict
def jsonfile2dict(pth):
    import json
    with open(pth, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

# String -> Dict (Advanced)
# Extract the JSON dictionary from LLM string result, return None if cannot extract
def str2dict_advanced(s):
    start = s.find('{')
    end = s.rfind('}')
    if start == -1 or end == -1 or start > end:
        return None
    else:
        res = s[start:end+1]
        res = str2pydata(res)
        if isinstance(res, dict):
            return res
        else:
            return None

# List -> String (Beautify for print)
def list2str(l):
    return "\n".join([str(e) for e in l])
# Dict -> String (Beautify for print)
def dict2str(d):
    import json
    return json.dumps(d, indent=4, ensure_ascii=False)

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================

def pil_2_ocv(img):
    import numpy as np
    import cv2
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
def ocv_2_pil(img):
    from PIL import Image
    import cv2
    return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

def show_ocv(img):
    import matplotlib.pyplot as plt
    import cv2
    plt.rcParams['figure.facecolor'] = 'grey'
    plt.figure(figsize=(8, 8))
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)); plt.axis('off'); plt.show()
def show_pil(img):
    import matplotlib.pyplot as plt
    plt.rcParams['figure.facecolor'] = 'grey'
    plt.imshow(img); plt.axis('off'); plt.show()
def show_ocv_multiple(list_imgs, list_titles=None):
    import matplotlib.pyplot as plt
    import cv2
    plt.rcParams['figure.facecolor'] = 'grey'
    n = len(list_imgs)
    fig, axes = plt.subplots(1, n, figsize=(16, 10))
    for i in range(n):
        (h, w) = list_imgs[i].shape[:2]
        axes[i].imshow(cv2.cvtColor(list_imgs[i], cv2.COLOR_BGR2RGB))
        if list_titles == None:
            axes[i].set_title(f"{w}x{h}")
        else:
            axes[i].set_title(list_titles[i])
        axes[i].axis('off')
    plt.tight_layout()
    plt.show()

def preprocess_document_image(img_ocv):
    import numpy as np
    import cv2

    def prepimg_contrast(img_ocv, goal_brightness=0.925):
        def get_brightness(img_ocv):
            b, g, r = cv2.split(img_ocv.astype(np.float32) / 255.0)
            brightness = np.mean(0.2126 * r + 0.7152 * g + 0.0722 * b)
            return round(float(brightness), 3)
        while get_brightness(img_ocv) < goal_brightness:
            img_ocv = cv2.convertScaleAbs(img_ocv, alpha=1.05, beta=0)
        return img_ocv

    def prepimg_resize(img_ocv, width=None, height=None):
        if width is None and height is None:
            raise ValueError("At least one of width or height must be specified.")
        (h, w) = img_ocv.shape[:2]
        # If only width is provided
        if height is None:
            ratio = width / float(w)
            dimension = (width, int(h * ratio))
        # If only height is provided
        elif width is None:
            ratio = height / float(h)
            dimension = (int(w * ratio), height)
        # If both width and height are provided
        else:
            dimension = (width, height)
        return cv2.resize(img_ocv, dimension, interpolation=cv2.INTER_LANCZOS4)

    def prepimg_denoise(img_ocv):
        return cv2.bilateralFilter(img_ocv, d=5, sigmaColor=35, sigmaSpace=35) # 9/75/75 -> 5/35/35

    def prepimg_cropblank(img_ocv, blank_pixel_keep=32):
        _, thresh = cv2.threshold(cv2.cvtColor(img_ocv, cv2.COLOR_BGR2GRAY), 128, 255, cv2.THRESH_BINARY)
        h, w = thresh.shape
        blank_x1 = 0
        blank_x2 = w
        blank_y1 = 0
        blank_y2 = h
        for c in range(0, w, 1):
            if set([r[c] for r in thresh]) != {255}:
                blank_x1 = max(c-blank_pixel_keep, 0)
                break
        for c in range(w-1, 0, -1):
            if set([r[c] for r in thresh]) != {255}:
                blank_x2 = min(c+blank_pixel_keep, w)
                break
        for r in range(0, h, 1):
            if set(thresh[r]) != {255}:
                blank_y1 = max(r-blank_pixel_keep, 0)
                break
        for r in range(h-1, 0, -1):
            if set(thresh[r]) != {255}:
                blank_y2 = min(r+blank_pixel_keep, h)
                break
        return img_ocv[blank_y1:blank_y2, blank_x1:blank_x2]

    img_ocv = prepimg_denoise(img_ocv)
    img_ocv = prepimg_contrast(img_ocv)
    img_ocv = prepimg_cropblank(img_ocv)
    img_ocv = prepimg_resize(img_ocv, width=1080)
    return img_ocv

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================