"""Sign in to xAI with the public Grok CLI OAuth client and inspect auth status."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from ai_video.production.grok_auth import GrokAuthError, GrokOAuthManager, GrokTokenStore


def _manager() -> GrokOAuthManager:
    return GrokOAuthManager(store=GrokTokenStore())


def _print_status(manager: GrokOAuthManager) -> int:
    status = manager.status()
    print(json.dumps(status.public_dict(), ensure_ascii=False, sort_keys=True))
    return 0 if status.state == "ready" else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("login", help="Sign in through xAI's official device-code page.")
    commands.add_parser("status", help="Show only public account and expiry metadata.")
    commands.add_parser("refresh", help="Explicitly refresh the stored OAuth credential.")
    commands.add_parser("quota", help="Read subscription usage; this cannot enable generation.")
    args = parser.parse_args(argv)

    try:
        manager = _manager()
        if args.command == "login":
            def show_device_code(uri: str, user_code: str) -> None:
                print(f"Verification URI: {uri}", flush=True)
                print(f"User code: {user_code}", flush=True)

            manager.login(on_device_code=show_device_code)
            return _print_status(manager)
        if args.command == "refresh":
            manager.refresh()
        if args.command == "quota":
            from ai_video.production.grok_billing import read_grok_subscription_usage
            status = manager.status()
            if status.state != "ready":
                return _print_status(manager)
            result = read_grok_subscription_usage(account_fingerprint=status.account_fingerprint,
                credential=manager.credential_supplier(status.account_fingerprint))
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
            return 1
        return _print_status(manager)
    except KeyboardInterrupt:
        print(json.dumps({
            "status": "stopped",
            "message": "Grok OAuth interrupted; inspect status before another authentication command.",
        }, ensure_ascii=False))
        return 130
    except GrokAuthError as error:
        print(json.dumps({"status": "stopped", "message": str(error)}, ensure_ascii=False))
        return 1
    except Exception:
        print(json.dumps({
            "status": "stopped",
            "message": "Grok OAuth stopped; sensitive details were suppressed.",
        }, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
