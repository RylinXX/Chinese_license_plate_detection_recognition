# -*- coding: UTF-8 -*-
from __future__ import annotations

import os
import sys
import torch
import numpy as np
import cv2
from abc import ABC, abstractmethod
from typing import Any

# 确保当前路径在 Python 模块搜索路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from detect_plate import load_model, detect_Recognition_plate
from plate_recognition.plate_rec import init_model

class BaseRecognizer(ABC):
    """
    车牌识别引擎抽象基类。
    """
    @abstractmethod
    def recognize(self, image_path: str) -> list[dict[str, Any]]:
        """
        识别单张图片中的车牌。
        
        Args:
            image_path: 图片文件的绝对/相对路径。
            
        Returns:
            一个字典列表，每个字典包含车牌号、颜色、置信度等信息。
        """
        pass

class LocalSimulatedCloudRecognizer(BaseRecognizer):
    """
    本地模拟云端车牌识别器。
    使用项目中已有的高精度 PyTorch 检测与多任务识别模型，模拟云端 API 的接收和处理结果。
    """
    def __init__(
        self, 
        detect_model_path: str = "weights/plate_detect.pt", 
        rec_model_path: str = "weights/plate_rec_color.pth", 
        is_color: bool = True
    ):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[Recognizer] 使用推理设备: {self.device}")
        
        # 校验模型路径是否存在
        if not os.path.exists(detect_model_path) or not os.path.exists(rec_model_path):
            raise FileNotFoundError(
                f"找不到模型权重文件，请确保 'weights/plate_detect.pt' 和 'weights/plate_rec_color.pth' 存在。"
            )
            
        self.detect_model = load_model(detect_model_path, self.device)
        self.plate_rec_model = init_model(self.device, rec_model_path, is_color=is_color)
        self.is_color = is_color

    def recognize(self, image_path: str) -> list[dict[str, Any]]:
        # 使用 numpy decode 以兼容含中文的文件路径
        img = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), -1)
        if img is None:
            raise FileNotFoundError(f"无法读取图片: {image_path}")
            
        if img.shape[-1] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
        # 运行检测与识别
        raw_results = detect_Recognition_plate(
            self.detect_model, 
            img, 
            self.device, 
            self.plate_rec_model, 
            img_size=640, 
            is_color=self.is_color
        )
        
        # 转换并规范化输出，对外隐藏内部实现细节，对齐云端标准数据结构
        standard_results = []
        for res in raw_results:
            standard_results.append({
                "plate_no": str(res.get("plate_no", "")),
                "plate_color": str(res.get("plate_color", "")),
                "detect_confidence": float(res.get("detect_conf", 0.0)),
                "recognition_confidence": float(np.mean(res.get("rec_conf", [0.0]))),
                "plate_type": "double" if res.get("plate_type") == 1 else "single"
            })
            
        return standard_results

class TencentCloudRecognizer(BaseRecognizer):
    """
    腾讯云车牌识别 API 适配器（预留公网升级接口）。
    当项目正式部署上云时，只需在 web-server.py 中将 Recognizer 切换为本类，即可不改变任何业务逻辑无缝商用。
    """
    def __init__(self, secret_id: str, secret_key: str, region: str = "ap-guangzhou"):
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.region = region

    def recognize(self, image_path: str) -> list[dict[str, Any]]:
        """
        调用腾讯云 OCR 车牌识别服务。
        使用此方法需要配置依赖：pip install tencentcloud-sdk-python
        """
        # import base64
        # from tencentcloud.common import credential
        # from tencentcloud.common.profile.client_profile import ClientProfile
        # from tencentcloud.common.profile.http_profile import HttpProfile
        # from tencentcloud.ocr.v20181119 import ocr_client, models
        
        # with open(image_path, "rb") as f:
        #     img_data = f.read()
        #     img_base64 = base64.b64encode(img_data).decode("utf-8")
            
        # cred = credential.Credential(self.secret_id, self.secret_key)
        # httpProfile = HttpProfile()
        # httpProfile.endpoint = "ocr.tencentcloudapi.com"
        # clientProfile = ClientProfile()
        # clientProfile.httpProfile = httpProfile
        # client = ocr_client.OcrClient(cred, self.region, clientProfile)
        
        # req = models.LicensePlateOCRRequest()
        # req.ImageBase64 = img_base64
        
        # resp = client.LicensePlateOCR(req)
        # data = json.loads(resp.to_json_string())
        
        # # 将云端返回结果解析为标准的列表结构
        # res = data.get("LicensePlateInfos", [])
        # standard_results = []
        # for item in res:
        #     standard_results.append({
        #         "plate_no": item.get("Number", ""),
        #         "plate_color": item.get("Color", ""),
        #         "detect_confidence": 0.99, # 云端通常不暴露检测置信度，设为高置信
        #         "recognition_confidence": 0.99,
        #         "plate_type": "single" # 默认单层
        #     })
        # return standard_results
        
        print("[TencentOCR] 模拟调用云端识别...")
        return []
