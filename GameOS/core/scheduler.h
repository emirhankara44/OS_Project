#ifndef SCHEDULER_H
#define SCHEDULER_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_PROCESSES 64
#define DEFAULT_QUANTUM 3

typedef enum {
    READY,
    RUNNING,
    BLOCKED,
    TERMINATED
} ProcessState;

typedef struct {
    int pid;
    char name[64];
    int priority;          // 0=highest, 3=lowest
    ProcessState state;
    int remaining_time;    // Kalan CPU burst suresi
    int total_time;        // Toplam CPU burst suresi
    int wait_time;
    int turnaround_time;
    int memory_required;   // KB cinsinden
} PCB;

typedef struct {
    PCB processes[MAX_PROCESSES];
    int count;
    int front;
    int rear;
    int time_quantum;
    int current_time;
} ReadyQueue;

// Scheduler fonksiyonlari
void init_scheduler(ReadyQueue *queue, int quantum);
int add_process(ReadyQueue *queue, PCB process);
PCB* get_next_process(ReadyQueue *queue);
void run_round_robin(ReadyQueue *queue);
void print_schedule_stats(ReadyQueue *queue);

// Priority Scheduler (gelismis versiyon)
void run_priority_rr(ReadyQueue *queue);

#endif
