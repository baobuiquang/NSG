# VOCR - VietOCR (Text Recognition)

# ----- Usage -----
# from pkg.VDOCR.VOCR.VOCR import Process_VOCR
# text = Process_VOCR("_test/img_18.jpg")

# ====================================================================================================

from onnxruntime import InferenceSession
from PIL import Image
import numpy as np
import math
import cv2

# ====================================================================================================

class VOCR_Vocab():
    def __init__(self, chars):
        self.pad = 0
        self.go = 1
        self.eos = 2
        self.mask_token = 3
        self.chars = chars
        self.c2i = {c:i+4 for i, c in enumerate(chars)}
        self.i2c = {i+4:c for i, c in enumerate(chars)}
        self.i2c[0] = '<pad>'
        self.i2c[1] = '<sos>'
        self.i2c[2] = '<eos>'
        self.i2c[3] = '*'
    def encode(self, chars):
        return [self.go] + [self.c2i[c] for c in chars] + [self.eos]
    def decode(self, ids):
        first = 1 if self.go in ids else 0
        last = ids.index(self.eos) if self.eos in ids else None
        sent = ''.join([self.i2c[i] for i in ids[first:last]])
        return sent
    def __len__(self):
        return len(self.c2i) + 4
    def batch_decode(self, arr):
        texts = [self.decode(ids) for ids in arr]
        return texts
    def __str__(self):
        return self.chars

def VOCR_process_input(image, image_height, image_min_width, image_max_width):
    def VOCR_process_image(image, image_height, image_min_width, image_max_width):
        def VOCR_resize(w, h, expected_height, image_min_width, image_max_width):
            new_w = int(expected_height * float(w) / float(h))
            round_to = 10
            new_w = math.ceil(new_w/round_to)*round_to
            new_w = max(new_w, image_min_width)
            new_w = min(new_w, image_max_width)
            return new_w, expected_height
        img = image.convert('RGB')
        w, h = img.size
        new_w, image_height = VOCR_resize(w, h, image_height, image_min_width, image_max_width)
        img = img.resize((new_w, image_height), Image.LANCZOS)
        img = np.asarray(img).transpose(2,0, 1)
        img = img/255
        return img
    img = VOCR_process_image(image, image_height, image_min_width, image_max_width)
    img = img[np.newaxis, ...]
    return img.astype(np.float32)

# ====================================================================================================

VOCR_CFG = { "vocab": "aAàÀảẢãÃáÁạẠăĂằẰẳẲẵẴắẮặẶâÂầẦẩẨẫẪấẤậẬbBcCdDđĐeEèÈẻẺẽẼéÉẹẸêÊềỀểỂễỄếẾệỆfFgGhHiIìÌỉỈĩĨíÍịỊjJkKlLmMnNoOòÒỏỎõÕóÓọỌôÔồỒổỔỗỖốỐộỘơƠờỜởỞỡỠớỚợỢpPqQrRsStTuUùÙủỦũŨúÚụỤưƯừỪửỬữỮứỨựỰvVwWxXyYỳỲỷỶỹỸýÝỵỴzZ0123456789!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~ ", "device": "cpu", "seq_modeling": "seq2seq", "transformer": { "encoder_hidden": 256, "decoder_hidden": 256, "img_channel": 256, "decoder_embedded": 256, "dropout": 0.1 }, "optimizer": { "max_lr": 0.001, "pct_start": 0.1 }, "trainer": { "batch_size": 32, "print_every": 200, "valid_every": 4000, "iters": 100000, "export": "mymodel.pth", "checkpoint": "mycheckpoint.pth", "log": "train.log", "metrics": None }, "dataset": { "name": "data", "data_root": "img/", "train_annotation": "annotation_train.txt", "valid_annotation": "annotation_val_small.txt", "image_height": 32, "image_min_width": 32, "image_max_width": 512 }, "dataloader": { "num_workers": 3, "pin_memory": True }, "aug": { "image_aug": True, "masked_language_model": True }, "predictor": { "beamsearch": False }, "quiet": False, "pretrain": "VDOCR/model/VOCR/vgg_seq2seq.pth", "weights": "VDOCR/model/VOCR/vgg_seq2seq.pth", "backbone": "vgg19_bn", "cnn": { "ss": [[2, 2], [2, 2], [2, 1], [2, 1], [1, 1]], "ks": [[2, 2], [2, 2], [2, 1], [2, 1], [1, 1]], "hidden": 256, } }

vocr_vocab = VOCR_Vocab(VOCR_CFG['vocab'])

ONNX_VOCR_CNN = InferenceSession("pkg/VDOCR/VOCR/model/cnn.onnx")
ONNX_VOCR_ENC = InferenceSession("pkg/VDOCR/VOCR/model/encoder.onnx")
ONNX_VOCR_DEC = InferenceSession("pkg/VDOCR/VOCR/model/decoder.onnx")

def Process_VOCR(img_path, max_seq_length=128, sos_token=1, eos_token=2):

    # Convert to PIL image
    if isinstance(img_path, str):             img_pil = Image.open(img_path)
    elif isinstance(img_path, np.ndarray):    img_pil = Image.fromarray(cv2.cvtColor(img_path, cv2.COLOR_BGR2RGB))
    elif isinstance(img_path, Image.Image):   img_pil = img_path
    elif img_path == None:                    return ""
    else:                                     raise ValueError("⚠️ VOCR > Not image path, PIL image, or OpenCV image")
    
    # Process input
    img_pil_processed = VOCR_process_input(img_pil, VOCR_CFG['dataset']['image_height'], VOCR_CFG['dataset']['image_min_width'], VOCR_CFG['dataset']['image_max_width'])  
    
    # CNN
    cnn_input = {ONNX_VOCR_CNN.get_inputs()[0].name: img_pil_processed}
    src = ONNX_VOCR_CNN.run(None, cnn_input)

    # Encoder
    encoder_input = {ONNX_VOCR_ENC.get_inputs()[0].name: src[0]}
    encoder_outputs, hidden = ONNX_VOCR_ENC.run(None, encoder_input)

    # Decoder
    max_length = 0
    translated_sentence = [[sos_token] * len(img_pil_processed)]
    while max_length <= max_seq_length and not all(np.any(np.asarray(translated_sentence).T == eos_token, axis=1)):
        tgt_inp = translated_sentence
        decoder_input = { ONNX_VOCR_DEC.get_inputs()[0].name: tgt_inp[-1], ONNX_VOCR_DEC.get_inputs()[1].name: hidden, ONNX_VOCR_DEC.get_inputs()[2].name: encoder_outputs }
        output, hidden, _ = ONNX_VOCR_DEC.run(None, decoder_input)
        output = np.expand_dims(output, axis=1)
        indices = np.argpartition(output, -1, axis=-1)[...,-1:][:, -1, 0].tolist()
        translated_sentence.append(indices)
        max_length += 1
        del output
    translated_sentence = np.asarray(translated_sentence).T
    vocr_text = vocr_vocab.decode(translated_sentence[0].tolist())

    # # # ---------------------------------------------------------------------------------------------------- Just to visualize
    # from pkg.UTILS.UTILS import show_pil
    # show_pil(img_pil)
    # print(vocr_text)
    # # # ----------------------------------------------------------------------------------------------------
    
    return vocr_text