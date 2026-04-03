"""
GameOS - Python <-> C Koprusu (ctypes)

Bu modul, C ile yazilmis scheduler ve memory manager'i
Python'dan cagirmayi saglar. ctypes kullanilarak
libgameos.so shared library'si yuklenir.

Tasarim Karari: Performans kritik islemler (scheduling, bellek
tahsisi) C'de, ust seviye mantik Python'da calisir.
Oyun konsollarinda bu "firmware + OS" katmanlarina benzer.
"""

import ctypes
import ctypes.util
import os
import sys

from logger import logger

# Shared library yolu
_LIB_DIR = os.path.join(os.path.dirname(__file__), '..', 'core')
_LIB_PATH = os.path.join(_LIB_DIR, 'libgameos.so')


# ===== C Struct Tanimlari (ctypes) =====

class C_PCB(ctypes.Structure):
    """C tarafindaki PCB struct'inin Python karsiligi"""
    _fields_ = [
        ("pid", ctypes.c_int),
        ("name", ctypes.c_char * 64),
        ("priority", ctypes.c_int),
        ("state", ctypes.c_int),          # 0=READY, 1=RUNNING, 2=BLOCKED, 3=TERMINATED
        ("remaining_time", ctypes.c_int),
        ("total_time", ctypes.c_int),
        ("wait_time", ctypes.c_int),
        ("turnaround_time", ctypes.c_int),
        ("memory_required", ctypes.c_int),
    ]


MAX_PROCESSES = 64


class C_ReadyQueue(ctypes.Structure):
    """C tarafindaki ReadyQueue struct'inin Python karsiligi"""
    _fields_ = [
        ("processes", C_PCB * MAX_PROCESSES),
        ("count", ctypes.c_int),
        ("front", ctypes.c_int),
        ("rear", ctypes.c_int),
        ("time_quantum", ctypes.c_int),
        ("current_time", ctypes.c_int),
    ]


class C_PageTableEntry(ctypes.Structure):
    """C tarafindaki PageTableEntry struct'inin Python karsiligi"""
    _fields_ = [
        ("frame_number", ctypes.c_int),
        ("valid", ctypes.c_int),
        ("dirty", ctypes.c_int),
        ("referenced", ctypes.c_int),
        ("owner_pid", ctypes.c_int),
    ]


class C_PhysicalMemory(ctypes.Structure):
    """C tarafindaki PhysicalMemory struct'inin Python karsiligi"""
    _fields_ = [
        ("frames", ctypes.POINTER(ctypes.c_int)),
        ("free_frame_count", ctypes.c_int),
        ("total_page_faults", ctypes.c_int),
        ("total_allocations", ctypes.c_int),
    ]


# ===== C Library Yukleme =====

class CSchedulerBridge:
    """C Scheduler'i Python'dan kullanan kopru sinifi"""

    def __init__(self):
        self.lib = None
        self._load_library()

    def _load_library(self):
        """libgameos.so yukle"""
        if not os.path.exists(_LIB_PATH):
            logger.warning("C_BRIDGE",
                          f"C library bulunamadi: {_LIB_PATH}")
            logger.info("C_BRIDGE", "Derleme yapiliyor: make -C core/")
            os.system(f"make -C {_LIB_DIR}")

        if not os.path.exists(_LIB_PATH):
            logger.error("C_BRIDGE", "C library derlenemedi!")
            return

        self.lib = ctypes.CDLL(_LIB_PATH)
        self._setup_functions()
        logger.info("C_BRIDGE", "C library basariyla yuklendi")

    def _setup_functions(self):
        """C fonksiyonlarinin imzalarini tanimla"""
        # init_scheduler
        self.lib.init_scheduler.argtypes = [
            ctypes.POINTER(C_ReadyQueue), ctypes.c_int
        ]
        self.lib.init_scheduler.restype = None

        # add_process
        self.lib.add_process.argtypes = [
            ctypes.POINTER(C_ReadyQueue), C_PCB
        ]
        self.lib.add_process.restype = ctypes.c_int

        # run_round_robin
        self.lib.run_round_robin.argtypes = [
            ctypes.POINTER(C_ReadyQueue)
        ]
        self.lib.run_round_robin.restype = None

        # run_priority_rr
        self.lib.run_priority_rr.argtypes = [
            ctypes.POINTER(C_ReadyQueue)
        ]
        self.lib.run_priority_rr.restype = None

        # print_schedule_stats
        self.lib.print_schedule_stats.argtypes = [
            ctypes.POINTER(C_ReadyQueue)
        ]
        self.lib.print_schedule_stats.restype = None

    def is_available(self):
        return self.lib is not None

    def create_queue(self, quantum=3):
        """Yeni ReadyQueue olustur ve baslatilmis dondur"""
        queue = C_ReadyQueue()
        self.lib.init_scheduler(ctypes.byref(queue), quantum)
        return queue

    def add_process(self, queue, pid, name, priority, burst_time, mem_req=0):
        """Queue'ya process ekle"""
        pcb = C_PCB()
        pcb.pid = pid
        pcb.name = name.encode('utf-8')[:63]
        pcb.priority = priority
        pcb.state = 0  # READY
        pcb.remaining_time = burst_time
        pcb.total_time = burst_time
        pcb.wait_time = 0
        pcb.turnaround_time = 0
        pcb.memory_required = mem_req
        return self.lib.add_process(ctypes.byref(queue), pcb)

    def run_round_robin(self, queue):
        """C Round Robin scheduler calistir"""
        self.lib.run_round_robin(ctypes.byref(queue))

    def run_priority_rr(self, queue):
        """C Priority RR scheduler calistir"""
        self.lib.run_priority_rr(ctypes.byref(queue))

    def get_results(self, queue):
        """Scheduling sonuclarini Python dict listesi olarak dondur"""
        results = []
        for i in range(queue.count):
            p = queue.processes[i]
            results.append({
                "pid": p.pid,
                "name": p.name.decode('utf-8'),
                "priority": p.priority,
                "burst_time": p.total_time,
                "wait_time": p.wait_time,
                "turnaround_time": p.turnaround_time,
            })
        return results


class CMemoryBridge:
    """C Memory Manager'i Python'dan kullanan kopru sinifi"""

    def __init__(self):
        self.lib = None
        self._load_library()

    def _load_library(self):
        if not os.path.exists(_LIB_PATH):
            logger.warning("C_BRIDGE", "C library bulunamadi, derleniyor...")
            os.system(f"make -C {_LIB_DIR}")

        if not os.path.exists(_LIB_PATH):
            logger.error("C_BRIDGE", "C library derlenemedi!")
            return

        self.lib = ctypes.CDLL(_LIB_PATH)
        self._setup_functions()
        logger.info("C_BRIDGE", "C Memory library yuklendi")

    def _setup_functions(self):
        # init_memory
        self.lib.init_memory.argtypes = [ctypes.POINTER(C_PhysicalMemory)]
        self.lib.init_memory.restype = None

        # allocate_pages
        self.lib.allocate_pages.argtypes = [
            ctypes.POINTER(C_PhysicalMemory), ctypes.c_int, ctypes.c_int,
            ctypes.POINTER(C_PageTableEntry)
        ]
        self.lib.allocate_pages.restype = ctypes.c_int

        # free_pages
        self.lib.free_pages.argtypes = [
            ctypes.POINTER(C_PhysicalMemory), ctypes.c_int,
            ctypes.POINTER(C_PageTableEntry), ctypes.c_int
        ]
        self.lib.free_pages.restype = None

        # translate_address
        self.lib.translate_address.argtypes = [
            ctypes.POINTER(C_PageTableEntry), ctypes.c_int,
            ctypes.c_int, ctypes.c_int
        ]
        self.lib.translate_address.restype = ctypes.c_int

        # print_memory_status
        self.lib.print_memory_status.argtypes = [
            ctypes.POINTER(C_PhysicalMemory)
        ]
        self.lib.print_memory_status.restype = None

        # free_memory_system
        self.lib.free_memory_system.argtypes = [
            ctypes.POINTER(C_PhysicalMemory)
        ]
        self.lib.free_memory_system.restype = None

        # get_free_frame_count
        self.lib.get_free_frame_count.argtypes = [
            ctypes.POINTER(C_PhysicalMemory)
        ]
        self.lib.get_free_frame_count.restype = ctypes.c_int

    def is_available(self):
        return self.lib is not None

    def create_memory(self):
        """Yeni PhysicalMemory olustur ve baslatilmis dondur"""
        mem = C_PhysicalMemory()
        self.lib.init_memory(ctypes.byref(mem))
        return mem

    def allocate(self, mem, pid, num_pages):
        """Sayfa tahsis et"""
        pt = (C_PageTableEntry * num_pages)()
        result = self.lib.allocate_pages(
            ctypes.byref(mem), pid, num_pages, pt)
        return result, pt

    def free(self, mem, pid, page_table, num_entries):
        """Sayfalari serbest birak"""
        self.lib.free_pages(ctypes.byref(mem), pid, page_table, num_entries)

    def translate(self, page_table, num_entries, logical_page, offset):
        """Adres cevirisi"""
        return self.lib.translate_address(page_table, num_entries,
                                          logical_page, offset)

    def print_status(self, mem):
        self.lib.print_memory_status(ctypes.byref(mem))

    def cleanup(self, mem):
        self.lib.free_memory_system(ctypes.byref(mem))

    def get_free_frames(self, mem):
        return self.lib.get_free_frame_count(ctypes.byref(mem))


# ===== Demo / Test =====

def demo_c_bridge():
    """C Bridge demo - Python'dan C fonksiyonlarini cagir"""
    print("\n" + "=" * 60)
    print("  Python <-> C Koprusu Demo")
    print("  (ctypes ile libgameos.so kullanimi)")
    print("=" * 60)

    # --- Scheduler Bridge ---
    print("\n--- C Scheduler Bridge ---")
    sched = CSchedulerBridge()

    if sched.is_available():
        queue = sched.create_queue(quantum=3)
        sched.add_process(queue, 1, "SuperMario",    0, 12, 65536)
        sched.add_process(queue, 2, "AudioEngine",   1,  6, 16384)
        sched.add_process(queue, 3, "OnlineService", 2,  8,  8192)
        sched.add_process(queue, 4, "GameUI",        1,  4, 32768)
        sched.add_process(queue, 5, "AutoSave",      3,  3,  4096)

        print("\n[Python -> C] Round Robin calistiriliyor...")
        sched.run_round_robin(queue)

        results = sched.get_results(queue)
        print("\n[Python] Sonuclar:")
        for r in results:
            print(f"  PID={r['pid']} {r['name']:<20} "
                  f"Wait={r['wait_time']:<5} TA={r['turnaround_time']}")
    else:
        print("C library yuklenemedi! 'cd core && make' calistirin.")

    # --- Memory Bridge ---
    print("\n--- C Memory Bridge ---")
    mem_bridge = CMemoryBridge()

    if mem_bridge.is_available():
        mem = mem_bridge.create_memory()

        print("\n[Python -> C] 16384 sayfa tahsis ediliyor (64MB)...")
        result, pt = mem_bridge.allocate(mem, 1, 16384)
        print(f"[Python] Sonuc: {result} sayfa tahsis edildi")

        print(f"[Python] Bos frame: {mem_bridge.get_free_frames(mem)}")

        addr = mem_bridge.translate(pt, 16384, 5, 100)
        print(f"[Python] Adres cevirisi: Sayfa 5, Offset 100 -> {addr}")

        mem_bridge.free(mem, 1, pt, 16384)
        mem_bridge.print_status(mem)
        mem_bridge.cleanup(mem)
    else:
        print("C library yuklenemedi!")


if __name__ == "__main__":
    demo_c_bridge()
