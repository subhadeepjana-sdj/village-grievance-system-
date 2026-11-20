from typing import List, Dict, Any

class ConfidenceCalculator:
    def calculate_overall_confidence(self, verification_results: List[Dict[str, Any]]) -> float:
        """
        Calculates aggregate confidence score (0.0 to 100.0%).
        """
        if not verification_results:
            return 0.0

        supported_count = sum(1 for v in verification_results if v["verification_result"] == "SUPPORTED")
        contradicted_count = sum(1 for v in verification_results if v["verification_result"] == "CONTRADICTED")
        
        # Penalize severely if contradicted
        if contradicted_count > 0:
            return round(max(0.0, 40.0 - (contradicted_count * 20.0)), 1)

        total = len(verification_results)
        conf_scores = [v.get("confidence", 0.5) for v in verification_results]
        avg_conf = sum(conf_scores) / total if total > 0 else 0.0
        
        support_ratio = supported_count / total if total > 0 else 0.0
        overall = (support_ratio * 0.7 + avg_conf * 0.3) * 100.0

        return round(min(max(overall, 0.0), 99.0), 1)

confidence_calculator = ConfidenceCalculator()
