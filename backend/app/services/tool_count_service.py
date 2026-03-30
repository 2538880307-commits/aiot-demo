from collections import Counter
from io import BytesIO
from pathlib import Path

from PIL import Image
from ultralytics import YOLO

from app.core.config import get_settings


class ToolCountService:
    def __init__(self) -> None:
        settings = get_settings()
        self.model_path = Path(settings.tool_count_model_path)
        self.conf = settings.tool_count_conf
        self.iou = settings.tool_count_iou
        self._model = None
        self._load_error = None

    def _ensure_model(self) -> YOLO:
        if self._model is not None:
            return self._model

        if self._load_error is not None:
            raise RuntimeError(self._load_error)

        if not self.model_path.exists():
            self._load_error = f'模型文件不存在: {self.model_path}'
            raise RuntimeError(self._load_error)

        try:
            self._model = YOLO(str(self.model_path))
            return self._model
        except Exception as exc:  # pragma: no cover
            self._load_error = f'模型加载失败: {exc}'
            raise RuntimeError(self._load_error) from exc

    def detect(self, image_bytes: bytes, filename: str) -> dict:
        model = self._ensure_model()

        image = Image.open(BytesIO(image_bytes)).convert('RGB')
        results = model.predict(source=image, conf=self.conf, iou=self.iou, verbose=False)
        result = results[0]

        detections = []
        name_counter: Counter[str] = Counter()

        boxes = result.boxes
        if boxes is not None and len(boxes) > 0:
            cls_list = boxes.cls.tolist()
            conf_list = boxes.conf.tolist()
            names = result.names if hasattr(result, 'names') else {}

            for cls_id, conf in zip(cls_list, conf_list):
                label = names.get(int(cls_id), str(int(cls_id))) if isinstance(names, dict) else str(int(cls_id))
                name_counter[label] += 1
                detections.append(
                    {
                        'class_id': int(cls_id),
                        'label': label,
                        'confidence': round(float(conf), 4),
                    }
                )

        return {
            'ready': True,
            'message': '识别完成',
            'total_count': int(sum(name_counter.values())),
            'by_class': dict(name_counter),
            'detections': detections,
            'filename': filename,
        }


tool_count_service = ToolCountService()
