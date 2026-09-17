"""Tests for the pure startup-dialog decision logic (no Qt involved).

Two independent checks, both re-evaluated fresh on every launch, with no
other exception or "already asked" memory:
  - the status question is shown whenever today is still undefined.
  - the message is shown whenever it exists and is not yet marked seen.
"""

from workday_tracker.app import compute_startup_decision
from workday_tracker.models import DayRecord, DayStatus


def test_prompts_when_undefined():
    should_prompt, show_dialog = compute_startup_decision(
        is_weekend_day=False,
        existing_record=DayRecord(),
        has_unseen_message=False,
    )
    assert should_prompt is True
    assert show_dialog is True


def test_prompts_again_on_every_restart_while_still_undefined():
    # Restarting the app several times the same day while the status is still
    # undefined must keep asking - it should never be silently skipped, and
    # nothing about a past clear/prompt is remembered across restarts.
    for _ in range(3):
        should_prompt, show_dialog = compute_startup_decision(
            is_weekend_day=False,
            existing_record=DayRecord(),
            has_unseen_message=False,
        )
        assert should_prompt is True
        assert show_dialog is True


def test_no_prompt_when_defined():
    should_prompt, show_dialog = compute_startup_decision(
        is_weekend_day=False,
        existing_record=DayRecord(am=DayStatus.OFFICE, pm=DayStatus.OFFICE),
        has_unseen_message=False,
    )
    assert should_prompt is False
    assert show_dialog is False


def test_prompts_again_once_a_defined_day_is_cleared():
    # A day that was defined and then cleared is undefined again right now -
    # so it must prompt again, with no "already handled today" memory.
    should_prompt, show_dialog = compute_startup_decision(
        is_weekend_day=False,
        existing_record=DayRecord(am=None, pm=None),
        has_unseen_message=False,
    )
    assert should_prompt is True
    assert show_dialog is True


def test_weekend_never_prompts_even_if_undefined():
    should_prompt, show_dialog = compute_startup_decision(
        is_weekend_day=True,
        existing_record=DayRecord(),
        has_unseen_message=False,
    )
    assert should_prompt is False
    assert show_dialog is False


def test_dialog_shows_for_unseen_message_even_when_day_defined():
    should_prompt, show_dialog = compute_startup_decision(
        is_weekend_day=False,
        existing_record=DayRecord(am=DayStatus.VACATION, pm=DayStatus.VACATION),
        has_unseen_message=True,
    )
    assert should_prompt is False
    assert show_dialog is True


def test_dialog_shows_for_unseen_message_on_weekend():
    should_prompt, show_dialog = compute_startup_decision(
        is_weekend_day=True,
        existing_record=DayRecord(),
        has_unseen_message=True,
    )
    assert should_prompt is False
    assert show_dialog is True


def test_no_dialog_when_message_already_seen_and_day_defined():
    # A message that has already been checked off must not keep popping up.
    should_prompt, show_dialog = compute_startup_decision(
        is_weekend_day=False,
        existing_record=DayRecord(am=DayStatus.OFFICE, pm=DayStatus.OFFICE),
        has_unseen_message=False,  # caller passes False once message.seen is True
    )
    assert should_prompt is False
    assert show_dialog is False


def test_both_checks_apply_independently():
    # Undefined day AND an unseen message: both parts of the dialog show.
    should_prompt, show_dialog = compute_startup_decision(
        is_weekend_day=False,
        existing_record=DayRecord(),
        has_unseen_message=True,
    )
    assert should_prompt is True
    assert show_dialog is True
