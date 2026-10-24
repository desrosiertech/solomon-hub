from solomon.food import Recipe, RecipeIngredient

HOUSEHOLD_ID = "household-1"
MEMBER_ID = "member-adult"
MEMBER_NAME = "Adult"

SEED_RECIPES = (
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
