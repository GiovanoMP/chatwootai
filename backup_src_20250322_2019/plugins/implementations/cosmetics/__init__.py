"""
Plugins específicos para o domínio de cosméticos.
"""

from .product_recommendation import ProductRecommendationPlugin
from .treatment_scheduler import TreatmentSchedulerPlugin

__all__ = ["ProductRecommendationPlugin", "TreatmentSchedulerPlugin"]
