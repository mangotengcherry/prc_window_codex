"""Small CLI demo that works without FastAPI."""

from app.analysis.ranking import rank_l3_features
from app.analysis.window_1d import analyze_single_window
from app.synthetic_data import make_synthetic_frame


def main() -> None:
    frame = make_synthetic_frame(seed=7, wafers=360)
    ranking = rank_l3_features(
        frame,
        product_id="P_ALPHA",
        l3_items=["l3_x", "l3_y", "l3_z"],
        l1_features=["cd_a", "thk_b", "ovl_c", "time_since_pm"],
    )
    single = analyze_single_window(frame, "P_ALPHA", "cd_a", "l3_x")
    print("Top features for l3_x:")
    for row in ranking["by_l3"]["l3_x"][:3]:
        print(f"- {row['l1_feature_name']}: score={row['priority_score']}")
    print("\nBest candidate for cd_a -> l3_x:")
    print(single["candidate_specs"][0])


if __name__ == "__main__":
    main()
