import os
os.system('git clone https://github.com/facebookresearch/detectron2.git')
os.system('pip install -e detectron2')
os.system("git clone https://github.com/microsoft/unilm.git")
os.system("sed -i 's/from collections import Iterable/from collections.abc import Iterable/' unilm/dit/object_detection/ditod/table_evaluation/data_structure.py")
os.system("curl -LJ -o publaynet_dit-b_cascade.pth 'https://layoutlm.blob.core.windows.net/dit/dit-fts/publaynet_dit-b_cascade.pth?sv=2022-11-02&ss=b&srt=o&sp=r&se=2033-06-08T16:48:15Z&st=2023-06-08T08:48:15Z&spr=https&sig=a9VXrihTzbWyVfaIDlIT1Z0FoR1073VB0RLQUMuudD4%3D'")

import sys
sys.path.append("unilm")
sys.path.append("detectron2")

import cv2
import numpy as np
from unilm.dit.object_detection.ditod import add_vit_config

import torch

from detectron2.config import CfgNode as CN
from detectron2.config import get_cfg
from detectron2.utils.visualizer import ColorMode, Visualizer
from detectron2.data import MetadataCatalog
from detectron2.engine import DefaultPredictor

from huggingface_hub import hf_hub_download

import gradio as gr


# Step 1: instantiate config
cfg = get_cfg()
add_vit_config(cfg)
cfg.merge_from_file("cascade_dit_base.yml")

# Step 2: add model weights URL to config
filepath = hf_hub_download(repo_id="Sebas6k/DiT_weights", filename="publaynet_dit-b_cascade.pth", repo_type="model")
cfg.MODEL.WEIGHTS = filepath

# Step 3: set device
cfg.MODEL.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Step 4: define model
predictor = DefaultPredictor(cfg)


def analyze_image(img):
    md = MetadataCatalog.get(cfg.DATASETS.TEST[0])
    if cfg.DATASETS.TEST[0]=='icdar2019_test':
        md.set(thing_classes=["table"])
    else:
        md.set(thing_classes=["text","title","list","table","figure"])
    
    output = predictor(img)["instances"]
    v = Visualizer(img[:, :, ::-1],
                    md,
                    scale=1.0,
                    instance_mode=ColorMode.SEGMENTATION)
    result = v.draw_instance_predictions(output.to("cpu"))
    result_image = result.get_image()[:, :, ::-1]
    
    return result_image


  
title = "Interactive demo: Document Layout Analysis with DiT"
description = "Demo for Microsoft's DiT, the Document Image Transformer for state-of-the-art document understanding tasks. This particular model is fine-tuned on PubLayNet, a large dataset for document layout analysis (read more at the links below). To use it, simply upload an image or use the example image below and click 'Submit'. Results will show up in a few seconds. If you want to make the output bigger, right-click on it and select 'Open image in new tab'."
article = "<p style='text-align: center'><a href='https://arxiv.org/abs/2203.02378' target='_blank'>Paper</a> | <a href='https://github.com/microsoft/unilm/tree/master/dit' target='_blank'>Github Repo</a></p> | <a href='https://huggingface.co/docs/transformers/master/en/model_doc/dit' target='_blank'>HuggingFace doc</a></p>"
examples =[['publaynet_example.jpeg']]
css = ".output-image, .input-image, .image-preview {height: 600px !important}"


iface = gr.Interface(
    fn=analyze_image,
    inputs=gr.Image(type="numpy", label="document image"),
    outputs=gr.Image(type="numpy", label="annotated document"),
    title=title,
    description=description,
    examples=examples,
    article=article,
    css=css,
)

iface.queue(5).launch(debug=True)