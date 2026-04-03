#!/usr/bin/env python3
"""
GameOS - Test Dosyasi
Tum bilesenler icin birim testleri
"""

import sys
import os
import unittest

# Path ayarla
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'simulation'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'challenges'))

from process_manager import ProcessManager, ProcessType, ProcessState
from memory_manager import MemoryManager
from scheduler import RoundRobinScheduler, PriorityRoundRobinScheduler
from file_system import FileSystem, FileType
from concurrency import GameMutex, GameSemaphore


class TestProcessManager(unittest.TestCase):
    def setUp(self):
        self.pm = ProcessManager()

    def test_create_process(self):
        p = self.pm.create_process("TestGame", ProcessType.GAME, priority=0)
        self.assertEqual(p.name, "TestGame")
        self.assertEqual(p.state, ProcessState.READY)
        self.assertEqual(p.priority, 0)

    def test_terminate_process(self):
        p = self.pm.create_process("TestGame", ProcessType.GAME)
        result = self.pm.terminate_process(p.pid)
        self.assertTrue(result)
        self.assertEqual(len(self.pm.processes), 0)

    def test_terminate_nonexistent(self):
        result = self.pm.terminate_process(999)
        self.assertFalse(result)

    def test_block_unblock(self):
        p = self.pm.create_process("TestGame", ProcessType.GAME)
        self.pm.block_process(p.pid)
        self.assertEqual(self.pm.processes[p.pid].state, ProcessState.BLOCKED)
        self.pm.unblock_process(p.pid)
        self.assertEqual(self.pm.processes[p.pid].state, ProcessState.READY)

    def test_pid_increment(self):
        p1 = self.pm.create_process("Game1", ProcessType.GAME)
        p2 = self.pm.create_process("Game2", ProcessType.GAME)
        self.assertEqual(p2.pid, p1.pid + 1)


class TestMemoryManager(unittest.TestCase):
    def setUp(self):
        self.mm = MemoryManager()

    def test_allocate(self):
        result = self.mm.allocate(1, 1024)  # 1 MB
        self.assertTrue(result)
        self.assertIn(1, self.mm.page_tables)

    def test_allocate_too_much(self):
        # 256 MB'den fazla istemeye calis
        result = self.mm.allocate(1, 300 * 1024)
        self.assertFalse(result)

    def test_free(self):
        self.mm.allocate(1, 1024)
        freed = self.mm.free(1)
        self.assertGreater(freed, 0)
        self.assertNotIn(1, self.mm.page_tables)

    def test_translate_address(self):
        self.mm.allocate(1, 16)  # 16 KB = 4 sayfa
        addr = self.mm.translate_address(1, 0, 0)
        self.assertGreaterEqual(addr, 0)

    def test_translate_invalid(self):
        addr = self.mm.translate_address(999, 0, 0)
        self.assertEqual(addr, -1)

    def test_usage_percent(self):
        self.mm.allocate(1, self.mm.TOTAL_MEMORY_KB // 2)
        usage = self.mm.get_usage_percent()
        self.assertAlmostEqual(usage, 50.0, places=0)


class TestScheduler(unittest.TestCase):
    def setUp(self):
        from process_manager import PCB
        self.PCB = PCB

    def test_round_robin(self):
        rr = RoundRobinScheduler(time_quantum=3)
        rr.add_process(self.PCB(1, "Game", ProcessType.GAME, 0, 6))
        rr.add_process(self.PCB(2, "Audio", ProcessType.AUDIO, 1, 3))
        completed = rr.run()
        self.assertEqual(len(completed), 2)
        # Tum process'ler tamamlanmis olmali
        for p in completed:
            self.assertEqual(p.state, ProcessState.TERMINATED)

    def test_priority_rr(self):
        prr = PriorityRoundRobinScheduler(time_quantum=3)
        prr.add_process(self.PCB(1, "Game", ProcessType.GAME, 0, 6))
        prr.add_process(self.PCB(2, "Save", ProcessType.SAVE, 3, 3))
        completed = prr.run()
        self.assertEqual(len(completed), 2)
        # Yuksek oncelikli once tamamlanmis olmali
        self.assertEqual(completed[0].name, "Game")


class TestFileSystem(unittest.TestCase):
    def setUp(self):
        self.fs = FileSystem()

    def test_create_file(self):
        f = self.fs.create_file("test.sav", FileType.SAVE_DATA)
        self.assertIsNotNone(f)
        self.assertIn("test.sav", self.fs.files)

    def test_create_duplicate(self):
        self.fs.create_file("test.sav", FileType.SAVE_DATA)
        f2 = self.fs.create_file("test.sav", FileType.SAVE_DATA)
        self.assertIsNone(f2)

    def test_write_read(self):
        self.fs.create_file("test.sav", FileType.SAVE_DATA)
        self.fs.write_file("test.sav", "hello world")
        content = self.fs.read_file("test.sav")
        self.assertEqual(content, "hello world")

    def test_delete(self):
        self.fs.create_file("test.sav", FileType.SAVE_DATA)
        result = self.fs.delete_file("test.sav")
        self.assertTrue(result)
        self.assertNotIn("test.sav", self.fs.files)

    def test_lock_prevents_write(self):
        self.fs.create_file("test.sav", FileType.SAVE_DATA, owner_pid=1)
        self.fs.lock_file("test.sav", pid=1)
        result = self.fs.write_file("test.sav", "hack", pid=99)
        self.assertFalse(result)

    def test_lock_owner_can_write(self):
        self.fs.create_file("test.sav", FileType.SAVE_DATA, owner_pid=1)
        self.fs.lock_file("test.sav", pid=1)
        result = self.fs.write_file("test.sav", "owner write", pid=1)
        self.assertTrue(result)


class TestConcurrency(unittest.TestCase):
    def test_mutex(self):
        m = GameMutex("test_mutex")
        m.acquire("test")
        self.assertTrue(m.is_locked())
        m.release("test")
        self.assertFalse(m.is_locked())

    def test_semaphore(self):
        s = GameSemaphore("test_sem", max_count=2)
        s.acquire("t1")
        self.assertEqual(s.current_count, 1)
        s.acquire("t2")
        self.assertEqual(s.current_count, 0)
        s.release("t1")
        self.assertEqual(s.current_count, 1)


if __name__ == "__main__":
    print("=" * 50)
    print("  GameOS - Birim Testleri")
    print("=" * 50)
    unittest.main(verbosity=2)
