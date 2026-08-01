import os
import numpy as np
import onnxruntime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "silero_vad.onnx")
SAMPLE_RATE = 16000
WINDOW_SAMPLES = 512
CONTEXT_SAMPLES = 64


class SpeechDetector:
    """
    Minimal, torch-free wrapper around the Silero VAD ONNX model. Runs
    entirely on onnxruntime + numpy. The official silero-vad pip package
    requires torch + torchaudio (a ~1.2GB install) just to run this same
    11MB model — this bypasses that, using the identical model file.
    """

    def __init__(self, model_path=MODEL_PATH):
        opts = onnxruntime.SessionOptions()
        opts.inter_op_num_threads = 1
        opts.intra_op_num_threads = 1
        self.session = onnxruntime.InferenceSession(
            model_path, sess_options=opts, providers=["CPUExecutionProvider"]
        )
        self.reset_state()

    def reset_state(self):
        self._state = np.zeros((2, 1, 128), dtype=np.float32)
        self._context = np.zeros((1, CONTEXT_SAMPLES), dtype=np.float32)

    def process_chunk(self, chunk):
        """chunk: 1D float32 array of exactly WINDOW_SAMPLES samples.
        Returns the speech probability for this chunk (0.0-1.0)."""
        chunk = chunk.reshape(1, -1).astype(np.float32)
        x = np.concatenate([self._context, chunk], axis=1)
        ort_inputs = {
            "input": x,
            "state": self._state,
            "sr": np.array(SAMPLE_RATE, dtype=np.int64),
        }
        out, state = self.session.run(None, ort_inputs)
        self._state = state
        self._context = x[:, -CONTEXT_SAMPLES:]
        return float(out[0][0])


def get_speech_probabilities(samples, sample_rate=SAMPLE_RATE):
    """
    samples: 1D numpy float32 array, values in [-1, 1].
    Returns a list of (start_sample, end_sample, probability) per frame.
    """
    if sample_rate != SAMPLE_RATE:
        raise ValueError(f"Expected {SAMPLE_RATE}Hz audio, got {sample_rate}Hz")

    detector = SpeechDetector()
    results = []
    for start in range(0, len(samples), WINDOW_SAMPLES):
        chunk = samples[start:start + WINDOW_SAMPLES]
        if len(chunk) < WINDOW_SAMPLES:
            chunk = np.pad(chunk, (0, WINDOW_SAMPLES - len(chunk)))
        prob = detector.process_chunk(chunk)
        results.append((start, start + WINDOW_SAMPLES, prob))
    return results
