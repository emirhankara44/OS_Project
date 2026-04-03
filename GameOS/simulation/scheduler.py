"""
GameOS - Python Scheduler (Round Robin + Priority)

Tasarim Karari: Python'da da scheduler yazildi cunku
C scheduler'i ctypes ile baglanirken bu dosya
bagimsiz olarak da kullanilabilir. Ayrica baseline (basit RR)
ve gelismis (Priority RR) karsilastirmasi burada yapilir.
"""

from collections import deque
from process_manager import ProcessState
from logger import logger


class RoundRobinScheduler:
    """Basit Round Robin Scheduler (Baseline)"""

    def __init__(self, time_quantum=3):
        self.time_quantum = time_quantum
        self.ready_queue = deque()
        self.current_time = 0
        self.completed = []
        self.timeline = []  # Gantt chart icin
        logger.info("SCHEDULER",
                    f"Round Robin Scheduler baslatildi | Quantum={time_quantum}")

    def add_process(self, pcb):
        """Process'i ready queue'ya ekle"""
        pcb.state = ProcessState.READY
        self.ready_queue.append(pcb)
        logger.debug("SCHEDULER",
                     f"PID={pcb.pid} ({pcb.name}) kuyruga eklendi")

    def run(self):
        """Round Robin scheduling calistir"""
        logger.info("SCHEDULER", "=== Round Robin Scheduling BASLADI ===")

        while self.ready_queue:
            pcb = self.ready_queue.popleft()
            pcb.state = ProcessState.RUNNING

            # Bu process'in calisacagi sure
            exec_time = min(pcb.remaining_time, self.time_quantum)

            logger.info("SCHEDULER",
                       f"[T={self.current_time:3d}] PID={pcb.pid} ({pcb.name}) "
                       f"calistiriliyor | {exec_time} birim | "
                       f"Kalan: {pcb.remaining_time} -> {pcb.remaining_time - exec_time}")

            # Timeline kaydi
            self.timeline.append({
                "pid": pcb.pid,
                "name": pcb.name,
                "start": self.current_time,
                "duration": exec_time
            })

            # Diger process'lerin bekleme suresini guncelle
            for other in self.ready_queue:
                other.wait_time += exec_time

            pcb.remaining_time -= exec_time
            self.current_time += exec_time

            if pcb.remaining_time <= 0:
                pcb.state = ProcessState.TERMINATED
                pcb.turnaround_time = self.current_time
                self.completed.append(pcb)
                logger.info("SCHEDULER",
                           f"[T={self.current_time:3d}] PID={pcb.pid} ({pcb.name}) "
                           f"TAMAMLANDI | TA={pcb.turnaround_time} | "
                           f"Wait={pcb.wait_time}")
            else:
                pcb.state = ProcessState.READY
                self.ready_queue.append(pcb)

        logger.info("SCHEDULER", "=== Round Robin Scheduling TAMAMLANDI ===")
        return self.completed

    def print_stats(self):
        """Istatistikleri yazdir"""
        if not self.completed:
            print("Henuz tamamlanan process yok.")
            return

        print(f"\n{'='*65}")
        print("Round Robin Scheduler Istatistikleri")
        print(f"{'='*65}")
        print(f"{'PID':<6} {'Ad':<20} {'Burst':<8} {'Bekleme':<10} {'Turnaround':<12}")
        print(f"{'-'*65}")

        total_wait = 0
        total_ta = 0

        for pcb in self.completed:
            print(f"{pcb.pid:<6} {pcb.name:<20} {pcb.burst_time:<8} "
                  f"{pcb.wait_time:<10} {pcb.turnaround_time:<12}")
            total_wait += pcb.wait_time
            total_ta += pcb.turnaround_time

        n = len(self.completed)
        print(f"{'-'*65}")
        print(f"Ortalama Bekleme:    {total_wait / n:.2f}")
        print(f"Ortalama Turnaround: {total_ta / n:.2f}")
        print(f"{'='*65}")

    def print_gantt_chart(self):
        """Basit Gantt chart goster"""
        print(f"\n--- Gantt Chart ---")
        for entry in self.timeline:
            bar = "#" * entry["duration"]
            print(f"T={entry['start']:3d} | PID={entry['pid']} "
                  f"({entry['name']:<15s}) |{bar}| +{entry['duration']}")


class PriorityRoundRobinScheduler(RoundRobinScheduler):
    """
    Gelismis Scheduler: Priority + Round Robin
    Ayni oncelikteki process'ler RR ile, farkli oncelikler
    priority sirasina gore calistirilir.

    Oyun konsolunda: GAME > AUDIO > UI > NETWORK > SAVE
    """

    def __init__(self, time_quantum=3):
        super().__init__(time_quantum)
        logger.info("SCHEDULER",
                    "Priority RR Scheduler baslatildi (gelismis)")

    def run(self):
        """Priority-based Round Robin scheduling"""
        logger.info("SCHEDULER", "=== Priority RR Scheduling BASLADI ===")

        all_processes = list(self.ready_queue)
        self.ready_queue.clear()

        while all_processes:
            # En yuksek oncelikli (en dusuk sayi) process'i bul
            min_priority = min(p.priority for p in all_processes)

            # Bu oncelikteki process'leri RR ile calistir
            current_batch = [p for p in all_processes if p.priority == min_priority]
            remaining = [p for p in all_processes if p.priority != min_priority]

            batch_queue = deque(current_batch)

            while batch_queue:
                pcb = batch_queue.popleft()
                pcb.state = ProcessState.RUNNING

                exec_time = min(pcb.remaining_time, self.time_quantum)

                logger.info("SCHEDULER",
                           f"[T={self.current_time:3d}] PID={pcb.pid} ({pcb.name}) "
                           f"[P{pcb.priority}] | {exec_time} birim")

                self.timeline.append({
                    "pid": pcb.pid,
                    "name": pcb.name,
                    "start": self.current_time,
                    "duration": exec_time
                })

                # Tum bekleyenlerin wait_time guncelle
                for other in batch_queue:
                    other.wait_time += exec_time
                for other in remaining:
                    other.wait_time += exec_time

                pcb.remaining_time -= exec_time
                self.current_time += exec_time

                if pcb.remaining_time <= 0:
                    pcb.state = ProcessState.TERMINATED
                    pcb.turnaround_time = self.current_time
                    self.completed.append(pcb)
                    logger.info("SCHEDULER",
                               f"[T={self.current_time:3d}] PID={pcb.pid} TAMAMLANDI")
                else:
                    pcb.state = ProcessState.READY
                    batch_queue.append(pcb)

            all_processes = remaining

        logger.info("SCHEDULER", "=== Priority RR Scheduling TAMAMLANDI ===")
        return self.completed
