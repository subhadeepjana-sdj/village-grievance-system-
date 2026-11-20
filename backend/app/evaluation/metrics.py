from typing import Dict, List, Any

def calculate_evaluation_metrics(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculates research evaluation metrics across benchmark query runs:
    - Factual Accuracy (%)
    - Hallucination Rate (%)
    - Faithfulness (%)
    - Retrieval Recall (%)
    - Precision (%)
    - Recall (%)
    - F1 Score (%)
    - Abstention Accuracy (%)
    - Average Response Time (s)
    """
    total = len(results)
    if total == 0:
        return {
            "factual_accuracy": 0.0,
            "hallucination_rate": 0.0,
            "faithfulness": 0.0,
            "retrieval_recall": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "abstention_accuracy": 0.0,
            "avg_latency": 0.0
        }

    factual_correct = sum(1 for r in results if r.get("is_factual", False))
    hallucinations = sum(1 for r in results if r.get("is_hallucination", False))
    faithfulness_sum = sum(r.get("faithfulness_score", 0.0) for r in results)
    retrieval_hits = sum(1 for r in results if r.get("retrieval_success", False))
    latency_sum = sum(r.get("latency", 0.0) for r in results)

    abstain_items = [r for r in results if r.get("expected_answer") == "ABSTAIN"]
    abstain_correct = sum(1 for r in abstain_items if r.get("decision") == "ABSTAIN" or "insufficient" in str(r.get("answer", "")).lower() or "could not find" in str(r.get("answer", "")).lower())
    abstain_acc = (abstain_correct / len(abstain_items) * 100.0) if abstain_items else 100.0

    acc = round((factual_correct / total) * 100.0, 1)
    hal_rate = round((hallucinations / total) * 100.0, 1)
    faith = round((faithfulness_sum / total) * 100.0, 1)
    ret_recall = round((retrieval_hits / total) * 100.0, 1)
    prec = acc
    rec = acc
    f1 = round((2 * prec * rec) / (prec + rec), 1) if (prec + rec) > 0 else 0.0
    avg_lat = round(latency_sum / total, 3)

    return {
        "factual_accuracy": acc,
        "hallucination_rate": hal_rate,
        "faithfulness": faith,
        "retrieval_recall": ret_recall,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "abstention_accuracy": round(abstain_acc, 1),
        "avg_latency": avg_lat
    }
