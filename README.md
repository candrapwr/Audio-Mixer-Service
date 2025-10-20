# Audio Mixer Service

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Pengantar

Audio Mixer Service adalah studio audio kecil berbasis Python yang membantu kamu memadukan background music dan voice-over secara otomatis. Proyek ini menyajikan dua cara pakai:
- **CLI tool** untuk kreator solo yang nyaman bekerja dari terminal.
- **RESTful API + web UI modern** (FastAPI) untuk tim kreatif yang ingin proses mixing lebih terstruktur dan bisa menangani banyak request sekaligus.

### Bagaimana Alur Kerjanya?
1. **Input**: kamu mengunggah/sebutkan dua file—musik latar (MP3/WAV) dan voice-over (WAV/MP3).
2. **Analisis Voice**: sistem mendeteksi bagian voice yang benar-benar berbicara (nonsilent) lalu menghitung durasinya.
3. **Mixing Otomatis**:
   - Musik latar otomatis diulang (loop) bila durasinya lebih pendek dari proyek, lalu diberikan fade-in halus di awal dan fade-out menjelang akhir supaya transisi terasa profesional.
   - Voice diberi delay sesuai preferensi, dipompa volumenya agar tetap tajam, dan ditimpa di atas musik sehingga timing dialog tetap presisi.
   - Saat voice aktif, sistem menurunkan volume musik (dynamic ducking) dan akan memulihkan volume penuh ketika voice diam; semuanya dilakukan secara otomatis tanpa perlu editing manual.
   - Begitu voice selesai, audio akhir dipotong otomatis setelah jeda beberapa detik (default 10 detik) sehingga hasilnya rapih, tidak kepanjangan, dan siap publish.
4. **Output**: hasil mixing diekspor ke MP3 baru. Pada mode API, nama file dibuat unik (UUID) supaya aman dipakai paralel atau heavy load.
5. **Metadata**: API mengembalikan detail seperti durasi voice, jumlah segmen aktif, dan parameter mixing untuk mempermudah debugging atau logging.

Dengan workflow tersebut, Audio Mixer Service cocok untuk bikin podcast, video narasi, audiobook, hingga konten short-form tanpa harus membuka DAW.

### Fitur Utama:
- **Deteksi Durasi Voice**: Otomatis mendeteksi panjang durasi voice dalam detik.
- **Delay Voice**: Voice dimulai setelah delay yang bisa disesuaikan (default: 5 detik), sementara musik sudah mulai dari awal.
- **Dynamic Ducking**: Volume musik otomatis meredup (ducking) saat voice aktif (berbicara), dan kembali normal saat voice diam (silent). Ini membuat voice lebih dominan tanpa mengganggu alur musik.
- **Fade-In/Out**: Musik dimulai dengan volume pelan yang naik perlahan (fade-in) di awal, dan mengecil perlahan (fade-out) sebelum audio berakhir.
- **Trim Otomatis**: Audio hasil dipotong tepat 10 detik setelah voice selesai, untuk menghindari file terlalu panjang.
- **Boost Voice**: Opsi untuk menaikkan volume voice agar lebih jelas.
- **Loop Musik**: Jika musik lebih pendek dari durasi total, otomatis diulang.
- **Output MP3**: Hasil diekspor ke format MP3 berkualitas tinggi.
- **REST API**: Endpoint `/api/mix` menerima file upload dan mengembalikan link unduhan hasil MP3 dengan nama acak (UUID) agar aman dipakai paralel/banyak request.
- **Web UI modern**: Halaman `http://localhost:8000/` siap pakai, responsif, dan ramah pengguna untuk upload musik + voice.
- **Metadata Mix**: API mengembalikan informasi segmen voice yang terdeteksi untuk mempermudah debugging atau analytics.

Aplikasi ini ringan, cepat, dan mudah dikustomisasi melalui argumen CLI maupun parameter form pada API. Cocok untuk pengguna MacBook atau sistem Unix-like lainnya.

**Catatan**: Aplikasi ini memerlukan FFmpeg untuk menangani format MP3. Pastikan file input: Musik (MP3), Voice (WAV/MP3).

## Requirements

- **Python**: Versi 3.12 atau lebih tinggi (untuk kompatibilitas optimal; jika pakai 3.13, instal `audioop-lts` tambahan).
- **Library**: `pydub`, `fastapi`, `uvicorn`, `python-multipart`.
- **FFmpeg**: Untuk konversi dan pemrosesan MP3.
- **Sistem**: MacBook (macOS) dengan Terminal.

## Installation & Setup

Ikuti langkah-langkah berikut untuk setup di MacBook. Asumsi kamu punya Homebrew terinstal (jika belum, instal dulu dengan `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`).

### 1. Buat Folder Proyek
Buka Terminal dan jalankan:
```bash
mkdir audio_mixer
cd audio_mixer
```

### 2. Instal Python (Jika Belum)
Cek versi Python:
```bash
python3 --version
```
Jika <3.12, instal via Homebrew:
```bash
brew install python@3.12
```
Gunakan `python3.12` untuk perintah selanjutnya jika diperlukan.

### 3. Buat Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # Aktifkan venv (prompt akan berubah jadi (venv))
```

### 4. Instal Dependensi
```bash
pip install -r requirements.txt
```
Jika pakai Python 3.13 dan ada error `audioop`, instal fix:
```bash
pip install audioop-lts
```

### 5. Instal FFmpeg
```bash
brew install ffmpeg
```
Verifikasi:
```bash
ffmpeg -version
```

## Menjalankan sebagai REST API + Web UI

1. Aktifkan virtual environment (`source venv/bin/activate`).
2. Pastikan dependensi sudah terinstal.
3. Jalankan server:
   ```bash
   uvicorn server:app --reload
   ```
4. Buka `http://localhost:8000/` untuk web UI modern.
5. Endpoint API tersedia di:
   - `POST /api/mix` → upload musik (`music`) dan voice (`voice`) dalam multipart form.
   - `GET /download/{filename}` → unduh hasil mixing berdasarkan nama file UUID.
   - `GET /health` → health check.

### Contoh Request API (cURL)
```bash
curl -X POST http://localhost:8000/api/mix \
  -F "music=@bg.mp3" \
  -F "voice=@suara.wav" \
  -F "delay_seconds=5" \
  -F "voice_boost_db=4"
```
Response akan berupa JSON:
```json
{
  "message": "Mixing berhasil",
  "download_url": "/download/mix-<uuid>.mp3",
  "metadata": {
    "voice_duration_seconds": 31.5,
    "nonsilent_segments": [...],
    "total_duration_seconds": 46.5,
    "delay_seconds": 5,
    "duck_db": -10,
    "voice_boost_db": 3,
    "output_file": "mix-<uuid>.mp3"
  }
}
```

## Penggunaan CLI (opsional)

Jalankan aplikasi dari folder `audio_mixer` dengan venv aktif.

### Contoh Dasar
```bash
python audio_mixer.py --music music.mp3 --voice voice.wav --output hasil.mp3
```
- Ini akan:
  - Deteksi durasi voice.
  - Mulai musik (fade-in 2 detik).
  - Voice masuk setelah 5 detik.
  - Musik redup saat voice aktif.
  - Fade-out di akhir.
  - Potong 10 detik setelah voice selesai.
  - Simpan ke `hasil.mp3`.

### Argumen CLI Lengkap
Gunakan `--help` untuk lihat semua. Default ditandai:

| Argumen | Deskripsi | Default | Contoh |
|---------|-----------|---------|--------|
| `--music` (required) | Path ke file musik MP3 | - | `--music lagu.mp3` |
| `--voice` (required) | Path ke file voice (WAV/MP3) | - | `--voice suara.wav` |
| `--output` | Path output MP3 | `output.mp3` | `--output podcast.mp3` |
| `--delay` | Delay voice dalam detik | `5` | `--delay 10` |
| `--duck_db` | Pengurangan volume musik saat voice (dB, negatif = redup) | `-10` | `--duck_db -15` |
| `--silence_thresh` | Threshold deteksi silence (dB, lebih rendah = lebih sensitif) | `-30` | `--silence_thresh -25` |
| `--min_silence_ms` | Minimal durasi silence (ms) | `500` | `--min_silence_ms 300` |
| `--fade_in_ms` | Durasi fade-in musik (ms) | `2000` | `--fade_in_ms 3000` |
| `--fade_out_ms` | Durasi fade-out akhir (ms) | `2000` | `--fade_out_ms 5000` |
| `--post_voice_duration` | Durasi setelah voice (ms) | `10000` | `--post_voice_duration 15000` |
| `--voice_boost_db` | Boost volume voice (dB) | `3` | `--voice_boost_db 5` |

### Contoh Lanjutan
Untuk voice yang pelan dan musik keras:
```bash
python audio_mixer.py --music intro.mp3 --voice narasi.wav --output final.mp3 --silence_thresh -25 --duck_db -20 --voice_boost_db 6 --fade_in_ms 1000 --post_voice_duration 5000
```

## Output dan Debug
- **Logs**: Jalankan CLI dengan `--verbose` atau lihat log server FastAPI untuk detail mixing.
- **Metadata Mix**: Endpoint API mengembalikan daftar segmen voice aktif (`nonsilent_segments`) beserta durasi.
- **File Output**: MP3 siap diputar di QuickTime, VLC, atau editor audio.

## Troubleshooting

| Masalah | Penyebab | Solusi |
|---------|----------|--------|
| **Error `audioop` (Python 3.13)** | Modul deprecated | `pip install audioop-lts` |
| **FFmpeg not found** | Belum terinstal | `brew install ffmpeg` |
| **Voice tidak terdengar** | Deteksi silence gagal atau volume rendah | Turunkan `--silence_thresh` ke -20/-15; naikkan `--voice_boost_db` ke 5+; normalize voice di Audacity. |
| **Musik tidak redup** | Segmen nonsilent 0 | Cek debug print; adjust `--silence_thresh` dan `--min_silence_ms`. Rekam voice lebih jelas. |
| **File output pendek/panjang** | Durasi musik/voice salah | Cek durasi dengan `ffprobe file.mp3`; extend musik jika perlu. |
| **Format error** | File bukan MP3/WAV | Konversi: `ffmpeg -i input.m4a voice.wav` |
| **Loop musik tidak jalan** | Musik terlalu pendek | Gunakan file musik lebih panjang atau biarkan kode handle (sudah otomatis). |

- **Test File**: Gunakan `ffprobe voice.wav` untuk info durasi.
- **Error Lain**: Jalankan CLI dengan `--verbose` atau lihat log server FastAPI (jalankan `uvicorn server:app --reload`) lalu share output/log.

## Pengembangan Lanjutan
- Tambah endpoint untuk queue/worker background, misalnya Celery atau RQ.
- Tambah autentikasi atau limitasi user untuk API publik.
- Integrasi efek lanjutan seperti normalisasi, limiter, atau reverb (lihat `pydub.effects`).
- Kontribusi: Fork repo ini dan submit pull request.
- Dependensi: Lihat `requirements.txt` (buat manual: `pip freeze > requirements.txt`).

## Kontak

Untuk pertanyaan atau dukungan, hubungi: [candrapwr@datasiber.com](mailto:candrapwr@datasiber.com)

## Lisensi

Proyek ini dilisensikan di bawah [MIT License](https://opensource.org/licenses/MIT). Anda bebas menggunakan, memodifikasi, dan mendistribusikan kode ini untuk tujuan pribadi atau komersial, dengan syarat menyertakan pemberitahuan hak cipta asli.
