"""
GameOS - Hata Senaryolari

Bu modul, isletim sistemlerinde yasanan tipik hata
durumlarini simule eder ve gosterir:
1. Bellek dolmasi (Out of Memory)
2. Deadlock tespiti
3. Dosya sistemi dolmasi
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'simulation'))
from logger import logger
from memory_manager import MemoryManager
from file_system import FileSystem, FileType
from process_manager import ProcessManager, ProcessType


class FailureScenarios:
    """Hata senaryolarini gosteren sinif"""

    def __init__(self):
        self.memory_mgr = MemoryManager()
        self.file_sys = FileSystem()
        self.process_mgr = ProcessManager()

    def scenario_out_of_memory(self):
        """
        Senaryo 1: Bellek Dolmasi (OOM)
        Birden fazla oyun yuklemeye calisinca bellek tukenir.
        """
        logger.info("FAILURE", "=== SENARYO: BELLEK DOLMASI (OOM) ===")

        # Buyuk oyunlar yuklemeye calis
        games = [
            ("SuperMario_HD", 128 * 1024),    # 128 MB
            ("Zelda_4K", 100 * 1024),          # 100 MB
            ("Pokemon_Ultra", 80 * 1024),       # 80 MB - Bu basarisiz olmali!
        ]

        for name, size_kb in games:
            pid = self.process_mgr.create_process(
                name, ProcessType.GAME, priority=0,
                burst_time=20, memory_required=size_kb
            ).pid

            success = self.memory_mgr.allocate(pid, size_kb)
            if not success:
                logger.critical("FAILURE",
                              f"OOM! '{name}' icin {size_kb}KB tahsis edilemedi!")
                logger.info("FAILURE",
                           "Cozum: En eski oyunu bellekten cikar")
                # Recovery: Ilk oyunu kapat
                first_pid = 1
                self.memory_mgr.free(first_pid)
                logger.info("FAILURE", "Bellek serbest birakildi, tekrar dene")
                success = self.memory_mgr.allocate(pid, size_kb)
                if success:
                    logger.info("FAILURE", f"'{name}' basariyla yuklendi (recovery)")

        self.memory_mgr.print_status()
        logger.info("FAILURE", "=== OOM SENARYOSU TAMAMLANDI ===")

    def scenario_disk_full(self):
        """
        Senaryo 2: Dosya Sistemi Dolmasi
        Cok fazla save dosyasi olusturulunca alan tukenir.
        """
        logger.info("FAILURE", "=== SENARYO: DISK DOLMASI ===")

        # Cok buyuk bir save dosyasi yazmayi dene
        self.file_sys.create_file("mega_save.dat", FileType.SAVE_DATA, owner_pid=1)
        big_content = "X" * (2 * 1024 * 1024)  # 2 MB - limitten buyuk!
        success = self.file_sys.write_file("mega_save.dat", big_content, pid=1)

        if not success:
            logger.critical("FAILURE", "Dosya boyutu limiti asildi!")
            logger.info("FAILURE",
                       "Cozum: Dosyayi parcalara ayirarak yaz")

            # Recovery: Kucuk parcalar halinde yaz
            small_content = "X" * (512 * 1024)  # 512 KB
            success = self.file_sys.write_file("mega_save.dat", small_content, pid=1)
            if success:
                logger.info("FAILURE", "Kucuk boyutlu save basarili (recovery)")

        self.file_sys.list_files()
        logger.info("FAILURE", "=== DISK DOLMASI SENARYOSU TAMAMLANDI ===")

    def scenario_process_crash(self):
        """
        Senaryo 3: Process Cokmesi
        Bir oyun process'i cokunce kaynaklari temizle.
        """
        logger.info("FAILURE", "=== SENARYO: PROCESS COKMESI ===")

        # Oyun ve yardimci process'ler olustur
        game = self.process_mgr.create_process(
            "CrashGame", ProcessType.GAME, priority=0,
            burst_time=15, memory_required=50 * 1024)
        audio = self.process_mgr.create_process(
            "CrashGame_Audio", ProcessType.AUDIO, priority=1,
            burst_time=15, memory_required=10 * 1024)

        self.memory_mgr.allocate(game.pid, game.memory_required)
        self.memory_mgr.allocate(audio.pid, audio.memory_required)

        # Save dosyasi olustur
        self.file_sys.create_file("crash_save.dat", FileType.SAVE_DATA, game.pid)
        self.file_sys.write_file("crash_save.dat", "game_state=running", game.pid)

        self.process_mgr.print_process_table()
        self.memory_mgr.print_status()

        # COKME!
        logger.critical("FAILURE",
                       f"PID={game.pid} (CrashGame) COKTU!")

        # Temizlik (cleanup)
        logger.info("FAILURE", "Temizlik basladi...")
        self.memory_mgr.free(game.pid)
        self.memory_mgr.free(audio.pid)
        self.process_mgr.terminate_process(game.pid)
        self.process_mgr.terminate_process(audio.pid)
        self.file_sys.delete_file("crash_save.dat", game.pid)

        logger.info("FAILURE", "Kaynaklar temizlendi")
        self.memory_mgr.print_status()
        logger.info("FAILURE", "=== PROCESS COKMESI SENARYOSU TAMAMLANDI ===")

    def run_all(self):
        """Tum hata senaryolarini calistir"""
        logger.info("FAILURE", ">>> TUM HATA SENARYOLARI BASLIYOR <<<")
        print("\n" + "=" * 60)
        print("  GameOS - Hata Senaryolari")
        print("=" * 60)

        self.scenario_out_of_memory()
        print()
        self.scenario_disk_full()
        print()
        self.scenario_process_crash()

        logger.info("FAILURE", ">>> TUM HATA SENARYOLARI TAMAMLANDI <<<")
