# GameOS - Oyun Konsolu Isletim Sistemi Simulasyonu

## Proje Hakkinda
GameOS, gercek bir oyun konsolunun isletim sisteminin temel bilesenlerini simule eden bir projedir. Python ve C dillerinin birlikte kullanildigi bu proje, isletim sistemi kavramlarini uygulamali olarak gosterir.

## Tema: Oyun Konsolu OS'i
Tum tasarim kararlari "bu bir oyun konsoludur" perspektifinden alinmistir:
- **Round Robin Scheduler**: Oyun, ses, ag ve UI process'leri adil CPU zamani alir
- **Sabit Sayfa Boyutu (4KB)**: Konsoldaki sinirli RAM (256MB) verimli yonetilir
- **Mutex/Semaphore**: Oyun state'i birden fazla thread'den guvenle korunur
- **Basit Dosya Sistemi**: Save dosyalari ve ROM'lar icin yeterli

## Bilesenler

| # | Bilesen | Dil | Dosyalar |
|---|---------|-----|----------|
| 1 | Process Yonetimi & Scheduler | C + Python | `core/scheduler.c`, `simulation/process_manager.py`, `simulation/scheduler.py` |
| 2 | Bellek Yonetimi (Paging) | C + Python | `core/memory.c`, `simulation/memory_manager.py` |
| 3 | Eszamanlilik & Senkronizasyon | Python | `simulation/concurrency.py` |
| 4 | Dosya Sistemi | Python | `simulation/file_system.py` |
| 5 | Muhendislik Zorluklari | Python | `challenges/priority_inversion.py` |
| 6 | Hata Senaryolari | Python | `challenges/failure_scenarios.py` |
| 7 | Log Sistemi | Python | `simulation/logger.py` |

## Is Bolumu (4 Kisi)

| Kisi | Sorumluluk |
|------|-----------|
| Kisi 1 | Process Yonetimi + Scheduler (C + Python) |
| Kisi 2 | Bellek Yonetimi (C + Python) |
| Kisi 3 | Concurrency + Muhendislik Zorluklari (Python) |
| Kisi 4 | Dosya Sistemi + Logger + Hata Senaryolari (Python) |

## Calistirma

### Python Simulasyonu
```bash
cd GameOS/simulation
python3 main.py
```

### C Derleme
```bash
cd GameOS/core
make
./scheduler_test
./memory_test
```

### Testler
```bash
cd GameOS/tests
python3 test_all.py
```

## Proje Yapisi
```
GameOS/
├── core/                    # C - Dusuk seviye bilesenler
│   ├── scheduler.c/h       # Round Robin & Priority Scheduler
│   ├── memory.c/h          # Paging & Adres Cevirisi
│   └── Makefile
├── simulation/              # Python - Simulasyon katmani
│   ├── main.py              # Ana menu ve giris noktasi
│   ├── process_manager.py   # PCB ve process yasam dongusu
│   ├── scheduler.py         # RR & Priority RR Scheduler
│   ├── memory_manager.py    # Sayfalama bellek yonetimi
│   ├── file_system.py       # Dosya CRUD islemleri
│   ├── concurrency.py       # Mutex, Semaphore, Thread
│   └── logger.py            # Merkezi log sistemi
├── challenges/
│   ├── priority_inversion.py  # Priority Inversion & Deadlock
│   └── failure_scenarios.py   # OOM, Disk Full, Process Crash
├── tests/
│   └── test_all.py          # Birim testleri
└── README.md
```

## Tasarim Kararlari

### Neden Round Robin?
Oyun konsollarinda birden fazla gorev (oyun render, ses isleme, ag iletisimi) esit zamanda calistirilmalidir. Round Robin bu adaleti saglar. Priority versiyonu ise oyun process'ine daha fazla oncelik verir.

### Neden 4KB Sayfa Boyutu?
Standart isletim sistemlerindeki sayfa boyutuyla uyumlu. Dis parcalanmayi (external fragmentation) onler. Konsolun sinirli bellegini verimli kullanir.

### Neden Mutex + Semaphore?
- Mutex: Tek seferde bir thread erisimi (oyun state korunmasi)
- Semaphore: Sinirli sayida eslemanli erisim (max 4 ag baglantisi)

### Neden Basit Dosya Sistemi?
Oyun konsollarinda karmasik dizin yapilari gerekmez. Save dosyalari, ROM'lar ve ayarlar duz bir yapida yeterince yonetilebilir.
