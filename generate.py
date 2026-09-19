#!/usr/bin/env python3
"""Generate 3D/gradient stock images using ComfyUI (headless, CPU) via its API."""
import argparse
import json
import random
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

COMFY_DIR = Path(__file__).resolve().parent / "ComfyUI"
PORT = 8188
BASE_URL = f"http://127.0.0.1:{PORT}"
CHECKPOINT = "sd15.safetensors"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def logs_path():
    return Path(__file__).resolve().parent / "comfyui.log"


def log_tail(n: int = 50):
    try:
        with open(logs_path(), encoding="utf-8", errors="replace") as fh:
            return "".join(fh.readlines()[-n:])
    except OSError:
        return "(comfyui.log tidak terbaca)"


def wait_for_server(proc: subprocess.Popen, timeout: int = 900):
    start = time.time()
    while time.time() - start < timeout:
        if proc.poll() is not None:
            print("--- comfyui.log (tail) ---")
            print(log_tail())
            raise RuntimeError(f"ComfyUI exited early (code={proc.returncode})")
        try:
            with urllib.request.urlopen(f"{BASE_URL}/system_stats", timeout=5) as resp:
                if resp.status == 200:
                    return
        except Exception:
            pass
        time.sleep(2)
    raise TimeoutError(f"ComfyUI tidak merespon dalam {timeout}s. Cek {logs_path()}")


def build_workflow(seed, prompt, negative, width, height, prefix):
    return {
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CHECKPOINT}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["4", 1]}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": 30,
                "cfg": 7.0,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
            },
        },
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": prefix, "images": ["8", 0]}},
    }


def exec_prompt(workflow):
    req = urllib.request.Request(
        f"{BASE_URL}/prompt",
        data=json.dumps({"prompt": workflow}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    prompt_id = result["prompt_id"]
    for _ in range(900):
        try:
            with urllib.request.urlopen(f"{BASE_URL}/history/{prompt_id}", timeout=10) as resp:
                history = json.loads(resp.read().decode("utf-8"))
            if prompt_id in history:
                return history[prompt_id].get("outputs", {})
        except urllib.error.HTTPError:
            pass
        time.sleep(2)
    raise TimeoutError(f"Prompt {prompt_id} tidak selesai dalam waktu wajar.")


def save_outputs(outputs, tag):
    for _, out in outputs.items():
        for img in out.get("images", []):
            query = urllib.parse.urlencode(img)
            url = f"{BASE_URL}/view?{query}"
            dest = OUTPUT_DIR / f"{tag}.png"
            with urllib.request.urlopen(url, timeout=60) as resp, open(dest, "wb") as fh:
                fh.write(resp.read())
            print(f"  tersimpan: {dest.name}")


def main():
    global PORT, BASE_URL
    parser = argparse.ArgumentParser(description="Generate gambar 3D/gradient dengan ComfyUI (CPU).")
    parser.add_argument("--batch", type=int, default=4, help="Jumlah gambar per run (default 4)")
    parser.add_argument("--seed", type=int, default=None, help="Seed (default acak per gambar)")
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()

    PORT = args.port
    BASE_URL = f"http://127.0.0.1:{PORT}"

    if not (COMFY_DIR / "main.py").exists():
        raise SystemExit(
            f"ComfyUI tidak ditemukan di {COMFY_DIR}.\n"
            "Clone dulu: git clone https://github.com/comfyanonymous/ComfyUI.git"
        )

    with open(Path(__file__).resolve().parent / "prompts.json", encoding="utf-8") as fh:
        prompts = json.load(fh)

    OUTPUT_DIR.mkdir(exist_ok=True)
    log = open(logs_path(), "w", encoding="utf-8")
    print("Memulai ComfyUI (CPU) ...")
    proc = subprocess.Popen(
        [sys.executable, str(COMFY_DIR / "main.py"), "--cpu", "--listen", "127.0.0.1", "--port", str(PORT)],
        cwd=str(COMFY_DIR),
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    try:
        wait_for_server(proc)
        print("ComfyUI siap.")
        manifest = []
        for i in range(args.batch):
            item = prompts[i % len(prompts)]
            seed = args.seed if args.seed is not None else random.randint(0, 2**31 - 1)
            tag = f"{item['name']}_{seed}"
            print(f"[{i + 1}/{args.batch}] {tag}")
            wf = build_workflow(
                seed,
                item["positive"],
                item.get("negative", ""),
                int(item.get("width", 512)),
                int(item.get("height", 512)),
                "comfyui",
            )
            outputs = exec_prompt(wf)
            save_outputs(outputs, tag)
            manifest.append(
                {"file": f"{tag}.png", "seed": seed, **{k: item.get(k) for k in ("name", "positive", "negative", "width", "height")}}
            )
        with open(OUTPUT_DIR / "metadata.json", "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=2)
        print(f"Selesai. {args.batch} gambar disimpan di {OUTPUT_DIR}")
    finally:
        proc.terminate()
        proc.wait(timeout=30)
        log.close()


if __name__ == "__main__":
    main()