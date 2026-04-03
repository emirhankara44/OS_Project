"""
GameOS - Dosya Sistemi Simulasyonu

Tasarim Karari: Basit, duz dosya sistemi secildi.
Oyun konsollarinda dosya sistemi genellikle save dosyalari,
ROM'lar ve konfigürasyon icin kullanilir. Karmasik dizin
yapisi gerekmez, bu yuzden flat file system uygundur.
"""

import time
from logger import logger


class FileType:
    SAVE_DATA = "SAVE"       # Oyun kayit dosyasi
    ROM = "ROM"              # Oyun ROM'u
    CONFIG = "CONFIG"        # Sistem ayarlari
    LOG = "LOG"              # Log dosyasi
    TEXTURE = "TEXTURE"      # Oyun dokusu
    AUDIO = "AUDIO_FILE"     # Ses dosyasi


class File:
    """Dosya metadata ve icerigi"""

    def __init__(self, name, file_type, owner_pid=0):
        self.name = name
        self.file_type = file_type
        self.owner_pid = owner_pid
        self.content = ""
        self.size = 0                  # Byte
        self.created_at = time.time()
        self.modified_at = time.time()
        self.is_locked = False
        self.locked_by = -1

    def __repr__(self):
        return f"File('{self.name}', type={self.file_type}, size={self.size}B)"


class FileSystem:
    """Basit dosya sistemi - flat yapida"""

    MAX_FILES = 256
    MAX_FILE_SIZE = 1024 * 1024  # 1 MB max dosya boyutu
    MAX_STORAGE = 64 * 1024 * 1024  # 64 MB toplam depolama

    def __init__(self):
        self.files = {}          # name -> File
        self.total_used = 0      # Byte
        self.operation_log = []
        logger.info("FILESYSTEM",
                    f"Dosya sistemi baslatildi | Max: {self.MAX_FILES} dosya, "
                    f"{self.MAX_STORAGE // (1024*1024)}MB depolama")

    def create_file(self, name, file_type, owner_pid=0):
        """Yeni dosya olustur"""
        if name in self.files:
            logger.error("FILESYSTEM", f"'{name}' zaten mevcut!")
            return None

        if len(self.files) >= self.MAX_FILES:
            logger.error("FILESYSTEM", "Maksimum dosya sayisina ulasildi!")
            return None

        f = File(name, file_type, owner_pid)
        self.files[name] = f

        self._log_operation("CREATE", name, owner_pid)
        logger.info("FILESYSTEM",
                    f"Dosya olusturuldu: '{name}' (tip={file_type}, PID={owner_pid})")
        return f

    def write_file(self, name, content, pid=0):
        """Dosyaya yaz"""
        if name not in self.files:
            logger.error("FILESYSTEM", f"'{name}' bulunamadi!")
            return False

        f = self.files[name]

        # Kilit kontrolu
        if f.is_locked and f.locked_by != pid:
            logger.warning("FILESYSTEM",
                          f"'{name}' kilitli (PID={f.locked_by} tarafindan)! "
                          f"PID={pid} yazamaz.")
            return False

        new_size = len(content.encode('utf-8'))

        if new_size > self.MAX_FILE_SIZE:
            logger.error("FILESYSTEM",
                        f"Dosya boyutu limiti asildi! {new_size}B > {self.MAX_FILE_SIZE}B")
            return False

        # Toplam depolama kontrolu
        size_diff = new_size - f.size
        if self.total_used + size_diff > self.MAX_STORAGE:
            logger.error("FILESYSTEM", "Depolama alani doldu!")
            return False

        self.total_used += size_diff
        f.content = content
        f.size = new_size
        f.modified_at = time.time()

        self._log_operation("WRITE", name, pid, new_size)
        logger.info("FILESYSTEM",
                    f"'{name}' yazildi | {new_size}B | PID={pid}")
        return True

    def read_file(self, name, pid=0):
        """Dosyadan oku"""
        if name not in self.files:
            logger.error("FILESYSTEM", f"'{name}' bulunamadi!")
            return None

        f = self.files[name]
        self._log_operation("READ", name, pid, f.size)
        logger.debug("FILESYSTEM", f"'{name}' okundu | {f.size}B | PID={pid}")
        return f.content

    def delete_file(self, name, pid=0):
        """Dosyayi sil"""
        if name not in self.files:
            logger.error("FILESYSTEM", f"'{name}' bulunamadi!")
            return False

        f = self.files[name]

        if f.is_locked:
            logger.warning("FILESYSTEM",
                          f"'{name}' kilitli, silinemez!")
            return False

        self.total_used -= f.size
        del self.files[name]

        self._log_operation("DELETE", name, pid)
        logger.info("FILESYSTEM", f"'{name}' silindi | PID={pid}")
        return True

    def lock_file(self, name, pid):
        """Dosyayi kilitle (concurrency icin)"""
        if name not in self.files:
            return False

        f = self.files[name]
        if f.is_locked:
            logger.warning("FILESYSTEM",
                          f"'{name}' zaten kilitli (PID={f.locked_by})")
            return False

        f.is_locked = True
        f.locked_by = pid
        logger.debug("FILESYSTEM", f"'{name}' kilitlendi (PID={pid})")
        return True

    def unlock_file(self, name, pid):
        """Dosya kilidini ac"""
        if name not in self.files:
            return False

        f = self.files[name]
        if f.locked_by != pid:
            logger.warning("FILESYSTEM",
                          f"'{name}' kilidi PID={pid} tarafindan acilamaz "
                          f"(sahibi: PID={f.locked_by})")
            return False

        f.is_locked = False
        f.locked_by = -1
        logger.debug("FILESYSTEM", f"'{name}' kilidi acildi (PID={pid})")
        return True

    def _log_operation(self, operation, filename, pid=0, size=0):
        """Islem logla"""
        self.operation_log.append({
            "operation": operation,
            "file": filename,
            "pid": pid,
            "size": size,
            "time": time.time()
        })

    def list_files(self):
        """Tum dosyalari listele"""
        print(f"\n{'='*70}")
        print("GameOS Dosya Sistemi")
        print(f"{'='*70}")
        print(f"{'Ad':<25} {'Tip':<12} {'Boyut':<10} {'PID':<6} {'Kilitli':<8}")
        print(f"{'-'*70}")

        for f in self.files.values():
            lock_str = f"Evet({f.locked_by})" if f.is_locked else "Hayir"
            print(f"{f.name:<25} {f.file_type:<12} {f.size:<10} "
                  f"{f.owner_pid:<6} {lock_str:<8}")

        print(f"{'-'*70}")
        print(f"Toplam: {len(self.files)} dosya | "
              f"Kullanilan: {self.total_used / 1024:.1f} KB / "
              f"{self.MAX_STORAGE / (1024*1024)} MB")
        print(f"{'='*70}")
