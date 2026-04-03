/*
 * GameOS - Oyun Konsolu Isletim Sistemi Simulasyonu
 * Round Robin Scheduler (C implementasyonu)
 *
 * Tasarim Karari: Round Robin secildi cunku oyun konsollarinda
 * birden fazla gorev (oyun, ses, ag, UI) esit CPU zamani almali.
 * Sabit time quantum ile her process adil sekilde calisir.
 */

#include "scheduler.h"

void init_scheduler(ReadyQueue *queue, int quantum) {
    queue->count = 0;
    queue->front = 0;
    queue->rear = -1;
    queue->time_quantum = (quantum > 0) ? quantum : DEFAULT_QUANTUM;
    queue->current_time = 0;
    printf("[SCHEDULER] Baslatildi | Quantum: %d | Max Process: %d\n",
           queue->time_quantum, MAX_PROCESSES);
}

int add_process(ReadyQueue *queue, PCB process) {
    if (queue->count >= MAX_PROCESSES) {
        printf("[SCHEDULER] HATA: Kuyruk dolu! PID %d eklenemedi.\n", process.pid);
        return -1;
    }
    queue->rear = (queue->rear + 1) % MAX_PROCESSES;
    process.state = READY;
    process.wait_time = 0;
    process.turnaround_time = 0;
    queue->processes[queue->rear] = process;
    queue->count++;
    printf("[SCHEDULER] Process eklendi: PID=%d, Ad=%s, Burst=%d, Oncelik=%d\n",
           process.pid, process.name, process.total_time, process.priority);
    return 0;
}

PCB* get_next_process(ReadyQueue *queue) {
    if (queue->count == 0) return NULL;

    // READY durumundaki ilk process'i bul
    for (int i = 0; i < queue->count; i++) {
        int idx = (queue->front + i) % MAX_PROCESSES;
        if (queue->processes[idx].state == READY) {
            return &queue->processes[idx];
        }
    }
    return NULL;
}

void run_round_robin(ReadyQueue *queue) {
    printf("\n========== ROUND ROBIN SCHEDULING BASLADI ==========\n");
    printf("Time Quantum: %d birim\n\n", queue->time_quantum);

    int completed = 0;
    int total = queue->count;
    queue->current_time = 0;

    while (completed < total) {
        int found = 0;

        for (int i = 0; i < total; i++) {
            PCB *p = &queue->processes[i];

            if (p->state == TERMINATED) continue;

            found = 1;
            p->state = RUNNING;

            int exec_time = (p->remaining_time < queue->time_quantum)
                            ? p->remaining_time
                            : queue->time_quantum;

            printf("[T=%3d] PID=%d (%s) calistiriliyor | %d birim | Kalan: %d -> %d\n",
                   queue->current_time, p->pid, p->name,
                   exec_time, p->remaining_time, p->remaining_time - exec_time);

            p->remaining_time -= exec_time;
            queue->current_time += exec_time;

            // Diger READY process'lerin bekleme suresini guncelle
            for (int j = 0; j < total; j++) {
                if (j != i && queue->processes[j].state != TERMINATED) {
                    queue->processes[j].wait_time += exec_time;
                }
            }

            if (p->remaining_time <= 0) {
                p->state = TERMINATED;
                p->turnaround_time = queue->current_time;
                completed++;
                printf("[T=%3d] PID=%d (%s) TAMAMLANDI | Turnaround: %d | Bekleme: %d\n",
                       queue->current_time, p->pid, p->name,
                       p->turnaround_time, p->wait_time);
            } else {
                p->state = READY;
            }
        }

        if (!found) break;
    }

    printf("\n========== SCHEDULING TAMAMLANDI ==========\n");
    print_schedule_stats(queue);
}

void run_priority_rr(ReadyQueue *queue) {
    /*
     * Gelismis Scheduler: Priority + Round Robin
     * Oncelik sirasiyla calistirir, ayni onceliktekiler RR ile
     * Bu, oyun konsolunda oyun process'ine ses/ag'dan daha fazla
     * oncelik vermemizi saglar.
     */
    printf("\n========== PRIORITY ROUND ROBIN SCHEDULING BASLADI ==========\n");
    printf("Time Quantum: %d birim\n\n", queue->time_quantum);

    int completed = 0;
    int total = queue->count;
    queue->current_time = 0;

    while (completed < total) {
        // En yuksek oncelikli (en dusuk sayi) READY process'i bul
        int best_priority = 999;
        for (int i = 0; i < total; i++) {
            if (queue->processes[i].state != TERMINATED &&
                queue->processes[i].priority < best_priority) {
                best_priority = queue->processes[i].priority;
            }
        }

        if (best_priority == 999) break;

        int ran_any = 0;
        for (int i = 0; i < total; i++) {
            PCB *p = &queue->processes[i];

            if (p->state == TERMINATED || p->priority != best_priority)
                continue;

            ran_any = 1;
            p->state = RUNNING;

            int exec_time = (p->remaining_time < queue->time_quantum)
                            ? p->remaining_time
                            : queue->time_quantum;

            printf("[T=%3d] PID=%d (%s) [P%d] calistiriliyor | %d birim | Kalan: %d\n",
                   queue->current_time, p->pid, p->name, p->priority,
                   exec_time, p->remaining_time - exec_time);

            p->remaining_time -= exec_time;
            queue->current_time += exec_time;

            for (int j = 0; j < total; j++) {
                if (j != i && queue->processes[j].state != TERMINATED) {
                    queue->processes[j].wait_time += exec_time;
                }
            }

            if (p->remaining_time <= 0) {
                p->state = TERMINATED;
                p->turnaround_time = queue->current_time;
                completed++;
                printf("[T=%3d] PID=%d (%s) TAMAMLANDI\n",
                       queue->current_time, p->pid, p->name);
            } else {
                p->state = READY;
            }
        }

        if (!ran_any) break;
    }

    printf("\n========== PRIORITY RR TAMAMLANDI ==========\n");
    print_schedule_stats(queue);
}

void print_schedule_stats(ReadyQueue *queue) {
    printf("\n--- Istatistikler ---\n");
    printf("%-6s %-20s %-8s %-12s %-12s\n",
           "PID", "Ad", "Burst", "Bekleme", "Turnaround");
    printf("--------------------------------------------------------------\n");

    float total_wait = 0, total_ta = 0;
    int total = queue->count;

    for (int i = 0; i < total; i++) {
        PCB *p = &queue->processes[i];
        printf("%-6d %-20s %-8d %-12d %-12d\n",
               p->pid, p->name, p->total_time,
               p->wait_time, p->turnaround_time);
        total_wait += p->wait_time;
        total_ta += p->turnaround_time;
    }

    printf("--------------------------------------------------------------\n");
    printf("Ortalama Bekleme Suresi:    %.2f\n", total_wait / total);
    printf("Ortalama Turnaround Suresi: %.2f\n", total_ta / total);
}

/* ====== TEST MAIN ====== */
#ifdef SCHEDULER_TEST

static PCB create_pcb(int pid, const char *name, int priority,
                       int burst, int mem_req) {
    PCB p;
    p.pid = pid;
    strncpy(p.name, name, 63);
    p.name[63] = '\0';
    p.priority = priority;
    p.state = READY;
    p.remaining_time = burst;
    p.total_time = burst;
    p.wait_time = 0;
    p.turnaround_time = 0;
    p.memory_required = mem_req;
    return p;
}

int main(void) {
    printf("╔══════════════════════════════════════════════╗\n");
    printf("║   GameOS Scheduler Test (C)                 ║\n");
    printf("╚══════════════════════════════════════════════╝\n");

    /* --- Oyun konsolu process'leri --- */
    PCB game   = create_pcb(1, "SuperMario",    0, 12, 65536);
    PCB audio  = create_pcb(2, "AudioEngine",   1,  6, 16384);
    PCB net    = create_pcb(3, "OnlineService", 2,  8,  8192);
    PCB ui     = create_pcb(4, "GameUI",        1,  4, 32768);
    PCB save   = create_pcb(5, "AutoSave",      3,  3,  4096);

    /* ---- TEST 1: Basit Round Robin ---- */
    printf("\n\n>>> TEST 1: BASELINE - Round Robin (Quantum=3) <<<\n");
    ReadyQueue rr_queue;
    init_scheduler(&rr_queue, 3);

    add_process(&rr_queue, game);
    add_process(&rr_queue, audio);
    add_process(&rr_queue, net);
    add_process(&rr_queue, ui);
    add_process(&rr_queue, save);

    run_round_robin(&rr_queue);

    /* ---- TEST 2: Priority Round Robin ---- */
    printf("\n\n>>> TEST 2: GELISMIS - Priority Round Robin (Quantum=3) <<<\n");
    ReadyQueue prr_queue;
    init_scheduler(&prr_queue, 3);

    /* Process'leri tekrar olustur (state sifirlanmali) */
    add_process(&prr_queue, create_pcb(1, "SuperMario",    0, 12, 65536));
    add_process(&prr_queue, create_pcb(2, "AudioEngine",   1,  6, 16384));
    add_process(&prr_queue, create_pcb(3, "OnlineService", 2,  8,  8192));
    add_process(&prr_queue, create_pcb(4, "GameUI",        1,  4, 32768));
    add_process(&prr_queue, create_pcb(5, "AutoSave",      3,  3,  4096));

    run_priority_rr(&prr_queue);

    /* ---- TEST 3: Karsilastirma ---- */
    printf("\n\n>>> BASELINE vs GELISMIS KARSILASTIRMASI <<<\n");
    printf("%-25s %-15s %-15s\n", "", "Round Robin", "Priority RR");
    printf("-----------------------------------------------------------\n");
    for (int i = 0; i < rr_queue.count; i++) {
        printf("%-25s Bek=%-5d TA=%-5d   Bek=%-5d TA=%-5d\n",
               rr_queue.processes[i].name,
               rr_queue.processes[i].wait_time,
               rr_queue.processes[i].turnaround_time,
               prr_queue.processes[i].wait_time,
               prr_queue.processes[i].turnaround_time);
    }

    printf("\nSonuc: Priority RR, yuksek oncelikli process'lere (GAME)\n");
    printf("daha dusuk bekleme suresi saglar. Oyun konsolunda render\n");
    printf("islemi oncelikli olmalidir.\n");

    return 0;
}

#endif
