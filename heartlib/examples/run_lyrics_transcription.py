from heartlib import HeartTranscriptorPipeline
import argparse
import torch


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, required=True)
    parser.add_argument("--music_path", type=str, default="./assets/output.mp3")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    pipe = HeartTranscriptorPipeline.from_pretrained(
        args.model_path,
        device=torch.device("cuda"),
        dtype=torch.float16,
    )
    with torch.no_grad():
        result = pipe(
            args.music_path,
            **{
                "max_new_tokens": 256,
                "num_beams": 2,
                "task": "transcribe",
                "condition_on_prev_tokens": False,
                "compression_ratio_threshold": 1.8,
                "temperature": (0.0, 0.1, 0.2, 0.4),
                "logprob_threshold": -1.0,
                "no_speech_threshold": 0.4,
            },
        )
    print(result)
