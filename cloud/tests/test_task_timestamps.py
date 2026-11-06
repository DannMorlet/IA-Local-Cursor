"""Regresión: REST debe entregar marcas de tiempo coherentes con SQLite."""
import json
import tempfile
import unittest
from pathlib import Path

from matick_cloud.tasks import TaskStore


class TaskTimestampTests(unittest.TestCase):
    def test_create_and_status_timestamps_match_persistence(self):
        with tempfile.TemporaryDirectory() as folder:
            store = TaskStore(Path(folder) / "tasks.sqlite")
            created = store.create("Revisar interfaz", "Prueba de persistencia")
            self.assertEqual(created["created_at"], created["updated_at"])
            self.assertEqual(store.list()[0]["updated_at"], created["updated_at"])
            updated = store.set_status(created["id"], "doing")
            self.assertEqual(updated["updated_at"], store.list()[0]["updated_at"])
            self.assertEqual(store.list()[0]["status"], "doing")

    def test_invalid_status_does_not_change_timestamp(self):
        with tempfile.TemporaryDirectory() as folder:
            store = TaskStore(Path(folder) / "tasks.sqlite")
            task = store.create("Conservar tarea")
            with self.assertRaises(ValueError):
                store.set_status(task["id"], "invalid")
            self.assertEqual(store.list()[0]["updated_at"], task["updated_at"])


if __name__ == "__main__":
    unittest.main()
