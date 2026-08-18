HARNESS_ARGS ?=

.PHONY: harness-inspect harness-verify harness-test

harness-inspect:
	python scripts/agent_harness.py inspect $(HARNESS_ARGS)

harness-verify:
	python scripts/agent_harness.py verify $(HARNESS_ARGS)

harness-test:
	python -m pytest tests/test_agent_harness.py -q
