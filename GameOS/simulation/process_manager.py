"""
GameOS - Process Yonetimi (PCB & Process Yasam Dongusu)

Tasarim Karari: Her oyun konsolu gorevi (oyun, ses motoru, ag,
UI) ayri bir process olarak modellenir. PCB (Process Control Block)
her process'in tum bilgisini tutar.
"""

from enum import Enum
from logger import logger


class ProcessState(Enum):
    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    BLOCKED = "BLOCKED"
    TERMINATED = "TERMINATED"


class ProcessType(Enum):
    """Oyun konsoluna ozgu process tipleri"""
    GAME = "GAME"           # Ana oyun process'i
    AUDIO = "AUDIO"         # Ses motoru
    NETWORK = "NETWORK"     # Online baglanti
    UI = "UI"               # Kullanici arayuzu
    SAVE = "SAVE"           # Kayit islemi
    SYSTEM = "SYSTEM"       # Sistem process'i


class PCB:
    """Process Control Block - Process'in tum bilgisini tutar"""

    def __init__(self, pid, name, process_type, priority=1,
                 burst_time=10, memory_required=1024):
        self.pid = pid
        self.name = name
        self.process_type = process_type
        self.priority = priority          # 0=en yuksek, 3=en dusuk
        self.state = ProcessState.NEW
        self.burst_time = burst_time      # Toplam CPU suresi
        self.remaining_time = burst_time
        self.memory_required = memory_required  # KB
        self.memory_allocated = False
        self.wait_time = 0
        self.turnaround_time = 0
        self.arrival_time = 0

    def __repr__(self):
        return (f"PCB(pid={self.pid}, name='{self.name}', "
                f"type={self.process_type.value}, state={self.state.value}, "
                f"remaining={self.remaining_time})")


class ProcessManager:
    """Process olusturma, sonlandirma ve durum yonetimi"""

    def __init__(self):
        self.processes = {}  # pid -> PCB
        self.next_pid = 1
        self.terminated_processes = []
        logger.info("PROCESS_MGR", "Process Manager baslatildi")

    def create_process(self, name, process_type, priority=1,
                       burst_time=10, memory_required=1024):
        """Yeni process olustur"""
        pid = self.next_pid
        self.next_pid += 1

        pcb = PCB(pid, name, process_type, priority,
                  burst_time, memory_required)
        pcb.state = ProcessState.READY
        self.processes[pid] = pcb

        logger.info("PROCESS_MGR",
                    f"Process olusturuldu: PID={pid}, Ad={name}, "
                    f"Tip={process_type.value}, Oncelik={priority}, "
                    f"Burst={burst_time}, Bellek={memory_required}KB")
        return pcb

    def terminate_process(self, pid):
        """Process'i sonlandir"""
        if pid not in self.processes:
            logger.error("PROCESS_MGR", f"PID={pid} bulunamadi!")
            return False

        pcb = self.processes[pid]
        pcb.state = ProcessState.TERMINATED
        self.terminated_processes.append(pcb)
        del self.processes[pid]

        logger.info("PROCESS_MGR",
                    f"Process sonlandirildi: PID={pid}, Ad={pcb.name}")
        return True

    def block_process(self, pid):
        """Process'i BLOCKED durumuna al (I/O bekleme vs.)"""
        if pid in self.processes:
            self.processes[pid].state = ProcessState.BLOCKED
            logger.info("PROCESS_MGR",
                       f"PID={pid} BLOCKED durumuna alindi")

    def unblock_process(self, pid):
        """BLOCKED process'i READY yap"""
        if pid in self.processes:
            self.processes[pid].state = ProcessState.READY
            logger.info("PROCESS_MGR",
                       f"PID={pid} READY durumuna geri dondu")

    def get_ready_processes(self):
        """READY durumdaki process'leri dondur"""
        return [p for p in self.processes.values()
                if p.state == ProcessState.READY]

    def get_all_processes(self):
        """Tum aktif process'leri dondur"""
        return list(self.processes.values())

    def print_process_table(self):
        """Process tablosunu yazdir"""
        print(f"\n{'='*75}")
        print("GameOS Process Tablosu")
        print(f"{'='*75}")
        print(f"{'PID':<6} {'Ad':<20} {'Tip':<10} {'Durum':<12} "
              f"{'Oncelik':<8} {'Kalan':<8} {'Bellek':<10}")
        print(f"{'-'*75}")

        for pcb in self.processes.values():
            print(f"{pcb.pid:<6} {pcb.name:<20} {pcb.process_type.value:<10} "
                  f"{pcb.state.value:<12} {pcb.priority:<8} "
                  f"{pcb.remaining_time:<8} {pcb.memory_required:<10}")

        print(f"{'-'*75}")
        print(f"Aktif: {len(self.processes)} | "
              f"Sonlanan: {len(self.terminated_processes)}")
        print(f"{'='*75}")
