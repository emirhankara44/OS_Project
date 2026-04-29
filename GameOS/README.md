# GameOS - Game Console Operating System Simulation

## About the Project
GameOS is a project that simulates the core components of a real game console operating system. Built with both Python and C, it demonstrates operating system concepts through practical examples.

## Theme: Game Console OS
All design decisions are made from the perspective of "this is a game console":
- **Round Robin Scheduler**: Game, audio, network, and UI processes receive fair CPU time
- **Fixed Page Size (4KB)**: The console's limited RAM (256MB) is managed efficiently
- **Mutex/Semaphore**: Game state is safely protected across multiple threads
- **Simple File System**: Sufficient for save files and ROMs

## Components

| # | Component | Language | Files |
|---|-----------|----------|-------|
| 1 | Process Management & Scheduler | C + Python | `core/scheduler.c`, `simulation/process_manager.py`, `simulation/scheduler.py` |
| 2 | Memory Management (Paging) | C + Python | `core/memory.c`, `simulation/memory_manager.py` |
| 3 | Concurrency & Synchronization | Python | `simulation/concurrency.py` |
| 4 | File System | Python | `simulation/file_system.py` |
| 5 | Engineering Challenges | Python | `challenges/priority_inversion.py` |
| 6 | Failure Scenarios | Python | `challenges/failure_scenarios.py` |
| 7 | Logging System | Python | `simulation/logger.py` |

## Team Workload (4 People)

| Person | Responsibility |
|--------|----------------|
| Person 1 | Process Management + Scheduler (C + Python) |
| Person 2 | Memory Management (C + Python) |
| Person 3 | Concurrency + Engineering Challenges (Python) |
| Person 4 | File System + Logger + Failure Scenarios (Python) |

## Running the Project

### Python Simulation
```bash
cd GameOS/simulation
python3 main.py
```

### C Build
```bash
cd GameOS/core
make
./scheduler_test
./memory_test
```

### Tests
```bash
cd GameOS/tests
python3 test_all.py
```

## Project Structure
```
GameOS/
├── core/                    # C - Low-level components
│   ├── scheduler.c/h       # Round Robin & Priority Scheduler
│   ├── memory.c/h          # Paging & Address Translation
│   └── Makefile
├── simulation/              # Python - Simulation layer
│   ├── main.py              # Main menu and entry point
│   ├── process_manager.py   # PCB and process lifecycle
│   ├── scheduler.py         # RR & Priority RR Scheduler
│   ├── memory_manager.py    # Paging memory management
│   ├── file_system.py       # File CRUD operations
│   ├── concurrency.py       # Mutex, Semaphore, Thread
│   └── logger.py            # Centralized logging system
├── challenges/
│   ├── priority_inversion.py  # Priority Inversion & Deadlock
│   └── failure_scenarios.py   # OOM, Disk Full, Process Crash
├── tests/
│   └── test_all.py          # Unit tests
└── README.md
```

## Design Decisions

### Process Management and Scheduler
**Selected design:** Round Robin is used as the baseline design, and Priority Round Robin is used as the advanced design. The PCB stores PID, name, type, priority, state, burst time, remaining time, and memory requirement.

**Alternative:** FCFS/FIFO and MLFQ were considered.

**Why it was not selected:** FIFO is simple, but a long-running game process can block audio or UI tasks. MLFQ is more realistic, but parameters such as queue count, aging, and quantum tuning add too much complexity for the project scope.

**Trade-off:** Round Robin is fair, but it increases the number of context switches. Priority RR speeds up game/render processes, but lower-priority save/network processes may wait longer.

### Memory Management
**Selected design:** The system uses 256MB of physical memory, a fixed 4KB page size, and one page table per process. Instead of demand paging, the simulator allocates all pages of a process at startup. If memory is insufficient, a controlled OOM scenario is triggered.

**Alternative:** Segmentation and demand paging with LRU page replacement were considered.

**Why it was not selected:** Segmentation increases the risk of external fragmentation. Demand paging with LRU is more realistic, but it requires a disk/swap layer and a page replacement policy. In this project, the main goal is to make memory limits, address translation, and OOM behavior observable.

**Trade-off:** Fixed paging simplifies address translation and observation, and it prevents external fragmentation. However, because all pages are allocated upfront, memory fills up faster and lazy allocation behavior from real operating systems is not modeled.

### Concurrency and Synchronization
**Selected design:** A Mutex is used for shared game state, and a Semaphore is used for limited network connections. A race condition is also demonstrated through score updates without a mutex.

**Alternative:** Spinlocks and lock-free data structures were considered.

**Why it was not selected:** Spinlocks waste CPU time and are not efficient or meaningful in a Python simulation. Lock-free approaches are unnecessarily complex and error-prone for a course project.

**Trade-off:** Mutexes and Semaphores provide a simple and readable solution. However, an incorrect lock order can create deadlocks, and threads waiting on locks may experience delays.

### File System
**Selected design:** A flat file system is used for save, ROM, config, and log files. It supports CRUD operations, file size/storage limits, and file locks.

**Alternative:** A hierarchical directory-based file system and a cached file system were considered.

**Why it was not selected:** A hierarchical structure adds unnecessary metadata and path parsing for the demo. A cached design could demonstrate performance, but it introduces additional problems such as consistency and cache invalidation.

**Trade-off:** A flat file system is simple, testable, and sufficient for save/ROM scenarios. However, because all files share the same namespace, there is no directory isolation, and it does not scale well to a large number of files.

### Engineering Challenge: Priority Inversion
**Problem:** A low-priority download thread holds the GPU lock while a high-priority render thread waits. A medium-priority audio thread runs without needing the GPU and extends the render thread's waiting time.

**Solution:** Priority inheritance is simulated. When the high-priority render thread waits for the GPU lock, the low-priority thread holding the lock temporarily receives a higher priority and finishes the critical section faster.

**Limitation:** This is not a real kernel scheduler. It is an event/signal-based simulation built on Python threads. Even so, the logs show the lock owner boost, the waiting high-priority thread, and the return to the original priority after the boost ends.

### Cross-Component Interactions
- Scheduler + ProcessManager + FileSystem: When a GAME process writes a save file, it becomes BLOCKED, is removed from the ready queue, and returns to READY after I/O completes.
- Scheduler + MemoryManager: The pages of a BLOCKED process are kept in memory. When the process completes, its memory is released.
- FileSystem + Concurrency: A file lock prevents another PID from writing to the same file.

### Failure Scenarios
- Out of Memory: When multiple large games are loaded, memory becomes insufficient. The system releases the memory of an older game and retries.
- Disk/File Limit: The 1MB file limit is exceeded. The system recovers by using a smaller save file.
- Process Crash: When a game process crashes, its memory and save file are cleaned up.
