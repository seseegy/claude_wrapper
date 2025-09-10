# Claude Code OpenAI Wrapper

🤖 **Wrapper API siap produksi yang kompatibel dengan OpenAI untuk Claude Code CLI dengan sistem dual mode**

Proyek ini menyediakan wrapper berbasis FastAPI yang membuat Claude Code CLI kompatibel dengan format API OpenAI, memungkinkan integrasi yang mulus dengan aplikasi berbasis OpenAI yang sudah ada sambil memanfaatkan kemampuan canggih Claude.

## ✨ Fitur

### 🔄 **Sistem Dual Mode**
- **Claude Code Mode**: Informasi terbaru 2025, bantuan coding, peristiwa terkini
- **Claude Regular Mode**: Analisis gambar, pemrosesan file, percakapan umum
- **Smart Auto-Switching**: Otomatis memilih model terbaik berdasarkan konteks

### 🚀 **Kemampuan Utama**
- **Kompatibel dengan OpenAI API**: Pengganti langsung untuk endpoint API OpenAI
- **Dukungan Streaming**: Streaming respons real-time
- **Dukungan Multi Model**: Claude Sonnet 4, Claude 3.5 Sonnet, Haiku, Opus
- **Sistem Autentikasi**: Perlindungan API key dengan kontrol akses yang dapat dikonfigurasi
- **Health Monitoring**: Health check dan metrics bawaan
- **Dukungan Docker**: Siap untuk deployment containerized

### 📎 **Fitur Lanjutan**
- **Analisis Gambar**: Memproses dan menganalisis gambar menggunakan kemampuan vision Claude
- **Pemrosesan File**: Dukungan untuk PDF, file teks, dan dokumen
- **Manajemen Sesi**: Preservasi konteks percakapan
- **Error Handling**: Penanganan error yang robust dengan logging detail
- **Rate Limiting**: Perlindungan bawaan terhadap penyalahgunaan

## 🏗️ Arsitektur

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Aplikasi      │────│  FastAPI Wrapper │────│   Claude CLI    │
│   Client        │    │   (Proyek Ini)   │    │   (Official)    │
│  (OpenAI SDK)   │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Mapping Model
| Model OpenAI | Model Claude | Kasus Penggunaan |
|--------------|--------------|------------------|
| `gpt-4o` | Claude 3.5 Sonnet | Tugas umum, analisis gambar |
| `claude-4-sonnet` | Claude Sonnet 4 | Info terbaru, coding |
| `gpt-4` | Claude 3 Sonnet | Tugas standar |
| `gpt-3.5-turbo` | Claude 3 Haiku | Respon cepat |

## 🚀 Memulai Cepat

### Prasyarat
- Python 3.8+
- Claude Code CLI terinstal dan ter-autentikasi
- Node.js 16+ (untuk bot WhatsApp)

### Instalasi

1. **Clone repository:**
```bash
git clone https://github.com/seseegy/claude_wrapper
cd claude-ai
```

2. **Install dependensi Python:**
```bash
pip install -r requirements.txt
```

3. **Install dan autentikasi Claude Code CLI:**
```bash
npm install -g @anthropic-ai/claude-code
claude auth login
```

4. **Jalankan server API:**
```bash
python main.py
```

API akan tersedia di `http://localhost:8000` dengan dokumentasi di `http://localhost:8000/docs`

## 📖 Penggunaan API

### Chat Completion Dasar
```python
import openai

client = openai.OpenAI(
    api_key="your-api-key",  # Diatur di VALID_API_KEYS env var
    base_url="http://localhost:8000/v1"
)

response = client.chat.completions.create(
    model="claude-4-sonnet",  # Info terbaru + coding
    messages=[
        {"role": "user", "content": "Siapa presiden Indonesia saat ini?"}
    ]
)

print(response.choices[0].message.content)
# Output: "Prabowo Subianto (2024-2029) dengan Wapres Gibran Rakabuming Raka"
```

### Analisis Gambar
```python
response = client.chat.completions.create(
    model="gpt-4o",  # Otomatis menggunakan Claude Regular untuk gambar
    messages=[
        {
            "role": "user", 
            "content": "Tolong analisis gambar ini dan jelaskan apa yang Anda lihat."
        }
    ]
)
```

### Streaming Response
```python
stream = client.chat.completions.create(
    model="claude-4-sonnet",
    messages=[{"role": "user", "content": "Jelaskan quantum computing"}],
    stream=True
)

for chunk in stream:
    print(chunk.choices[0].delta.content, end="")
```

## 🤖 Integrasi Bot WhatsApp

Proyek ini termasuk bot WhatsApp berfitur lengkap dengan integrasi Claude:

### Fitur
- **Dual Mode AI**: Switching otomatis antar model Claude
- **Pemrosesan Media**: Analisis gambar, pembacaan PDF, pemrosesan dokumen
- **Kontrol Akses**: Manajemen pengguna dan permissions
- **Manajemen Sesi**: Konteks percakapan per pengguna
- **Perintah Admin**: Manajemen pengguna, status bot, dll.

### Setup Bot WhatsApp
```bash
cd whatsapp-bot
npm install
node bot.js
```

## ⚙️ Konfigurasi

### Environment Variables
```bash
# Konfigurasi Server
PORT=8000
HOST=0.0.0.0
LOG_LEVEL=INFO

# Autentikasi (API keys dipisah koma)
VALID_API_KEYS="sk-key1,sk-key2,sk-key3"

# Konfigurasi Claude CLI
CLAUDE_CLI_TIMEOUT=60
CLAUDE_MODEL_DEFAULT=claude-3-sonnet-20240229

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Monitoring
ENABLE_METRICS=true
ENABLE_LOGGING=true
```

## 🐳 Docker Deployment

### Menggunakan Docker Compose
```bash
docker-compose up -d
```

### Manual Docker Build
```bash
docker build -t claude-ai-wrapper .
docker run -p 8000:8000 -e VALID_API_KEYS="your-keys" claude-ai-wrapper
```

## 📊 Monitoring & Health Checks

### Health Endpoint
```bash
curl http://localhost:8000/health
```

### Model yang Tersedia
```bash
curl http://localhost:8000/v1/models
```

## 🔧 Development

### Struktur Proyek
```
claude-ai/
├── main.py                    # Entry point aplikasi FastAPI
├── corrected_claude_client.py # Integrasi Claude CLI
├── requirements.txt           # Dependensi Python
├── docker-compose.yml         # Konfigurasi Docker
├── test.py                   # Test API
└── README.md                 # File ini
```

### Testing
```bash
# Test endpoint API
python test.py

# Test dengan info terkini
python test_dual.py

# Test analisis gambar
python test_image.py
```

## 🛡️ Keamanan

### Autentikasi
- Autentikasi berbasis API key
- Kontrol akses yang dapat dikonfigurasi
- Perlindungan rate limiting

### Best Practices
- Jangan commit API keys ke version control
- Gunakan environment variables untuk data sensitif
- Rotate credentials secara berkala

## 🐛 Troubleshooting

### Masalah Umum

1. **Claude CLI Tidak Ter-autentikasi**
```bash
claude auth login
```

2. **Port Sudah Digunakan**
```bash
pkill -f "python main.py"
PORT=8001 python main.py
```

3. **Masalah Timeout Model**
```bash
export CLAUDE_CLI_TIMEOUT=120
```

## 📄 Referensi API

### Endpoint yang Didukung

| Endpoint | Method | Deskripsi |
|----------|--------|-----------|
| `/v1/chat/completions` | POST | Chat completions (streaming/non-streaming) |
| `/v1/models` | GET | Daftar model yang tersedia |
| `/health` | GET | Health check |
| `/docs` | GET | Dokumentasi API interaktif |

## 🤝 Kontribusi

1. Fork repository ini
2. Buat branch fitur: `git checkout -b nama-fitur`
3. Buat perubahan dan test menyeluruh
4. Commit dengan pesan yang jelas: `git commit -m "Tambah fitur X"`
5. Push ke fork Anda: `git push origin nama-fitur`
6. Buat Pull Request

## 📝 Lisensi

Proyek ini dilisensikan di bawah MIT License.

## 🙏 Acknowledgments

- [Anthropic](https://anthropic.com) untuk Claude AI
- [FastAPI](https://fastapi.tiangolo.com) untuk web framework yang excellent
- [OpenAI](https://openai.com) untuk standar API

---

**Dibuat dengan ❤️ untuk komunitas AI Indonesia**

*Ubah Claude Code CLI Anda menjadi layanan API siap produksi dengan kemampuan dual-mode canggih!*