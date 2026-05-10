from __future__ import annotations

import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.repository_test_support import ROOT


SCRIPT_PATH = ROOT / "scripts" / "api_quiz_bank_production_monitor_snapshot.sh"

FAILURE_ALERT_SCENARIOS = [
    (
        "ready",
        {"FAKE_READY_CODE": "503"},
        "| Public ready with edge key | 503 |",
        "public ready with edge key expected 200 got 503",
    ),
    (
        "backup",
        {"FAKE_BACKUP_RESULT": "failed", "FAKE_BACKUP_STATUS": "1"},
        "| Latest PostgreSQL backup service result | failed/1 |",
        "latest PostgreSQL backup service expected success/0 got failed/1",
    ),
    (
        "disk",
        {"API_QUIZ_BANK_DISK_USED_MAX_PERCENT": "10"},
        "| Disk used percent | 42 |",
        "disk usage expected <= 10% got 42%",
    ),
    (
        "memory",
        {"API_QUIZ_BANK_MEM_AVAILABLE_MIN_MB": "4096"},
        "| Memory available MB | 2048 |",
        "memory available expected >= 4096MB got 2048MB",
    ),
    (
        "api-restart",
        {"FAKE_API_RESTART_COUNT": "1"},
        "| API container restart count | 1 |",
        "API container restarts expected <= 0 got 1",
    ),
    (
        "postgres-restart",
        {"FAKE_POSTGRES_RESTART_COUNT": "1"},
        "| PostgreSQL container restart count | 1 |",
        "PostgreSQL container restarts expected <= 0 got 1",
    ),
    (
        "api-health",
        {"FAKE_API_STATE": "running/unhealthy"},
        "| API container | running/unhealthy |",
        "API container expected running/healthy got running/unhealthy",
    ),
]


class ProductionMonitorSnapshotTests(unittest.TestCase):
    def test_success_snapshot_records_operational_alert_signals(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            result = self.run_monitor(temp_path)

            report = self.read_report(temp_path)
            alert_log = temp_path / "curl_alert.log"

        self.assertEqual(0, result.returncode, report + result.stderr)
        self.assertIn("production-monitor-snapshot-ok", result.stdout)
        self.assertFalse(alert_log.exists())
        self.assertIn("| Latest PostgreSQL backup service result | success/0 |", report)
        self.assertIn("| Disk used percent | 42 |", report)
        self.assertIn("| Memory available MB | 2048 |", report)
        self.assertIn("| API container restart count | 0 |", report)
        self.assertIn("| PostgreSQL container restart count | 0 |", report)
        self.assertIn("| Alert notification | disabled |", report)
        self.assertIn("| Failures | none |", report)

    def test_failure_conditions_send_alert_without_exposing_webhook(self) -> None:
        for name, env_overrides, expected_report_row, expected_failure in FAILURE_ALERT_SCENARIOS:
            with self.subTest(name=name):
                self.assert_failure_sends_alert(
                    env_overrides,
                    expected_report_row,
                    expected_failure,
                )

    def assert_failure_sends_alert(
        self,
        env_overrides: dict[str, str],
        expected_report_row: str,
        expected_failure: str,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            webhook_url = "https://alerts.example.test/api-quiz-bank-secret-hook"
            result = self.run_monitor(
                temp_path,
                {"API_QUIZ_BANK_ALERT_WEBHOOK_URL": webhook_url, **env_overrides},
            )

            report = self.read_report(temp_path)
            alert_log = (temp_path / "curl_alert.log").read_text(encoding="utf-8")
            alert_payload = self.read_alert_payload(temp_path)

        self.assertEqual(1, result.returncode)
        self.assertIn("production-monitor-snapshot-failed", result.stderr)
        self.assertIn(webhook_url, alert_log)
        self.assertIn(expected_report_row, report)
        self.assertIn("| Alert notification | sent |", report)
        self.assertIn(expected_failure, report)
        self.assertIn(expected_failure, alert_payload)
        self.assertNotIn(webhook_url, report)
        self.assertNotIn(webhook_url, alert_payload)

    def run_monitor(
        self,
        temp_path: Path,
        env_overrides: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        fake_bin = temp_path / "bin"
        fake_bin.mkdir()
        self.write_fake_commands(fake_bin)

        meminfo_path = temp_path / "meminfo"
        meminfo_path.write_text(
            "MemTotal:       4096000 kB\nMemAvailable:   2097152 kB\n",
            encoding="utf-8",
        )

        env = os.environ.copy()
        env.update(
            {
                "PATH": f"{fake_bin}{os.pathsep}{env['PATH']}",
                "FAKE_CURL_LOG": str(temp_path / "curl_alert.log"),
                "API_QUIZ_BANK_BASE_URL": "https://api.example.test",
                "API_QUIZ_BANK_PUBLIC_API_KEY": "test-public-key",
                "API_QUIZ_BANK_MONITOR_REPORT_DIR": str(temp_path / "reports"),
                "API_QUIZ_BANK_DISK_CHECK_PATH": str(temp_path),
                "API_QUIZ_BANK_MEMINFO_FILE": str(meminfo_path),
            }
        )
        if env_overrides:
            env.update(env_overrides)

        return subprocess.run(
            ["sh", str(SCRIPT_PATH)],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
            env=env,
        )

    def write_fake_commands(self, fake_bin: Path) -> None:
        self.write_executable(fake_bin / "date", 'printf "20260510T120000Z\\n"\n')
        self.write_executable(fake_bin / "curl", FAKE_CURL)
        self.write_executable(fake_bin / "docker", FAKE_DOCKER)
        self.write_executable(fake_bin / "systemctl", FAKE_SYSTEMCTL)
        self.write_executable(fake_bin / "df", FAKE_DF)

    def write_executable(self, path: Path, body: str) -> None:
        path.write_text(f"#!/usr/bin/env sh\n{body}", encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR)

    def read_report(self, temp_path: Path) -> str:
        report_path = temp_path / "reports" / "production_monitor_20260510T120000Z.md"
        return report_path.read_text(encoding="utf-8")

    def read_alert_payload(self, temp_path: Path) -> str:
        payload_path = temp_path / "reports" / "production_monitor_alert_20260510T120000Z.txt"
        return payload_path.read_text(encoding="utf-8")


FAKE_CURL = r'''
is_alert=0
has_key=0
last_arg=""
url_arg=""
while [ "$#" -gt 0 ]; do
  [ "$1" = "--data-binary" ] && is_alert=1
  case "$1" in
    X-API-Key:*)
      has_key=1
      ;;
    http://*|https://*)
      url_arg="$1"
      ;;
  esac
  last_arg="$1"
  shift
done

if [ "$is_alert" = "1" ]; then
  printf "%s\n" "$last_arg" >>"$FAKE_CURL_LOG"
  exit "${FAKE_ALERT_EXIT:-0}"
fi

case "$url_arg" in
  */health)
    if [ "$has_key" = "1" ]; then
      printf "%s" "${FAKE_HEALTH_KEY_CODE:-200}"
    else
      printf "%s" "${FAKE_HEALTH_NO_KEY_CODE:-401}"
    fi
    ;;
  */ready)
    printf "%s" "${FAKE_READY_CODE:-200}"
    ;;
  */v1/quiz-items/next)
    printf "%s" "${FAKE_DELIVERY_NO_KEY_CODE:-401}"
    ;;
  *)
    printf "000"
    ;;
esac
'''

FAKE_DOCKER = r'''
format=""
container=""
while [ "$#" -gt 0 ]; do
  if [ "$1" = "-f" ]; then
    shift
    format="$1"
  else
    container="$1"
  fi
  shift
done

case "$format" in
  *RestartCount*)
    case "$container" in
      api-quiz-bank-pilot)
        printf "%s\n" "${FAKE_API_RESTART_COUNT:-0}"
        ;;
      api-quiz-bank-postgres)
        printf "%s\n" "${FAKE_POSTGRES_RESTART_COUNT:-0}"
        ;;
    esac
    ;;
  *)
    case "$container" in
      api-quiz-bank-pilot)
        printf "%s\n" "${FAKE_API_STATE:-running/healthy}"
        ;;
      api-quiz-bank-postgres)
        printf "%s\n" "${FAKE_POSTGRES_STATE:-running/healthy}"
        ;;
    esac
    ;;
esac
'''

FAKE_SYSTEMCTL = r'''
if [ "$1" = "is-active" ]; then
  printf "%s\n" "${FAKE_BACKUP_TIMER_STATE:-active}"
  exit 0
fi

if [ "$1" = "show" ]; then
  printf "%s\n%s\n" "${FAKE_BACKUP_RESULT:-success}" "${FAKE_BACKUP_STATUS:-0}"
fi
'''

FAKE_DF = r'''
printf "Filesystem 1024-blocks Used Available Capacity Mounted on\n"
printf "/dev/test 100 42 58 %s%% /\n" "${FAKE_DISK_USED_PERCENT:-42}"
'''


if __name__ == "__main__":
    unittest.main()
