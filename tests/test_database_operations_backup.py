from __future__ import annotations

import os
import stat
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from tests.repository_test_support import ROOT


BACKUP_SCRIPT = ROOT / "scripts" / "api_quiz_bank_postgres_backup.sh"
RESTORE_SCRIPT = ROOT / "scripts" / "api_quiz_bank_postgres_restore_drill.sh"


class DatabaseOperationsBackupTests(unittest.TestCase):
    def test_postgres_backup_writes_metadata_offsite_copy_and_retention_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            backup_dir = temp_path / "backups"
            offsite_dir = temp_path / "offsite"
            old_backup = self.write_old_backup(backup_dir)

            result = self.run_script(
                BACKUP_SCRIPT,
                temp_path,
                {
                    "API_QUIZ_BANK_BACKUP_DIR": str(backup_dir),
                    "API_QUIZ_BANK_BACKUP_OFFSITE_DIR": str(offsite_dir),
                    "API_QUIZ_BANK_BACKUP_RETENTION_DAYS": "30",
                },
            )

            backup_path = backup_dir / "api_quiz_bank_pg_20260510T130000Z.dump"
            metadata = (backup_path.with_suffix(".dump.meta")).read_text(encoding="utf-8")
            old_backup_removed = not old_backup.exists()
            offsite_backup_exists = (offsite_dir / backup_path.name).exists()
            offsite_metadata = (
                offsite_dir / backup_path.with_suffix(".dump.meta").name
            ).read_text(encoding="utf-8")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(f"postgres-backup-ok {backup_path}", result.stdout)
        self.assertTrue(old_backup_removed)
        self.assertTrue(offsite_backup_exists)
        self.assertIn("backup_id=api_quiz_bank_pg_20260510T130000Z", metadata)
        self.assertIn("checksum_sha256=", metadata)
        self.assertIn("retention_days=30", metadata)
        self.assertIn("offsite_status=copied", metadata)
        self.assertIn("offsite_status=copied", offsite_metadata)
        self.assertIn("restore_tested_status=pending", metadata)

    def test_postgres_backup_script_records_encryption_policy(self) -> None:
        script = BACKUP_SCRIPT.read_text(encoding="utf-8")

        self.assertIn("API_QUIZ_BANK_BACKUP_ENCRYPTION_KEY_FILE", script)
        self.assertIn("openssl enc -aes-256-cbc -salt -pbkdf2", script)
        self.assertIn("rm -f \"$backup_path\"", script)
        self.assertIn("postgres-custom+openssl-aes-256-cbc", script)

    def test_restore_drill_writes_periodic_schedule_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            backup_path = temp_path / "selected.dump"
            backup_path.write_text("backup-bytes", encoding="utf-8")
            report_dir = temp_path / "restore-reports"

            result = self.run_script(
                RESTORE_SCRIPT,
                temp_path,
                {
                    "API_QUIZ_BANK_POSTGRES_BACKUP_PATH": str(backup_path),
                    "API_QUIZ_BANK_RESTORE_DRILL_REPORT_DIR": str(report_dir),
                    "API_QUIZ_BANK_RESTORE_DRILL_INTERVAL_DAYS": "30",
                    "API_QUIZ_BANK_RESTORE_DRILL_OWNER": "ops-owner",
                },
            )

            report_path = report_dir / "postgres_restore_drill_20260510T130000Z.md"
            report = report_path.read_text(encoding="utf-8")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("postgres-restore-drill-ok api_quiz_bank_restore_drill", result.stdout)
        self.assertIn("Owner: ops-owner", report)
        self.assertIn(f"Source backup: {backup_path}", report)
        self.assertIn("Required interval days: 30", report)
        self.assertIn("Next drill due: within 30 days from this report", report)

    def run_script(
        self,
        script_path: Path,
        temp_path: Path,
        env_overrides: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        fake_bin = temp_path / "bin"
        fake_bin.mkdir()
        self.write_fake_commands(fake_bin)

        env = os.environ.copy()
        env.update(
            {
                "PATH": f"{fake_bin}{os.pathsep}{env['PATH']}",
                **env_overrides,
            }
        )
        return subprocess.run(
            ["sh", str(script_path)],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
            env=env,
        )

    def write_old_backup(self, backup_dir: Path) -> Path:
        backup_dir.mkdir()
        old_backup = backup_dir / "api_quiz_bank_pg_20200101T000000Z.dump"
        old_backup.write_text("old-backup", encoding="utf-8")
        old_time = time.time() - 40 * 24 * 60 * 60
        os.utime(old_backup, (old_time, old_time))
        return old_backup

    def write_fake_commands(self, fake_bin: Path) -> None:
        self.write_executable(fake_bin / "date", 'printf "20260510T130000Z\\n"\n')
        self.write_executable(fake_bin / "docker", FAKE_DOCKER)

    def write_executable(self, path: Path, body: str) -> None:
        path.write_text(f"#!/usr/bin/env sh\n{body}", encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR)


FAKE_DOCKER = r'''
case "$*" in
  *pg_dump*)
    printf "PGDUMP"
    ;;
  *psql*)
    printf "t\n"
    ;;
  *)
    ;;
esac
'''


if __name__ == "__main__":
    unittest.main()
