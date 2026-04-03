"""
GameOS - Muhendislik Zorluğu: Priority Inversion & Deadlock

Priority Inversion: Dusuk oncelikli thread bir kilidi tutarken
yuksek oncelikli thread'in beklemek zorunda kalmasi.
Cozum: Priority Inheritance Protocol

Deadlock: Iki thread birbirinin tuttugu kilidi beklemesi.
Cozum: Lock ordering (kilit siralama)
"""

import threading
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'simulation'))
from logger import logger
from concurrency import GameMutex, GameThread


class PriorityInversionDemo:
    """
    Priority Inversion ornegi ve cozumu.

    Senaryo (Oyun Konsolu):
    - Yuksek oncelikli: Oyun render thread'i (GPU erisimi gerekli)
    - Orta oncelikli: Ses thread'i (GPU gerektirmez)
    - Dusuk oncelikli: Arka plan indirme thread'i (GPU erisimi tutuyor)

    Problem: Indirme thread'i GPU kilidini tutuyor,
    render thread'i bekliyor, ses thread'i calisip render'i engelliyor.
    """

    def __init__(self):
        self.gpu_mutex = GameMutex("GPU_Access")
        self.execution_log = []

    def _log(self, message):
        self.execution_log.append(message)
        logger.info("PRIORITY_INV", message)

    def low_priority_task(self, use_inheritance=False):
        """Dusuk oncelikli: Arka plan indirme (GPU kullanir)"""
        self._log("DUSUK: GPU kilidi aliniyor...")
        self.gpu_mutex.acquire("LOW-Download")
        self._log("DUSUK: GPU kilidi alindi, indirme basliyor...")

        # Uzun islem - bu sirada yuksek oncelikli thread bekler
        for i in range(5):
            time.sleep(0.05)
            self._log(f"DUSUK: Indirme devam ediyor... %{(i+1)*20}")

        self.gpu_mutex.release("LOW-Download")
        self._log("DUSUK: GPU kilidi birakildi, indirme tamamlandi")

    def medium_priority_task(self):
        """Orta oncelikli: Ses isleme (GPU gerektirmez)"""
        self._log("ORTA: Ses isleme basliyor...")
        for i in range(3):
            time.sleep(0.04)
            self._log(f"ORTA: Ses buffer {i+1}/3 islendi")
        self._log("ORTA: Ses isleme tamamlandi")

    def high_priority_task(self):
        """Yuksek oncelikli: Oyun render (GPU gerekli)"""
        time.sleep(0.02)  # Kisa gecikme ile basla
        self._log("YUKSEK: GPU kilidi isteniyor (RENDER)...")
        self.gpu_mutex.acquire("HIGH-Render")
        self._log("YUKSEK: GPU kilidi alindi! Render basliyor...")
        time.sleep(0.03)
        self.gpu_mutex.release("HIGH-Render")
        self._log("YUKSEK: Render tamamlandi")

    def demonstrate_problem(self):
        """Priority Inversion problemini goster"""
        self.execution_log = []
        logger.info("PRIORITY_INV",
                    "=== PRIORITY INVERSION PROBLEMI GOSTERISI ===")
        logger.info("PRIORITY_INV",
                    "Yuksek oncelikli render, dusuk oncelikli indirmeyi bekliyor!")

        t_low = GameThread("LOW-Download", self.low_priority_task)
        t_med = GameThread("MED-Audio", self.medium_priority_task)
        t_high = GameThread("HIGH-Render", self.high_priority_task)

        t_low.start()
        time.sleep(0.01)
        t_med.start()
        t_high.start()

        t_low.join()
        t_med.join()
        t_high.join()

        logger.info("PRIORITY_INV", "=== PROBLEM GOSTERISI TAMAMLANDI ===")
        self._print_execution_log("Priority Inversion (Problem)")

    def _print_execution_log(self, title):
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        for i, entry in enumerate(self.execution_log):
            print(f"  {i+1:2d}. {entry}")
        print(f"{'='*60}")


class DeadlockDemo:
    """
    Deadlock ornegi ve cozumu.

    Senaryo:
    - Thread A: Once kilit_1 sonra kilit_2 ister
    - Thread B: Once kilit_2 sonra kilit_1 ister
    -> Deadlock!

    Cozum: Her iki thread de ayni sirala kilit alir (lock ordering)
    """

    def __init__(self):
        self.lock_save = GameMutex("SaveFile_Lock")
        self.lock_config = GameMutex("Config_Lock")
        self.execution_log = []
        self.deadlock_detected = False

    def _log(self, message):
        self.execution_log.append(message)
        logger.info("DEADLOCK", message)

    def thread_a_deadlock(self):
        """Thread A: save -> config (DEADLOCK RISKI)"""
        self._log("Thread-A: SaveFile kilidi aliniyor...")
        self.lock_save.acquire("Thread-A")
        self._log("Thread-A: SaveFile kilidi alindi")

        time.sleep(0.05)  # Baska thread'e sans ver

        self._log("Thread-A: Config kilidi isteniyor...")
        # Bu noktada Thread-B config kilidini tutuyorsa -> DEADLOCK
        acquired = self.lock_config._lock.acquire(timeout=2)
        if not acquired:
            self._log("Thread-A: DEADLOCK TESPIT EDILDI! Config kilidi alinamadi!")
            self.deadlock_detected = True
            self.lock_save.release("Thread-A")
            return

        self.lock_config.owner = "Thread-A"
        self._log("Thread-A: Her iki kilit alindi, islem yapiliyor...")
        time.sleep(0.02)
        self.lock_config.release("Thread-A")
        self.lock_save.release("Thread-A")
        self._log("Thread-A: Tamamlandi")

    def thread_b_deadlock(self):
        """Thread B: config -> save (DEADLOCK RISKI - ters sira!)"""
        self._log("Thread-B: Config kilidi aliniyor...")
        self.lock_config.acquire("Thread-B")
        self._log("Thread-B: Config kilidi alindi")

        time.sleep(0.05)

        self._log("Thread-B: SaveFile kilidi isteniyor...")
        acquired = self.lock_save._lock.acquire(timeout=2)
        if not acquired:
            self._log("Thread-B: DEADLOCK TESPIT EDILDI! SaveFile kilidi alinamadi!")
            self.deadlock_detected = True
            self.lock_config.release("Thread-B")
            return

        self.lock_save.owner = "Thread-B"
        self._log("Thread-B: Her iki kilit alindi, islem yapiliyor...")
        time.sleep(0.02)
        self.lock_save.release("Thread-B")
        self.lock_config.release("Thread-B")
        self._log("Thread-B: Tamamlandi")

    def thread_a_safe(self):
        """Thread A: GUVENLI - ayni sirayla kilit al"""
        self._log("Thread-A (SAFE): SaveFile kilidi aliniyor...")
        self.lock_save.acquire("Thread-A-Safe")
        self._log("Thread-A (SAFE): SaveFile kilidi alindi")

        self._log("Thread-A (SAFE): Config kilidi aliniyor...")
        self.lock_config.acquire("Thread-A-Safe")
        self._log("Thread-A (SAFE): Her iki kilit alindi, islem yapiliyor...")

        time.sleep(0.02)

        self.lock_config.release("Thread-A-Safe")
        self.lock_save.release("Thread-A-Safe")
        self._log("Thread-A (SAFE): Tamamlandi")

    def thread_b_safe(self):
        """Thread B: GUVENLI - AYNI sirayla kilit al (save -> config)"""
        self._log("Thread-B (SAFE): SaveFile kilidi aliniyor...")
        self.lock_save.acquire("Thread-B-Safe")
        self._log("Thread-B (SAFE): SaveFile kilidi alindi")

        self._log("Thread-B (SAFE): Config kilidi aliniyor...")
        self.lock_config.acquire("Thread-B-Safe")
        self._log("Thread-B (SAFE): Her iki kilit alindi, islem yapiliyor...")

        time.sleep(0.02)

        self.lock_config.release("Thread-B-Safe")
        self.lock_save.release("Thread-B-Safe")
        self._log("Thread-B (SAFE): Tamamlandi")

    def demonstrate_deadlock(self):
        """Deadlock problemini goster"""
        self.execution_log = []
        self.deadlock_detected = False
        logger.info("DEADLOCK", "=== DEADLOCK GOSTERISI BASLADI ===")

        t_a = GameThread("Thread-A", self.thread_a_deadlock)
        t_b = GameThread("Thread-B", self.thread_b_deadlock)

        t_a.start()
        t_b.start()
        t_a.join(timeout=5)
        t_b.join(timeout=5)

        if self.deadlock_detected:
            logger.warning("DEADLOCK", "Deadlock tespit edildi ve timeout ile cozuldu!")
        logger.info("DEADLOCK", "=== DEADLOCK GOSTERISI TAMAMLANDI ===")
        self._print_log("Deadlock Gosterisi")

    def demonstrate_safe(self):
        """Deadlock-free cozumu goster"""
        self.execution_log = []
        self.lock_save = GameMutex("SaveFile_Lock")
        self.lock_config = GameMutex("Config_Lock")
        logger.info("DEADLOCK", "=== GUVENLI (Lock Ordering) GOSTERISI ===")

        t_a = GameThread("Thread-A-Safe", self.thread_a_safe)
        t_b = GameThread("Thread-B-Safe", self.thread_b_safe)

        t_a.start()
        t_b.start()
        t_a.join()
        t_b.join()

        logger.info("DEADLOCK", "=== GUVENLI GOSTERIS TAMAMLANDI ===")
        self._print_log("Guvenli Lock Ordering Cozumu")

    def _print_log(self, title):
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        for i, entry in enumerate(self.execution_log):
            print(f"  {i+1:2d}. {entry}")
        print(f"{'='*60}")
