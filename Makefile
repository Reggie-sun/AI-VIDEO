BASE_REF ?=
HEAD_REF ?= HEAD
RECEIPT ?=
RUN_ID ?=
LEVEL ?= related

.PHONY: frontend harness-inspect harness-verify harness-verify-range harness-receipt harness-audit harness-repository harness-test harness-focused harness-related harness-full

frontend:
	cd provider-console && npm run dev -- --host 127.0.0.1

harness-inspect:
	python scripts/agent_harness.py inspect --level "$(LEVEL)"

harness-verify:
	python scripts/agent_harness.py verify --staged --level "$(LEVEL)" $(if $(RUN_ID),--run-id "$(RUN_ID)",)

harness-verify-range:
	@test -n "$(BASE_REF)" || { echo "BASE_REF is required" >&2; exit 2; }
	python scripts/agent_harness.py verify --base-ref "$(BASE_REF)" --head-ref "$(HEAD_REF)" --level "$(LEVEL)" $(if $(RUN_ID),--run-id "$(RUN_ID)",)

harness-focused:
	$(MAKE) harness-verify LEVEL=focused

harness-related:
	$(MAKE) harness-verify LEVEL=related

harness-full:
	$(MAKE) $(if $(BASE_REF),harness-verify-range,harness-verify) LEVEL=full

harness-receipt:
	@test -n "$(RECEIPT)" || { echo "RECEIPT is required" >&2; exit 2; }
	python scripts/agent_harness.py verify-receipt "$(RECEIPT)"

harness-audit:
	python scripts/agent_harness.py policy-audit

harness-repository:
	@env -i PATH="$(PATH)" LANG=C.UTF-8 AI_VIDEO_HARNESS_NO_NETWORK=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTEST_PLUGINS=scripts.harness_pytest_guard python -m pytest -p no:cacheprovider -q
	@env -i PATH="$(PATH)" LANG=C.UTF-8 python -m scripts.architecture_gate check

harness-test:
	@env -i PATH="$(PATH)" LANG=C.UTF-8 AI_VIDEO_HARNESS_NO_NETWORK=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTEST_PLUGINS=scripts.harness_pytest_guard python -m pytest -p no:cacheprovider tests/test_agent_harness.py -q
