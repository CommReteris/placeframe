from pydantic import BaseModel


class LocalizationMetrics(BaseModel):
    inlier_ratio: float
    reprojection_error_median: float
    num_inliers: int
    num_correspondences: int
    num_matches: int
    inlier_coverage: float
