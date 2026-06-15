
# How to start
uv run python server.py


# Installation

## LLM
sudo systemctl enable --now ollama
ollama pull mistral
ollama run mistral

- mkdir -p ~/piper_models
dowload the language voice files

## Download the .onnx model file
curl -L https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx -o ~/piper_models/en_US-lessac-medium.onnx

## Download the .json config file
curl -L https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.json -o ~/piper_models/en_US-lessac-medium.json