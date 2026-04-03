#!/usr/bin/env python3
"""
GameOS - Oyun Konsolu Isletim Sistemi Simulasyonu
Ana giris noktasi

Bu program, bir oyun konsolunun isletim sistemini simule eder.
4 ana bilesen: Process Yonetimi, Bellek Yonetimi, Eszamanlilik, Dosya Sistemi
"""

import sys
import os
import time

# Path ayarla
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'challenges'))

from logger import logger, Logger
from process_manager import ProcessManager, ProcessType
from memory_manager import MemoryManager
from scheduler import RoundRobinScheduler, PriorityRoundRobinScheduler
from file_system import FileSystem, FileType
from concurrency import ConcurrencyDemo
from priority_inversion import PriorityInversionDemo, DeadlockDemo
from failure_scenarios import FailureScenarios
from c_bridge import CSchedulerBridge, CMemoryBridge


def print_banner():
    banner = """
    ╔══════════════════════════════════════════════════════╗
    ║                                                      ║
    ║              🎮  G A M E O S  v1.0  🎮              ║
    ║         Oyun Konsolu Isletim Sistemi Simulasyonu     ║
    ║                                                      ║
    ║  Bilesenler:                                         ║
    ║    [1] Process Yonetimi & Scheduler                  ║
    ║    [2] Bellek Yonetimi (Paging)                      ║
    ║    [3] Eszamanlilik & Senkronizasyon                 ║
    ║    [4] Dosya Sistemi                                 ║
    ║    [5] Muhendislik Zorluklari                        ║
    ║    [6] Hata Senaryolari                              ║
    ║    [7] Tam Simulasyon (Tum Bilesenler)               ║
    ║    [8] C Bridge Demo (Python <-> C)                  ║
    ║    [0] Cikis                                         ║
    ║                                                      ║
    ╚══════════════════════════════════════════════════════╝
    """
    print(banner)


def demo_process_and_scheduler():
    """Bilesen 1: Process Yonetimi ve Scheduler demo"""
    logger.info("MAIN", "=== PROCESS YONETIMI & SCHEDULER DEMO ===")

    pm = ProcessManager()

    # Oyun konsolu process'leri olustur
    game = pm.create_process("SuperMario", ProcessType.GAME,
                             priority=0, burst_time=12, memory_required=65536)
    audio = pm.create_process("AudioEngine", ProcessType.AUDIO,
                              priority=1, burst_time=6, memory_required=16384)
    network = pm.create_process("OnlineService", ProcessType.NETWORK,
                                priority=2, burst_time=8, memory_required=8192)
    ui = pm.create_process("GameUI", ProcessType.UI,
                           priority=1, burst_time=4, memory_required=32768)
    save = pm.create_process("AutoSave", ProcessType.SAVE,
                             priority=3, burst_time=3, memory_required=4096)

    pm.print_process_table()

    # --- Baseline: Basit Round Robin ---
    print("\n" + "=" * 60)
    print("  BASELINE: Basit Round Robin (Quantum=3)")
    print("=" * 60)

    rr = RoundRobinScheduler(time_quantum=3)
    # Process'lerin kopyalarini olustur (RR icin)
    for p in [game, audio, network, ui, save]:
        from process_manager import PCB, ProcessState
        pcb_copy = PCB(p.pid, p.name, p.process_type, p.priority,
                       p.burst_time, p.memory_required)
        rr.add_process(pcb_copy)

    rr.run()
    rr.print_stats()
    rr.print_gantt_chart()

    # --- Gelismis: Priority Round Robin ---
    print("\n" + "=" * 60)
    print("  GELISMIS: Priority Round Robin (Quantum=3)")
    print("=" * 60)

    prr = PriorityRoundRobinScheduler(time_quantum=3)
    for p in [game, audio, network, ui, save]:
        pcb_copy = PCB(p.pid, p.name, p.process_type, p.priority,
                       p.burst_time, p.memory_required)
        prr.add_process(pcb_copy)

    prr.run()
    prr.print_stats()
    prr.print_gantt_chart()


def demo_memory():
    """Bilesen 2: Bellek Yonetimi demo"""
    logger.info("MAIN", "=== BELLEK YONETIMI DEMO ===")

    mm = MemoryManager()

    # Oyun konsolu bellek tahsisleri
    allocations = [
        (1, "SuperMario", 65536),      # 64 MB
        (2, "AudioEngine", 16384),      # 16 MB
        (3, "OnlineService", 8192),     # 8 MB
        (4, "GameUI", 32768),           # 32 MB
    ]

    for pid, name, size_kb in allocations:
        logger.info("MAIN", f"'{name}' icin {size_kb}KB tahsis ediliyor...")
        mm.allocate(pid, size_kb)

    mm.print_status()

    # Adres cevirisi ornekleri
    print("\n--- Adres Cevirisi Ornekleri ---")
    mm.translate_address(1, 0, 0)       # Ilk sayfa, offset 0
    mm.translate_address(1, 5, 100)     # 5. sayfa, offset 100
    mm.translate_address(2, 0, 2048)    # Audio, ilk sayfa
    mm.translate_address(99, 0, 0)      # Olmayan process -> HATA

    # Bellek serbest birakma
    logger.info("MAIN", "OnlineService bellegi serbest birakiliyor...")
    mm.free(3)
    mm.print_status()


def demo_concurrency():
    """Bilesen 3: Eszamanlilik ve Senkronizasyon demo"""
    logger.info("MAIN", "=== ESZAMANLILIK DEMO ===")

    demo = ConcurrencyDemo()

    # 1. Guvenli (mutex) demo
    safe_result = demo.run_safe_demo()
    print(f"\nGuvenli skor sonucu: {safe_result}")

    # 2. Guvenli olmayan (race condition) demo
    unsafe_result = demo.run_unsafe_demo()
    print(f"Guvenli olmayan skor sonucu: {unsafe_result}")

    # 3. Semaphore demo
    demo.run_semaphore_demo()


def demo_filesystem():
    """Bilesen 4: Dosya Sistemi demo"""
    logger.info("MAIN", "=== DOSYA SISTEMI DEMO ===")

    fs = FileSystem()

    # Dosya islemleri
    fs.create_file("mario_save_1.sav", FileType.SAVE_DATA, owner_pid=1)
    fs.create_file("zelda_rom.bin", FileType.ROM, owner_pid=0)
    fs.create_file("system.cfg", FileType.CONFIG, owner_pid=0)
    fs.create_file("bgm_overworld.ogg", FileType.AUDIO, owner_pid=2)

    # Yazma
    fs.write_file("mario_save_1.sav",
                  '{"level": 5, "score": 12500, "lives": 3, "coins": 47}',
                  pid=1)
    fs.write_file("system.cfg",
                  'resolution=1080p\nvolume=80\nlanguage=tr\ncontroller=wireless',
                  pid=0)

    # Okuma
    content = fs.read_file("mario_save_1.sav", pid=1)
    print(f"\nSave dosyasi icerigi: {content}")

    # Kilit mekanizmasi
    fs.lock_file("mario_save_1.sav", pid=1)
    fs.write_file("mario_save_1.sav", "hack!", pid=99)  # Basarisiz olmali
    fs.unlock_file("mario_save_1.sav", pid=1)

    # Silme
    fs.delete_file("bgm_overworld.ogg", pid=2)

    fs.list_files()


def demo_challenges():
    """Bilesen 5: Muhendislik Zorluklari"""
    logger.info("MAIN", "=== MUHENDISLIK ZORLUKLARI ===")

    # Priority Inversion
    pi_demo = PriorityInversionDemo()
    pi_demo.demonstrate_problem()

    print()

    # Deadlock
    dl_demo = DeadlockDemo()
    dl_demo.demonstrate_deadlock()
    print()
    dl_demo.demonstrate_safe()


def demo_failures():
    """Bilesen 6: Hata Senaryolari"""
    scenarios = FailureScenarios()
    scenarios.run_all()


def full_simulation():
    """Bilesen 7: Tam Simulasyon - Tum bilesenler birlikte"""
    logger.info("MAIN", ">>> GAMEOS TAM SIMULASYON BASLADI <<<")
    print("\n" + "=" * 60)
    print("  GAMEOS TAM SIMULASYON")
    print("  Tum bilesenler birlikte calisiyor")
    print("=" * 60)

    # 1. Sistem baslatma
    pm = ProcessManager()
    mm = MemoryManager()
    fs = FileSystem()

    # 2. Sistem dosyalari olustur
    fs.create_file("system.cfg", FileType.CONFIG)
    fs.write_file("system.cfg", "boot=ok\nmode=game")

    # 3. Oyun process'leri olustur ve bellek tahsis et
    game = pm.create_process("SuperMario", ProcessType.GAME,
                             priority=0, burst_time=12,
                             memory_required=65536)
    audio = pm.create_process("AudioEngine", ProcessType.AUDIO,
                              priority=1, burst_time=6,
                              memory_required=16384)
    net = pm.create_process("NetService", ProcessType.NETWORK,
                            priority=2, burst_time=8,
                            memory_required=8192)

    for proc in [game, audio, net]:
        mm.allocate(proc.pid, proc.memory_required)

    # 4. Save dosyasi olustur
    fs.create_file("mario_save.sav", FileType.SAVE_DATA, game.pid)
    fs.write_file("mario_save.sav",
                  '{"level": 1, "score": 0}', game.pid)

    # 5. Scheduler calistir
    print("\n--- Scheduler ---")
    from process_manager import PCB
    scheduler = PriorityRoundRobinScheduler(time_quantum=3)
    for p in pm.get_all_processes():
        pcb_copy = PCB(p.pid, p.name, p.process_type,
                       p.priority, p.burst_time, p.memory_required)
        scheduler.add_process(pcb_copy)
    scheduler.run()
    scheduler.print_stats()

    # 6. Concurrency demo
    print("\n--- Concurrency ---")
    conc = ConcurrencyDemo()
    conc.run_safe_demo()

    # 7. Save guncelle
    fs.write_file("mario_save.sav",
                  '{"level": 5, "score": 12500}', game.pid)

    # 8. Sonuc
    print("\n--- Sistem Durumu ---")
    pm.print_process_table()
    mm.print_status()
    fs.list_files()

    # 9. Temizlik
    for proc in pm.get_all_processes():
        mm.free(proc.pid)

    logger.info("MAIN", ">>> GAMEOS TAM SIMULASYON TAMAMLANDI <<<")
    logger.print_summary()


def demo_c_bridge():
    """Bilesen 8: Python <-> C Koprusu Demo"""
    from c_bridge import demo_c_bridge as _demo
    _demo()


def main():
    print_banner()

    while True:
        choice = input("\nSecim yapiniz (0-8): ").strip()

        if choice == "0":
            print("GameOS kapatiliyor... Hosca kalin!")
            break
        elif choice == "1":
            demo_process_and_scheduler()
        elif choice == "2":
            demo_memory()
        elif choice == "3":
            demo_concurrency()
        elif choice == "4":
            demo_filesystem()
        elif choice == "5":
            demo_challenges()
        elif choice == "6":
            demo_failures()
        elif choice == "7":
            full_simulation()
        elif choice == "8":
            demo_c_bridge()
        else:
            print("Gecersiz secim! 0-8 arasi bir sayi giriniz.")

        input("\nDevam etmek icin Enter'a basin...")


if __name__ == "__main__":
    main()
