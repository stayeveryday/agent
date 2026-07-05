import importlib.util
import sys


def main() -> None:
    print("Python:", sys.version)

    packages = [
        "torch",
        "transformers",
        "datasets",
        "accelerate",
        "peft",
        "trl",
    ]

    for name in packages:
        spec = importlib.util.find_spec(name)
        print(f"{name}: {'OK' if spec else 'MISSING'}")

    try:
        import torch

        print("CUDA available:", torch.cuda.is_available())
        if torch.cuda.is_available():
            print("CUDA device:", torch.cuda.get_device_name(0))
            print("CUDA capability:", torch.cuda.get_device_capability(0))
    except Exception as exc:
        print("Torch check failed:", exc)


if __name__ == "__main__":
    main()
