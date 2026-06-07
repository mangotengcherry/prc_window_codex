export type Catalog = {
  products: string[];
  l1_features: string[];
  l3_items: string[];
  current_specs: Record<string, unknown>;
};

export type RankingRow = {
  l3_item_name: string;
  l1_feature_name: string;
  priority_score: number;
  mean_abs_shap: number;
  u_safe_r2: number;
  sample_wafer_count: number;
  baseline_ppm: number;
  caution_flags: string[];
};

export type SingleAnalysis = {
  product_id: string;
  l1_feature_name: string;
  l3_item_name: string;
  analysis_population_wafers: number;
  baseline_ppm: number;
  bins: Array<Record<string, number | string>>;
  candidate_specs: Array<Record<string, number | null>>;
  denominators: Record<string, string>;
};

export type InteractionAnalysis = {
  l1_feature_x: string;
  l1_feature_y: string;
  l3_item_name: string;
  x_bin_count: number;
  y_bin_count: number;
  cells: Array<{
    x_bin: number;
    y_bin: number;
    x_center: number;
    y_center: number;
    x_min: number;
    x_max: number;
    y_min: number;
    y_max: number;
    wafer_count: number;
    defect_ppm: number;
    volume_share: number;
    unreliable: boolean;
  }>;
};
