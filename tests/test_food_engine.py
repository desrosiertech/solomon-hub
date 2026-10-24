"""Food-engine transitions. No model. Vocabulary from GLOSSARY.md / 06-food-engine.md."""

from datetime import UTC, datetime, timedelta

from solomon.food import (
    HouseholdSettings,
    InventorySnapshot,
    Recipe,
    RecipeIngredient,
    SuppressionRule,
    assign_estimated_window,
    derive_confidence,
    filter_suggestions,
    meal_ideas,
    next_item_state,
    use_soon_suggestions,
)


ACQUIRED = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)


def test_leafy_greens_in_fridge_get_a_conservative_four_day_window():
    window = assign_estimated_window(
        category="leafy_greens",
        storage="fridge",
        acquired_at=ACQUIRED,
        profile="conservative",
    )

    assert window.window_days == 4.0
    assert window.estimated_use_by == datetime(2026, 10, 24, 12, 0, tzinfo=UTC)
    assert window.window_source == "category_default"
    assert window.explanation == "Fridge · leafy greens · bought Oct 20 · about 4 days"


def test_cooked_leftovers_in_fridge_get_a_conservative_2_4_day_window():
    window = assign_estimated_window(
        category="cooked_leftovers",
        storage="fridge",
        acquired_at=ACQUIRED,
        profile="conservative",
    )

    assert window.window_days == 2.4
    assert window.estimated_use_by == datetime(2026, 10, 22, 21, 36, tzinfo=UTC)
    assert window.explanation == "Fridge · cooked leftovers · bought Oct 20 · about 2.4 days"


# Leafy greens, fridge, conservative: 4-day window, use-soon lead = 1 day.
LEAFY_USE_BY = datetime(2026, 10, 24, 12, 0, tzinfo=UTC)
LEAFY_WINDOW_DAYS = 4.0
SHORT = HouseholdSettings(
    grace_period=timedelta(minutes=10),
    presume_after=timedelta(minutes=10),
)


def test_item_is_use_soon_one_day_before_the_window_ends():
    assert (
        next_item_state(LEAFY_USE_BY, LEAFY_WINDOW_DAYS, LEAFY_USE_BY - timedelta(days=1), SHORT)
        == "use_soon"
    )


def test_item_is_active_before_the_use_soon_lead():
    assert (
        next_item_state(LEAFY_USE_BY, LEAFY_WINDOW_DAYS, LEAFY_USE_BY - timedelta(days=2), SHORT)
        == "active"
    )


def test_item_is_past_window_at_the_estimated_use_by():
    assert next_item_state(LEAFY_USE_BY, LEAFY_WINDOW_DAYS, LEAFY_USE_BY, SHORT) == "past_window"


def test_unresolved_item_becomes_stale_after_the_grace_period():
    now = LEAFY_USE_BY + timedelta(minutes=10)
    assert next_item_state(LEAFY_USE_BY, LEAFY_WINDOW_DAYS, now, SHORT) == "stale"


def test_unresolved_stale_item_becomes_presumed_discarded_never_eaten():
    now = LEAFY_USE_BY + timedelta(minutes=20)
    assert next_item_state(LEAFY_USE_BY, LEAFY_WINDOW_DAYS, now, SHORT) == "presumed_discarded"
    assert next_item_state(LEAFY_USE_BY, LEAFY_WINDOW_DAYS, now, SHORT) != "consumed"


def test_opening_leafy_greens_halves_the_remaining_default_to_a_two_day_window():
    window = assign_estimated_window(
        category="leafy_greens",
        storage="fridge",
        acquired_at=ACQUIRED,
        opened_at=ACQUIRED,
        profile="conservative",
    )
    # 4.0 * 0.5 = 2.0, above the 1-day floor
    assert window.window_days == 2.0
    assert window.anchor == ACQUIRED


def _spinach(state: str = "use_soon") -> InventorySnapshot:
    return InventorySnapshot(
        id="item-spinach",
        label="Spinach",
        category="leafy_greens",
        storage="fridge",
        quantity_kind="one_package",
        state=state,
        confidence=0.9,
        confidence_band="confident",
        estimated_use_by=LEAFY_USE_BY,
        window_epoch="2026-10-24",
        is_leftover=False,
    )


def _chili(state: str = "use_soon") -> InventorySnapshot:
    return InventorySnapshot(
        id="item-chili",
        label="Leftover chili",
        category="cooked_leftovers",
        storage="fridge",
        quantity_kind="count",
        quantity_count=2,
        state=state,
        confidence=0.9,
        confidence_band="confident",
        estimated_use_by=datetime(2026, 10, 22, 21, 36, tzinfo=UTC),
        window_epoch="2026-10-22",
        is_leftover=True,
    )


SEEDED_RECIPES = (
    Recipe(
        id="sauteed-greens",
        title="Sautéed greens",
        ingredients=(RecipeIngredient(canonical="leafy_greens"),),
    ),
    Recipe(
        id="leftover-bowl",
        title="Leftover chili bowl",
        ingredients=(RecipeIngredient(canonical="cooked_leftovers"),),
    ),
    Recipe(
        id="greens-and-leftovers",
        title="Greens with leftovers",
        ingredients=(
            RecipeIngredient(canonical="leafy_greens"),
            RecipeIngredient(canonical="cooked_leftovers"),
        ),
    ),
    Recipe(
        id="melon-bowl",
        title="Melon & yogurt bowl",
        ingredients=(
            RecipeIngredient(canonical="whole_melon"),
            RecipeIngredient(canonical="dairy_milk", staple=True),
        ),
    ),
    Recipe(
        id="chicken-fried-rice",
        title="Chicken fried rice",
        ingredients=(
            RecipeIngredient(canonical="raw_poultry_or_ground_meat"),
            RecipeIngredient(canonical="dry_goods"),
            RecipeIngredient(canonical="cooked_leftovers"),
        ),
    ),
)


def test_use_soon_lists_past_window_and_use_soon_items_with_cautious_copy():
    suggestions = use_soon_suggestions(
        [_spinach("use_soon"), _chili("past_window")],
        settings=SHORT,
    )
    assert [s.key for s in suggestions] == [
        "past_window:item-chili",
        "use_soon:item-spinach:2026-10-24",
    ]
    assert "may be past its expected freshness window" in suggestions[0].detail
    assert suggestions[1].title == "Spinach"


def test_stale_and_presumed_discarded_items_are_not_surfaced_as_use_soon():
    suggestions = use_soon_suggestions(
        [_spinach("stale"), _chili("presumed_discarded")],
        settings=SHORT,
    )
    assert suggestions == []


def test_stop_asking_suppresses_that_item_on_later_reads():
    stop = SuppressionRule(kind="stop_asking", subject_type="item", subject_id="item-spinach")
    suggestions = filter_suggestions(
        use_soon_suggestions([_spinach(), _chili()], settings=SHORT),
        (stop,),
    )
    assert [s.subject_id for s in suggestions] == ["item-chili"]


def test_meal_ideas_are_empty_when_nothing_is_on_hand():
    assert meal_ideas([], SEEDED_RECIPES, settings=SHORT) == []


def test_meal_ideas_come_from_what_is_on_hand_and_cap_at_three():
    ideas = meal_ideas([_spinach(), _chili()], SEEDED_RECIPES, settings=SHORT)
    # score = 3*use_soon + leftover − 2*missing: 7, 4, 3 — melon/fried rice drop out
    assert [idea.title for idea in ideas] == [
        "Greens with leftovers",
        "Leftover chili bowl",
        "Sautéed greens",
    ]
    assert all(idea.missing == () for idea in ideas)


def test_meal_ideas_skip_recipes_with_too_many_missing_non_staples():
    ideas = meal_ideas([_spinach()], SEEDED_RECIPES, settings=SHORT)
    titles = [idea.title for idea in ideas]
    assert "Sautéed greens" in titles
    assert "Chicken fried rice" not in titles


def test_stale_items_do_not_count_toward_meal_ideas():
    ideas = meal_ideas([_spinach("stale"), _chili("active")], SEEDED_RECIPES, settings=SHORT)
    titles = [idea.title for idea in ideas]
    assert "Leftover chili bowl" in titles
    for idea in ideas:
        assert "Spinach" not in idea.have


def test_quick_add_confidence_stays_0_9_until_halfway_through_the_window():
    # age_ratio 0.4 = 1.6 / 4.0 → decay 1.0; base quick_add 0.9
    assert (
        derive_confidence(
            source="quick_add",
            days_since_strong=1.6,
            window_days=4.0,
            grace_period=timedelta(days=3),
        )
        == 0.9
    )


def test_quick_add_confidence_is_0_27_when_the_window_elapses():
    # age_ratio 1.0 → decay 0.3 → 0.9 * 0.3
    assert (
        derive_confidence(
            source="quick_add",
            days_since_strong=4.0,
            window_days=4.0,
            grace_period=timedelta(days=3),
        )
        == 0.27
    )


def test_dismissed_suggestion_stays_suppressed_until_the_period_ends():
    suggestions = use_soon_suggestions([_spinach(), _chili()], settings=SHORT)
    chili = next(s for s in suggestions if s.subject_id == "item-chili")
    rule = SuppressionRule(
        kind="dismissal",
        subject_type="item",
        subject_id="item-chili",
        key=chili.key,
        until=ACQUIRED + timedelta(days=7),
    )
    hidden = filter_suggestions(suggestions, (rule,), now=ACQUIRED + timedelta(days=6))
    visible = filter_suggestions(suggestions, (rule,), now=ACQUIRED + timedelta(days=8))
    assert "item-chili" not in [s.subject_id for s in hidden]
    assert "item-chili" in [s.subject_id for s in visible]
