"""TimesFM forecasting integration for SOMS."""

from __future__ import annotations

import threading
from dataclasses import dataclass

import numpy as np


@dataclass
class ForecastResult:
    point_shape: tuple[int, ...]
    quantile_shape: tuple[int, ...]
    point_preview: list[list[float]]


class TimesFMService:
    """Lazy TimesFM 2.5 Torch model loader.

    The model is large and may download weights from Hugging Face on first use,
    so SOMS keeps it out of the normal startup path.
    """

    def __init__(self):
        self._model = None
        self._lock = threading.Lock()

    def available(self) -> tuple[bool, str]:
        try:
            import torch  # noqa: F401
            import timesfm
        except Exception as exc:
            return False, f"TimesFM dependencies are missing: {exc}"

        if not hasattr(timesfm, "TimesFM_2p5_200M_torch"):
            return False, (
                "Installed timesfm does not expose TimesFM_2p5_200M_torch. "
                "Install the torch extra or a compatible TimesFM release."
            )
        return True, "TimesFM is available."

    def _load_model(self):
        import torch
        import timesfm

        torch.set_float32_matmul_precision("high")
        model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(
            "google/timesfm-2.5-200m-pytorch"
        )
        model.compile(
            timesfm.ForecastConfig(
                max_context=1024,
                max_horizon=256,
                normalize_inputs=True,
                use_continuous_quantile_head=True,
                force_flip_invariance=True,
                infer_is_positive=True,
                fix_quantile_crossing=True,
            )
        )
        return model

    def get_model(self):
        with self._lock:
            if self._model is None:
                ok, message = self.available()
                if not ok:
                    raise RuntimeError(message)
                self._model = self._load_model()
            return self._model

    def demo_forecast(self, horizon: int = 12) -> ForecastResult:
        model = self.get_model()
        point_forecast, quantile_forecast = model.forecast(
            horizon=horizon,
            inputs=[
                np.linspace(0, 1, 100),
                np.sin(np.linspace(0, 20, 67)),
            ],
        )
        return ForecastResult(
            point_shape=tuple(point_forecast.shape),
            quantile_shape=tuple(quantile_forecast.shape),
            point_preview=np.round(point_forecast[:, : min(horizon, 5)], 4).tolist(),
        )

    def status_text(self) -> str:
        ok, message = self.available()
        loaded = self._model is not None
        return f"{message}\nModel loaded: {'yes' if loaded else 'no'}"

