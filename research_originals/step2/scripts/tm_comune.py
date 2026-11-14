# Funzioni comuni agli script del Test M. Girano in tutti e tre gli ambienti (Python 3.11 e 3.12):
# usano solo la libreria standard, numpy e torch.
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

LABELS = ("YES", "NO", "UNKNOWN")


def encode(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False).encode("utf-8")


def fingerprint(obj):
    return hashlib.sha256(encode(obj)).hexdigest()


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(encode(obj))
    os.replace(tmp, path)


def read_json(path):
    return json.loads(Path(path).read_text())


def say(*args):
    print(time.strftime("%H:%M:%S"), *args, flush=True)


def parse_label(text):
    match = re.match(r"""^\s*[*#`"']*\s*(YES|NO|UNKNOWN)\b""", text, re.IGNORECASE)
    return match.group(1).upper() if match else "ALTRO"


def finite(x):
    return x is not None and x == x and x not in (float("inf"), float("-inf"))


def clean(x):
    # valori non finiti -> None, così il JSON resta valido e la coppia si esclude nell'analisi
    x = float(x)
    return x if finite(x) else None


def batches(rows, size):
    for start in range(0, len(rows), size):
        yield rows[start:start + size]


def checkpoint(folder, stage, rows, compute, size=64, key="row_id"):
    # Salva ogni blocco su Drive: una run interrotta riprende dai blocchi già scritti.
    # l'impronta copre il contenuto completo delle righe (prompt compresi), non solo gli identificativi
    sig = fingerprint(rows)[:16]
    folder = Path(folder) / "checkpoint" / f"{stage}-{sig}"
    folder.mkdir(parents=True, exist_ok=True)
    out = []
    for i, chunk in enumerate(batches(rows, size)):
        path = folder / f"{i:04d}.json"
        expected = [r[key] for r in chunk]
        if path.exists():
            part = read_json(path)
        else:
            part = list(compute(chunk, i))
            if [r[key] for r in part] != expected:
                raise RuntimeError(f"Risultati incompleti in {stage}, blocco {i}")
            write_json(path, part)
        if [r[key] for r in part] != expected:
            raise RuntimeError(f"Checkpoint incoerente in {stage}, blocco {i}")
        out.extend(part)
        if i == 0 or (i + 1) % 5 == 0 or len(out) == len(rows):
            say(f"  {stage} {len(out)}/{len(rows)}")
    return out


# ---------- codifica dei prompt e p(UNKNOWN), identiche al Test U2 ----------

def chat_text(tokenizer, model_key, prompt):
    options = {"enable_thinking": False} if model_key == "qwen" else {}
    return tokenizer.apply_chat_template([{"role": "user", "content": prompt}], tokenize=False,
                                         add_generation_prompt=True, **options)


def prompt_ids(tokenizer, model_key, prompt):
    return tokenizer(chat_text(tokenizer, model_key, prompt), add_special_tokens=False)["input_ids"]


def label_ids(tokenizer):
    audit = {}
    for label in LABELS:
        variants = [prefix + word for word in (label, label.capitalize(), label.lower()) for prefix in ("", " ")]
        audit[label] = {v: tokenizer.encode(v, add_special_tokens=False) for v in variants}
    ids = {label: sorted({sequence[0] for sequence in audit[label].values()}) for label in LABELS}
    if len(set().union(*map(set, ids.values()))) != sum(map(len, ids.values())):
        raise RuntimeError(f"Il tokenizer condivide i primi token fra etichette: {ids}")
    return ids


def stop_ids(tokenizer, model):
    ids = set()
    for value in (tokenizer.eos_token_id, getattr(model.generation_config, "eos_token_id", None)):
        if isinstance(value, int):
            ids.add(value)
        elif isinstance(value, (list, tuple)):
            ids.update(v for v in value if isinstance(v, int))
    return ids


def predict_reference(model, tokenizer, model_key, rows, ids, keep_answer_ids=False):
    # Come la cella 8 del Test U2: batch 1, greedy, 8 token, probabilità delle etichette sul primo token.
    import torch
    stops = stop_ids(tokenizer, model)
    for row in rows:
        enc = tokenizer(chat_text(tokenizer, model_key, row["prompt"]), return_tensors="pt",
                        add_special_tokens=False).to(model.device)
        with torch.inference_mode():
            result = model.generate(**enc, do_sample=False, max_new_tokens=8, use_cache=True,
                                    return_dict_in_generate=True, output_logits=True,
                                    pad_token_id=tokenizer.pad_token_id if tokenizer.pad_token_id is not None
                                    else tokenizer.eos_token_id)
        logits = result.logits[0].float()
        if not bool(torch.isfinite(logits).all()):
            raise RuntimeError("Logit non finiti al primo passo")
        p = logits.softmax(dim=-1)[0]
        probability = [float(p[ids[label]].sum()) for label in LABELS]
        new = result.sequences[0, enc["input_ids"].shape[1]:].tolist()
        text = tokenizer.decode(new, skip_special_tokens=True)
        out = dict(row_id=row["row_id"], generated=text, parsed=parse_label(text),
                   prompt_tokens=int(enc["input_ids"].shape[1]), mass_total=sum(probability),
                   **{f"p_{k}": v for k, v in zip(LABELS, probability)})
        if keep_answer_ids:
            answer = []
            for t in new:                       # la risposta senza il token di fine turno
                if t in stops:
                    break
                answer.append(t)
            out["prompt_ids"] = enc["input_ids"][0].tolist()
            out["answer_ids"] = answer
        yield out


def load_causal_lm(model_key, model_id, revision, token):
    # Come il Test U2: bf16, attention eager, tutto sulla GPU 0, padding a sinistra.
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer
    extra = {"fix_mistral_regex": True} if model_key == "mistral" else {}
    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision, token=token, trust_remote_code=False, **extra)
    tokenizer.padding_side = "left"
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    major, minor = (int(x) for x in transformers.__version__.split(".")[:2])
    dtype_arg = "dtype" if (major, minor) >= (4, 56) else "torch_dtype"
    model = AutoModelForCausalLM.from_pretrained(model_id, revision=revision, token=token, device_map={"": 0},
                                                 attn_implementation="eager", trust_remote_code=False,
                                                 low_cpu_mem_usage=True, **{dtype_arg: torch.bfloat16}).eval()
    return model, tokenizer


def alignment(results, reference):
    # reference: [(pair_key, kind, valore)] da P−S del Test U2
    by_key = {(r["pair_key"], r["kind"]): r for r in results}
    errors = [abs(by_key[(k, kind)]["p_UNKNOWN"] - v) for k, kind, v in reference if (k, kind) in by_key]
    return dict(n=len(errors), errore_assoluto_max=max(errors) if errors else None)


def manifest(**extra):
    import platform
    info = dict(python=platform.python_version(), eseguibile=sys.executable)
    from importlib import metadata
    for name in ("torch", "transformers", "numpy", "peft", "datasets", "lm-polygraph", "accelerate", "tokenizers"):
        try:
            info[name] = metadata.version(name)
        except Exception:
            info[name] = None
    try:
        import torch
        info["gpu"] = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    except Exception:
        pass
    info.update(extra)
    return info
