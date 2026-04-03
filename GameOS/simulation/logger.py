"""
GameOS - Log / Gozlemlenebilirlik Sistemi

Tasarim Karari: Merkezi log sistemi secildi cunku
tum bilesenler (scheduler, bellek, dosya sistemi, concurrency)
tek bir yerden izlenebilmeli. Oyun konsollarinda debug icin
log kaydi kritik oneme sahiptir.
"""

import time
import os
from datetime import datetime
from enum import Enum


class LogLevel(Enum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


class Logger:
    # ANSI renk kodlari
    COLORS = {
        LogLevel.DEBUG: "\033[36m",      # Cyan
        LogLevel.INFO: "\033[32m",       # Yesil
        LogLevel.WARNING: "\033[33m",    # Sari
        LogLevel.ERROR: "\033[31m",      # Kirmizi
        LogLevel.CRITICAL: "\033[35m",   # Mor
    }
    RESET = "\033[0m"

    def __init__(self, log_file="gameos.log", min_level=LogLevel.DEBUG):
        self.log_file = log_file
        self.min_level = min_level
        self.start_time = time.time()
        self.log_entries = []

        # Log dosyasini olustur/temizle
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        with open(self.log_file, 'w') as f:
            f.write(f"=== GameOS Log Baslangic: {datetime.now()} ===\n\n")

        self.info("LOGGER", "Log sistemi baslatildi")

    def _elapsed(self):
        """Baslangictan bu yana gecen sure (ms)"""
        return int((time.time() - self.start_time) * 1000)

    def log(self, level, component, message):
        """Ana log fonksiyonu"""
        if level.value < self.min_level.value:
            return

        elapsed = self._elapsed()
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        entry = {
            "time": timestamp,
            "elapsed_ms": elapsed,
            "level": level.name,
            "component": component,
            "message": message
        }
        self.log_entries.append(entry)

        # Konsol ciktisi (renkli)
        color = self.COLORS.get(level, "")
        console_line = (f"{color}[{timestamp}] [{elapsed:6d}ms] "
                       f"[{level.name:8s}] [{component:12s}] "
                       f"{message}{self.RESET}")
        print(console_line)

        # Dosyaya yaz
        file_line = (f"[{timestamp}] [{elapsed:6d}ms] "
                    f"[{level.name:8s}] [{component:12s}] {message}\n")
        with open(self.log_file, 'a') as f:
            f.write(file_line)

    def debug(self, component, message):
        self.log(LogLevel.DEBUG, component, message)

    def info(self, component, message):
        self.log(LogLevel.INFO, component, message)

    def warning(self, component, message):
        self.log(LogLevel.WARNING, component, message)

    def error(self, component, message):
        self.log(LogLevel.ERROR, component, message)

    def critical(self, component, message):
        self.log(LogLevel.CRITICAL, component, message)

    def get_stats(self):
        """Log istatistiklerini dondur"""
        stats = {}
        for entry in self.log_entries:
            level = entry["level"]
            stats[level] = stats.get(level, 0) + 1
        return stats

    def print_summary(self):
        """Log ozetini yazdir"""
        stats = self.get_stats()
        print(f"\n{'='*50}")
        print("GameOS Log Ozeti")
        print(f"{'='*50}")
        print(f"Toplam log sayisi: {len(self.log_entries)}")
        for level in LogLevel:
            count = stats.get(level.name, 0)
            print(f"  {level.name:10s}: {count}")
        print(f"Toplam sure: {self._elapsed()} ms")
        print(f"Log dosyasi: {self.log_file}")
        print(f"{'='*50}")


# Global logger instance
logger = Logger()
