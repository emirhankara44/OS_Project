"""
GameOS - Eszamanlilik ve Senkronizasyon

Tasarim Karari: Mutex + Semaphore kullanildi cunku
oyun konsollarinda birden fazla thread ayni kaynaklara
(oyun state'i, ses buffer'i, ag soketi) erisir.
Senkronizasyon olmadan data race ve tutarsizlik olusur.
"""

import threading
import time
from logger import logger


class GameMutex:
    """
    Mutex (Mutual Exclusion) implementasyonu.
    Bir seferde sadece bir thread kaynaga erisebilir.
    Ornek: Oyun state'ine erisim
    """

    def __init__(self, name="unnamed"):
        self.name = name
        self._lock = threading.Lock()
        self.owner = None
        self.lock_count = 0
        logger.debug("CONCURRENCY", f"Mutex olusturuldu: '{name}'")

    def acquire(self, thread_name="unknown"):
        """Kilidi al"""
        logger.debug("CONCURRENCY",
                     f"'{self.name}' kilidi isteniyor ({thread_name})")

        self._lock.acquire()
        self.owner = thread_name
        self.lock_count += 1

        logger.info("CONCURRENCY",
                    f"'{self.name}' kilidi alindi ({thread_name}) "
                    f"[toplam: {self.lock_count}]")

    def release(self, thread_name="unknown"):
        """Kilidi birak"""
        self.owner = None
        self._lock.release()
        logger.info("CONCURRENCY",
                    f"'{self.name}' kilidi birakildi ({thread_name})")

    def is_locked(self):
        return self._lock.locked()


class GameSemaphore:
    """
    Semaphore implementasyonu.
    Birden fazla thread'in sinirli sayida kaynaga erismesini saglar.
    Ornek: Maksimum 4 oyuncu ayni anda ag baglantisi
    """

    def __init__(self, name="unnamed", max_count=1):
        self.name = name
        self.max_count = max_count
        self._semaphore = threading.Semaphore(max_count)
        self.current_count = max_count
        logger.debug("CONCURRENCY",
                     f"Semaphore olusturuldu: '{name}' (max={max_count})")

    def acquire(self, thread_name="unknown"):
        """Kaynak al"""
        logger.debug("CONCURRENCY",
                     f"'{self.name}' semaphore isteniyor ({thread_name})")

        self._semaphore.acquire()
        self.current_count -= 1

        logger.info("CONCURRENCY",
                    f"'{self.name}' semaphore alindi ({thread_name}) "
                    f"[kalan: {self.current_count}/{self.max_count}]")

    def release(self, thread_name="unknown"):
        """Kaynak birak"""
        self._semaphore.release()
        self.current_count += 1
        logger.info("CONCURRENCY",
                    f"'{self.name}' semaphore birakildi ({thread_name}) "
                    f"[kalan: {self.current_count}/{self.max_count}]")


class GameThread:
    """
    Oyun konsolu thread simulasyonu.
    Her thread belirli bir gorevi (render, ses, ag) temsil eder.
    """

    _thread_counter = 0

    def __init__(self, name, target_func, args=(), daemon=True):
        GameThread._thread_counter += 1
        self.thread_id = GameThread._thread_counter
        self.name = name
        self._thread = threading.Thread(
            target=self._wrapper,
            args=(target_func, args),
            name=name,
            daemon=daemon
        )
        self.is_running = False
        self.result = None
        logger.debug("CONCURRENCY",
                     f"Thread olusturuldu: {name} (TID={self.thread_id})")

    def _wrapper(self, func, args):
        """Thread calistirma wrapper'i - log ile"""
        self.is_running = True
        logger.info("CONCURRENCY",
                    f"Thread basladi: {self.name} (TID={self.thread_id})")
        try:
            self.result = func(*args)
        except Exception as e:
            logger.error("CONCURRENCY",
                        f"Thread hatasi: {self.name} - {e}")
        finally:
            self.is_running = False
            logger.info("CONCURRENCY",
                        f"Thread bitti: {self.name} (TID={self.thread_id})")

    def start(self):
        self._thread.start()

    def join(self, timeout=None):
        self._thread.join(timeout)


class ConcurrencyDemo:
    """
    Eszamanlilik orneklerini gosteren demo sinifi.
    Hem dogru senkronizasyonu hem de yarış durumunu gosterir.
    """

    def __init__(self):
        self.game_state = {"score": 0, "health": 100, "level": 1}
        self.state_mutex = GameMutex("game_state")
        self.network_sem = GameSemaphore("network_slots", max_count=4)

    def safe_update_score(self, thread_name, points, iterations=5):
        """Mutex ile guvenli skor guncelleme"""
        for i in range(iterations):
            self.state_mutex.acquire(thread_name)
            old_score = self.game_state["score"]
            time.sleep(0.01)  # Islem suresi simulasyonu
            self.game_state["score"] = old_score + points
            logger.debug("CONCURRENCY",
                        f"{thread_name}: Skor {old_score} -> "
                        f"{self.game_state['score']}")
            self.state_mutex.release(thread_name)

    def unsafe_update_score(self, thread_name, points, iterations=5):
        """MUTEX OLMADAN skor guncelleme - RACE CONDITION gosterisi"""
        for i in range(iterations):
            old_score = self.game_state["score"]
            time.sleep(0.01)  # Bu bekleme sirasinda baska thread degistirebilir!
            self.game_state["score"] = old_score + points
            logger.debug("CONCURRENCY",
                        f"{thread_name}: Skor {old_score} -> "
                        f"{self.game_state['score']}")

    def network_connection(self, player_name, duration=0.1):
        """Semaphore ile ag baglantisi simulasyonu"""
        self.network_sem.acquire(player_name)
        logger.info("CONCURRENCY",
                    f"{player_name} baglandi (ag simulasyonu)")
        time.sleep(duration)
        self.network_sem.release(player_name)

    def run_safe_demo(self):
        """Mutex ile guvenli eslzamanli erisim demo"""
        logger.info("CONCURRENCY", "=== GUVENLI (Mutex) DEMO BASLADI ===")
        self.game_state["score"] = 0

        threads = []
        for i in range(3):
            t = GameThread(
                f"Player_{i+1}",
                self.safe_update_score,
                args=(f"Player_{i+1}", 10, 5)
            )
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        expected = 3 * 5 * 10  # 3 thread * 5 iterasyon * 10 puan
        actual = self.game_state["score"]
        logger.info("CONCURRENCY",
                    f"GUVENLI SONUC: Beklenen={expected}, Gercek={actual} "
                    f"{'DOGRU' if expected == actual else 'HATALI!'}")
        return actual

    def run_unsafe_demo(self):
        """Race condition demo (mutex olmadan)"""
        logger.info("CONCURRENCY", "=== GUVENLI OLMAYAN (Race Condition) DEMO BASLADI ===")
        self.game_state["score"] = 0

        threads = []
        for i in range(3):
            t = GameThread(
                f"UnsafePlayer_{i+1}",
                self.unsafe_update_score,
                args=(f"UnsafePlayer_{i+1}", 10, 5)
            )
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        expected = 3 * 5 * 10
        actual = self.game_state["score"]
        logger.info("CONCURRENCY",
                    f"GUVENLI OLMAYAN SONUC: Beklenen={expected}, Gercek={actual} "
                    f"{'DOGRU (sans!)' if expected == actual else 'RACE CONDITION!'}")
        return actual

    def run_semaphore_demo(self):
        """Semaphore demo - max 4 eslzamanli ag baglantisi"""
        logger.info("CONCURRENCY", "=== SEMAPHORE DEMO BASLADI ===")
        logger.info("CONCURRENCY", "Max 4 eslzamanli ag baglantisi")

        threads = []
        for i in range(8):
            t = GameThread(
                f"NetPlayer_{i+1}",
                self.network_connection,
                args=(f"NetPlayer_{i+1}", 0.1)
            )
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        logger.info("CONCURRENCY", "=== SEMAPHORE DEMO TAMAMLANDI ===")
