/*
 * GameOS - Oyun Konsolu Isletim Sistemi Simulasyonu
 * Bellek Yonetimi (Paging) - C implementasyonu
 *
 * Tasarim Karari: Sabit boyutlu sayfalama (4KB) secildi cunku
 * oyun konsollarinda bellek sinirlidir (256MB). Sabit sayfa boyutu
 * dis parcalanmayi (external fragmentation) onler ve bellek
 * tahsisini hizlandirir.
 */

#include "memory.h"

void init_memory(PhysicalMemory *mem) {
    mem->frames = (int *)calloc(TOTAL_PAGES, sizeof(int));
    if (!mem->frames) {
        printf("[MEMORY] KRITIK HATA: Bellek tahsis edilemedi!\n");
        return;
    }
    mem->free_frame_count = TOTAL_PAGES;
    mem->total_page_faults = 0;
    mem->total_allocations = 0;
    printf("[MEMORY] Baslatildi | Toplam: %d KB (%d sayfa) | Sayfa boyutu: %d KB\n",
           TOTAL_MEMORY_KB, TOTAL_PAGES, PAGE_SIZE_KB);
}

int allocate_pages(PhysicalMemory *mem, int pid, int num_pages,
                   PageTableEntry *page_table) {
    if (num_pages > mem->free_frame_count) {
        printf("[MEMORY] HATA: Yetersiz bellek! Istenen: %d sayfa, Bos: %d sayfa (PID=%d)\n",
               num_pages, mem->free_frame_count, pid);
        return -1;
    }

    int allocated = 0;
    for (int i = 0; i < TOTAL_PAGES && allocated < num_pages; i++) {
        if (mem->frames[i] == 0) {
            mem->frames[i] = pid;
            page_table[allocated].frame_number = i;
            page_table[allocated].valid = 1;
            page_table[allocated].dirty = 0;
            page_table[allocated].referenced = 0;
            page_table[allocated].owner_pid = pid;
            allocated++;
        }
    }

    mem->free_frame_count -= allocated;
    mem->total_allocations += allocated;

    printf("[MEMORY] PID=%d icin %d sayfa tahsis edildi | Bos kalan: %d sayfa (%d KB)\n",
           pid, allocated, mem->free_frame_count,
           mem->free_frame_count * PAGE_SIZE_KB);

    return allocated;
}

void free_pages(PhysicalMemory *mem, int pid,
                PageTableEntry *page_table, int num_entries) {
    int freed = 0;
    for (int i = 0; i < num_entries; i++) {
        if (page_table[i].valid && page_table[i].owner_pid == pid) {
            int frame = page_table[i].frame_number;
            mem->frames[frame] = 0;
            page_table[i].valid = 0;
            freed++;
        }
    }
    mem->free_frame_count += freed;
    printf("[MEMORY] PID=%d icin %d sayfa serbest birakildi | Bos: %d sayfa\n",
           pid, freed, mem->free_frame_count);
}

int translate_address(PageTableEntry *page_table, int num_entries,
                      int logical_page, int offset) {
    if (logical_page < 0 || logical_page >= num_entries) {
        printf("[MEMORY] HATA: Gecersiz mantiksal sayfa: %d\n", logical_page);
        return -1;
    }

    if (!page_table[logical_page].valid) {
        printf("[MEMORY] PAGE FAULT! Mantiksal sayfa %d bellekte degil.\n",
               logical_page);
        return -1;
    }

    page_table[logical_page].referenced = 1;
    int physical_address = page_table[logical_page].frame_number * PAGE_SIZE_KB + offset;

    printf("[MEMORY] Adres cevirisi: Sayfa %d, Offset %d -> Fiziksel: %d\n",
           logical_page, offset, physical_address);

    return physical_address;
}

void print_memory_status(PhysicalMemory *mem) {
    printf("\n--- Bellek Durumu ---\n");
    printf("Toplam Bellek:     %d KB (%d sayfa)\n", TOTAL_MEMORY_KB, TOTAL_PAGES);
    printf("Kullanilan:        %d KB (%d sayfa)\n",
           (TOTAL_PAGES - mem->free_frame_count) * PAGE_SIZE_KB,
           TOTAL_PAGES - mem->free_frame_count);
    printf("Bos:               %d KB (%d sayfa)\n",
           mem->free_frame_count * PAGE_SIZE_KB, mem->free_frame_count);
    printf("Toplam Tahsis:     %d\n", mem->total_allocations);
    printf("Doluluk Orani:     %.1f%%\n",
           (float)(TOTAL_PAGES - mem->free_frame_count) / TOTAL_PAGES * 100);
}

void free_memory_system(PhysicalMemory *mem) {
    if (mem->frames) {
        free(mem->frames);
        mem->frames = NULL;
    }
}

int get_free_frame_count(PhysicalMemory *mem) {
    return mem->free_frame_count;
}

/* ====== TEST MAIN ====== */
#ifdef MEMORY_TEST

int main(void) {
    printf("╔══════════════════════════════════════════════╗\n");
    printf("║   GameOS Memory Manager Test (C)            ║\n");
    printf("╚══════════════════════════════════════════════╝\n");

    PhysicalMemory mem;
    init_memory(&mem);

    /* --- TEST 1: Bellek Tahsisi --- */
    printf("\n>>> TEST 1: Bellek Tahsisi <<<\n");

    // SuperMario - 64 MB = 16384 sayfa
    int mario_pages = 16384;
    PageTableEntry *mario_pt = calloc(mario_pages, sizeof(PageTableEntry));
    printf("\nSuperMario icin %d sayfa (%d KB) tahsis ediliyor...\n",
           mario_pages, mario_pages * PAGE_SIZE_KB);
    int result = allocate_pages(&mem, 1, mario_pages, mario_pt);
    printf("Sonuc: %d sayfa tahsis edildi\n", result);

    // AudioEngine - 16 MB = 4096 sayfa
    int audio_pages = 4096;
    PageTableEntry *audio_pt = calloc(audio_pages, sizeof(PageTableEntry));
    printf("\nAudioEngine icin %d sayfa (%d KB) tahsis ediliyor...\n",
           audio_pages, audio_pages * PAGE_SIZE_KB);
    result = allocate_pages(&mem, 2, audio_pages, audio_pt);
    printf("Sonuc: %d sayfa tahsis edildi\n", result);

    // GameUI - 32 MB = 8192 sayfa
    int ui_pages = 8192;
    PageTableEntry *ui_pt = calloc(ui_pages, sizeof(PageTableEntry));
    printf("\nGameUI icin %d sayfa (%d KB) tahsis ediliyor...\n",
           ui_pages, ui_pages * PAGE_SIZE_KB);
    result = allocate_pages(&mem, 3, ui_pages, ui_pt);

    print_memory_status(&mem);

    /* --- TEST 2: Adres Cevirisi --- */
    printf("\n>>> TEST 2: Adres Cevirisi <<<\n");

    printf("\nMario - Sayfa 0, Offset 0:\n");
    int addr = translate_address(mario_pt, mario_pages, 0, 0);
    printf("  -> Fiziksel adres: %d\n", addr);

    printf("\nMario - Sayfa 5, Offset 2048:\n");
    addr = translate_address(mario_pt, mario_pages, 5, 2048);
    printf("  -> Fiziksel adres: %d\n", addr);

    printf("\nGecersiz sayfa (100000):\n");
    addr = translate_address(mario_pt, mario_pages, 100000, 0);
    printf("  -> Fiziksel adres: %d (hata bekleniyor)\n", addr);

    /* --- TEST 3: Bellek Serbest Birakma --- */
    printf("\n>>> TEST 3: Bellek Serbest Birakma <<<\n");
    printf("\nAudioEngine bellegi serbest birakiliyor...\n");
    free_pages(&mem, 2, audio_pt, audio_pages);
    print_memory_status(&mem);

    /* --- TEST 4: Yetersiz Bellek (OOM) --- */
    printf("\n>>> TEST 4: Yetersiz Bellek (OOM) Testi <<<\n");
    PageTableEntry oom_pt;
    int huge_pages = TOTAL_PAGES + 1;  // Toplam bellekten fazla
    printf("\n%d sayfa isteniyor (toplam bellekten fazla)...\n", huge_pages);
    result = allocate_pages(&mem, 99, huge_pages, &oom_pt);
    printf("Sonuc: %d (hata bekleniyor)\n", result);

    /* --- Temizlik --- */
    printf("\n>>> Temizlik <<<\n");
    free_pages(&mem, 1, mario_pt, mario_pages);
    free_pages(&mem, 3, ui_pt, ui_pages);
    print_memory_status(&mem);

    free(mario_pt);
    free(audio_pt);
    free(ui_pt);
    free_memory_system(&mem);
    printf("\nTum testler tamamlandi.\n");

    return 0;
}

#endif
