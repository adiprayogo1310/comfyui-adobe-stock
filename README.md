# ComfyUI Adobe Stock Generator

Menghasilkan gambar konten **3D / gradient** secara otomatis memakai **ComfyUI** yang berjalan di **GitHub Actions** (CPU runner gratis), lalu meng-upscale hasilnya agar siap diunggah ke **Adobe Stock**.

## Cara pakai

1. Buka tab **Actions** di repo ini.
2. Pilih workflow **Generate Images** & tap **Run workflow**.
3. (Opsional) ubah **batch count** dan/atau **model URL**.
4. Tunggu sampai selesai (sekitar 10–20 menit per beberapa gambar karena pakai CPU).
5. Unduh artifact **generated-images** (kanan bawah run).
6. Kirim file dari folder `stock_ready/` ke **contributor.stock.adobe.com**.

## Menyesuaikan prompt

Edit `prompts.json` lalu jalankan workflow lagi. Tiap entri punya:

- `name` – label nama file output (awalan).
- `positive` – prompt utama.
- `negative` – hal yang harus dihindari.
- `width` / `height` – resolusi generate (default 512, aman untuk CPU). Resolusi akhir setelah upscale menyesuaikan proporsinya.

## Struktur

```
.github/workflows/generate.yml   # workflow GitHub Actions
generate.py                      # menjalankan ComfyUI headless dan generate via API
prompts.json                     # daftar prompt
output/                          # gambar mentah (hasil run workflow)
stock_ready/                     # gambar upscale 2048x2048 (>=4MP)
```

## Syarat Adobe Stock (wajib dibaca)

- Konten hasil AI **harus diberi label "dibuat/dibantu AI"** saat submit.
- Anda wajib punya hak menjual gambar; pakai model dengan lisensi komersial.
- Jangan memuat orang/karakter terkenal, merek/logo, atau meniru gaya artis hidup.
- Foto/ilustrasi minimal **4 megapixel** — hasil upscale `stock_ready/` sudah memenuhi ini.
- Cek panduan terkini: https://helpx.adobe.com/stock/contributor/submit-your-content/submit-generative-ai-content/generative-ai-content-guidelines.html

## Catatan teknis

- Runner GitHub standar **tanpa GPU**, jadi ComfyUI berjalan di **CPU** (`--cpu`).
- Model default: Stable Diffusion 1.5 (resmi dari Hugging Face, ~4 GB, lisensi CreativeML Open RAIL-M — boleh dipakai komersial).
- Butuh disk ~8–10 GB di runner; jika gagal karena space, gunakan model lebih kecil dengan mengganti `model_url`.