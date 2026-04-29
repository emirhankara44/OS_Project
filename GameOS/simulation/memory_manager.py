"""
GameOS - Bellek Yonetimi (Python tarafı)

Tasarim Karari: 256MB toplam bellek, 4KB sayfa boyutu.
Oyun konsollarinda bellek sinirlidir, bu yuzden verimli
tahsis ve serbest birakma kritiktir. Bu simulator demand paging
yerine tum process sayfalarini bastan tahsis eder; bellek yetmezse
kontrollu OOM hatasi uretir.
"""

from logger import logger


class Page:
    """Tek bir bellek sayfasini temsil eder"""

    def __init__(self, page_id, frame_number=-1):
        self.page_id = page_id
        self.frame_number = frame_number
        self.valid = False
        self.dirty = False
        self.referenced = False
        self.owner_pid = -1


class MemoryManager:
    """Sayfalama tabanli bellek yonetimi"""

    TOTAL_MEMORY_KB = 262144    # 256 MB
    PAGE_SIZE_KB = 4            # 4 KB
    TOTAL_FRAMES = TOTAL_MEMORY_KB // PAGE_SIZE_KB  # 65536

    def __init__(self):
        # Her frame: 0=bos, pid=dolu
        self.frames = [0] * self.TOTAL_FRAMES
        self.free_frame_count = self.TOTAL_FRAMES
        self.page_tables = {}  # pid -> [Page]
        self.allocation_log = []
        self.page_fault_count = 0

        logger.info("MEMORY",
                    f"Bellek baslatildi | {self.TOTAL_MEMORY_KB}KB "
                    f"({self.TOTAL_FRAMES} frame) | Sayfa: {self.PAGE_SIZE_KB}KB")

    def allocate(self, pid, size_kb):
        """
        Bir process icin bellek tahsis et.
        size_kb: Gereken bellek miktari (KB)
        """
        num_pages = (size_kb + self.PAGE_SIZE_KB - 1) // self.PAGE_SIZE_KB

        if num_pages > self.free_frame_count:
            logger.error("MEMORY",
                        f"YETERSIZ BELLEK! PID={pid} icin {num_pages} sayfa "
                        f"istendi, {self.free_frame_count} bos.")
            return False

        pages = []
        allocated = 0

        for i in range(self.TOTAL_FRAMES):
            if allocated >= num_pages:
                break
            if self.frames[i] == 0:
                self.frames[i] = pid
                page = Page(allocated, i)
                page.valid = True
                page.owner_pid = pid
                pages.append(page)
                allocated += 1

        self.free_frame_count -= allocated
        self.page_tables[pid] = pages

        self.allocation_log.append({
            "action": "ALLOCATE",
            "pid": pid,
            "pages": allocated,
            "kb": allocated * self.PAGE_SIZE_KB
        })

        logger.info("MEMORY",
                    f"PID={pid} icin {allocated} sayfa ({allocated * self.PAGE_SIZE_KB}KB) "
                    f"tahsis edildi | Bos: {self.free_frame_count} frame")
        return True

    def free(self, pid):
        """Bir process'in tum bellegini serbest birak"""
        if pid not in self.page_tables:
            logger.warning("MEMORY", f"PID={pid} icin sayfa tablosu bulunamadi")
            return 0

        freed = 0
        for page in self.page_tables[pid]:
            if page.valid:
                self.frames[page.frame_number] = 0
                page.valid = False
                freed += 1

        self.free_frame_count += freed
        del self.page_tables[pid]

        self.allocation_log.append({
            "action": "FREE",
            "pid": pid,
            "pages": freed,
            "kb": freed * self.PAGE_SIZE_KB
        })

        logger.info("MEMORY",
                    f"PID={pid} icin {freed} sayfa serbest birakildi | "
                    f"Bos: {self.free_frame_count} frame")
        return freed

    def translate_address(self, pid, logical_page, offset):
        """
        Mantiksal adresi fiziksel adrese cevir.
        logical_page: Sayfa numarasi
        offset: Sayfa ici offset (0 - PAGE_SIZE_KB-1)
        """
        if pid not in self.page_tables:
            logger.error("MEMORY", f"PID={pid} icin sayfa tablosu yok!")
            return -1

        pages = self.page_tables[pid]

        if logical_page < 0 or logical_page >= len(pages):
            logger.error("MEMORY",
                        f"Gecersiz sayfa numarasi: {logical_page} (PID={pid})")
            self.page_fault_count += 1
            return -1

        page = pages[logical_page]
        if not page.valid:
            logger.warning("MEMORY",
                          f"PAGE FAULT! PID={pid}, Sayfa={logical_page}")
            self.page_fault_count += 1
            return -1

        page.referenced = True
        physical_addr = page.frame_number * self.PAGE_SIZE_KB + offset

        logger.debug("MEMORY",
                    f"Adres cevirisi: PID={pid} | Sayfa {logical_page}, "
                    f"Offset {offset} -> Fiziksel {physical_addr}")
        return physical_addr

    def get_usage_percent(self):
        """Bellek kullanim yuzdesi"""
        used = self.TOTAL_FRAMES - self.free_frame_count
        return (used / self.TOTAL_FRAMES) * 100

    def print_status(self):
        """Bellek durumunu yazdir"""
        used = self.TOTAL_FRAMES - self.free_frame_count
        print(f"\n{'='*55}")
        print("GameOS Bellek Durumu")
        print(f"{'='*55}")
        print(f"Toplam:     {self.TOTAL_MEMORY_KB:>8} KB ({self.TOTAL_FRAMES} frame)")
        print(f"Kullanilan: {used * self.PAGE_SIZE_KB:>8} KB ({used} frame)")
        print(f"Bos:        {self.free_frame_count * self.PAGE_SIZE_KB:>8} KB "
              f"({self.free_frame_count} frame)")
        print(f"Doluluk:    {self.get_usage_percent():>7.1f}%")
        print(f"Page Fault: {self.page_fault_count}")
        print(f"{'='*55}")

        if self.page_tables:
            print(f"\n{'PID':<6} {'Sayfa Sayisi':<15} {'Bellek (KB)':<12}")
            print(f"{'-'*35}")
            for pid, pages in self.page_tables.items():
                valid_pages = sum(1 for p in pages if p.valid)
                print(f"{pid:<6} {valid_pages:<15} "
                      f"{valid_pages * self.PAGE_SIZE_KB:<12}")
