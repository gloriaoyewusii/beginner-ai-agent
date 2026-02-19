import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# Pick a model you have access to.
# Example Mistral instruct (may require HF login + acceptance):
# MODEL_ID = "mistralai/Mistral-7B-Instruct-v0.2"

MODEL_ID = os.getenv("MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.3")

_tokenizer = None
_model = None


def load_model():
    global _tokenizer, _model

    if _tokenizer is not None and _model is not None:
        return _tokenizer, _model

    _tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

    # Device + dtype
    use_cuda = torch.cuda.is_available()
    dtype = torch.float16 if use_cuda else torch.float32

    _model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=dtype,
        device_map="auto" if use_cuda else None,  # GPU: auto place layers
    )

    return _tokenizer, _model


def generate_text(prompt: str, max_new_tokens: int = 600) -> str:
    tokenizer, model = load_model()

    inputs = tokenizer(prompt, return_tensors="pt")
    if torch.cuda.is_available():
        inputs = {k: v.to("cuda") for k, v in inputs.items()}

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
        )

    return tokenizer.decode(output_ids[0], skip_special_tokens=True)
