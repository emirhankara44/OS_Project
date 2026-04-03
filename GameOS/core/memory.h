#ifndef MEMORY_H
#define MEMORY_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define TOTAL_MEMORY_KB 262144   // 256 MB = 262144 KB
#define PAGE_SIZE_KB 4           // 4 KB sayfa boyutu
#define TOTAL_PAGES (TOTAL_MEMORY_KB / PAGE_SIZE_KB)  // 65536 sayfa
#define MAX_PAGE_TABLE_ENTRIES 16384

typedef struct {
    int frame_number;
    int valid;              // 1 = bellekte, 0 = degil
    int dirty;              // 1 = degistirildi
    int referenced;         // LRU icin
    int owner_pid;
} PageTableEntry;

typedef struct {
    int *frames;             // Dinamik: malloc ile TOTAL_PAGES boyutunda
    int free_frame_count;
    int total_page_faults;
    int total_allocations;
} PhysicalMemory;

// Bellek yonetimi fonksiyonlari
void init_memory(PhysicalMemory *mem);
int allocate_pages(PhysicalMemory *mem, int pid, int num_pages,
                   PageTableEntry *page_table);
void free_pages(PhysicalMemory *mem, int pid,
                PageTableEntry *page_table, int num_entries);
int translate_address(PageTableEntry *page_table, int num_entries,
                      int logical_page, int offset);
void print_memory_status(PhysicalMemory *mem);
void free_memory_system(PhysicalMemory *mem);
int get_free_frame_count(PhysicalMemory *mem);

#endif
