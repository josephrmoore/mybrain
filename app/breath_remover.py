import numpy as np
import soundfile as sf

import voice_detection

FRAME_SAMPLES = voice_detection.WINDOW_SAMPLES  # 512 samples at 16kHz VAD rate
SPEECH_PROB_THRESHOLD = 0.5
SILENCE_RMS_THRESHOLD = 0.01
NOISE_REPLACEMENT_SECONDS = 0.5


def _rms(chunk):
    if len(chunk) == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(chunk))))


def classify_frames(samples_16k):
    """
    Classifies each FRAME_SAMPLES-sized frame of 16kHz audio as one of
    'speech', 'silence', or 'noise'. Returns a list of (start, end, label)
    at the VAD's native frame resolution — not yet merged into segments.
    """
    probs = voice_detection.get_speech_probabilities(samples_16k)
    labels = []
    for start, end, prob in probs:
        if prob >= SPEECH_PROB_THRESHOLD:
            label = "speech"
        else:
            chunk = samples_16k[start:end]
            label = "silence" if _rms(chunk) < SILENCE_RMS_THRESHOLD else "noise"
        labels.append((start, end, label))
    return labels


def merge_segments(frame_labels):
    """Merges consecutive frames sharing the same label into one segment."""
    if not frame_labels:
        return []

    segments = []
    seg_start, seg_end, seg_label = frame_labels[0]
    for start, end, label in frame_labels[1:]:
        if label == seg_label:
            seg_end = end
        else:
            segments.append((seg_start, seg_end, seg_label))
            seg_start, seg_end, seg_label = start, end, label
    segments.append((seg_start, seg_end, seg_label))
    return segments


def render_cleaned_audio(samples, segments, sample_rate, noise_replacement_seconds=NOISE_REPLACEMENT_SECONDS):
    """
    Given the ORIGINAL samples (at their real sample rate, which may
    differ from the 16kHz used for VAD classification) and segments
    expressed in 16kHz-frame sample indices, builds the cleaned output:
    speech and silence are copied verbatim, noise is replaced with a
    fixed-duration block of true silence.

    segments are in 16kHz sample space; this function scales them to
    the real sample_rate before slicing the real samples.
    """
    scale = sample_rate / voice_detection.SAMPLE_RATE
    replacement_len = int(noise_replacement_seconds * sample_rate)
    replacement_block = np.zeros(replacement_len, dtype=samples.dtype)

    output_chunks = []
    for start_16k, end_16k, label in segments:
        real_start = int(start_16k * scale)
        real_end = int(end_16k * scale)
        real_end = min(real_end, len(samples))
        if real_start >= real_end:
            continue

        if label == "noise":
            output_chunks.append(replacement_block)
        else:
            output_chunks.append(samples[real_start:real_end])

    if not output_chunks:
        return np.array([], dtype=samples.dtype)
    return np.concatenate(output_chunks)


def process_file(input_path, output_path):
    """
    Loads input_path, removes non-speech/non-silence noise (breaths,
    clicks, pops, etc.), replacing each occurrence with a fixed 0.5s
    silence block, and writes the result to output_path. The original
    file is never modified.
    """
    samples, sample_rate = sf.read(input_path, dtype="float32", always_2d=False)
    if samples.ndim > 1:
        samples = samples.mean(axis=1)  # downmix to mono for processing

    if sample_rate == voice_detection.SAMPLE_RATE:
        samples_16k = samples
    else:
        # resample for VAD analysis only — segments get scaled back to
        # the real sample_rate in render_cleaned_audio
        duration = len(samples) / sample_rate
        target_len = int(duration * voice_detection.SAMPLE_RATE)
        samples_16k = np.interp(
            np.linspace(0, len(samples), target_len, endpoint=False),
            np.arange(len(samples)),
            samples,
        ).astype(np.float32)

    frame_labels = classify_frames(samples_16k)
    segments = merge_segments(frame_labels)
    cleaned = render_cleaned_audio(samples, segments, sample_rate)

    sf.write(output_path, cleaned, sample_rate)
    return {"input": input_path, "output": output_path, "segments": len(segments)}
