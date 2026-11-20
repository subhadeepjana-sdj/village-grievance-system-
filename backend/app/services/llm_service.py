import os
import json
import logging
from typing import List, Dict, Any, Optional
from app.config import settings

logger = logging.getLogger("uvicorn.error")

SYSTEM_PROMPT = """You are an official Evidence-Grounded AI Assistant for Gram Panchayat Village Grievance Redressal.
CRITICAL INSTRUCTION: You must answer ONLY using the supplied evidence provided in the context below. 
Do NOT invent, extrapolate, or guess complaint status, department names, deadlines, officer names, procedures, or government schemes.
If the evidence does not contain sufficient information to answer the user's question, respond with:
"INSUFFICIENT_EVIDENCE: I could not find verified information in the village knowledge base or complaint records to answer this question."

Supply your response as a JSON object with keys:
- "answer": Clear, concise, helpful natural language answer grounded in evidence.
- "claims": Array of atomic factual statements contained in your answer.
"""

class LLMService:
    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.model_name = settings.LLM_MODEL
        self.genai_client = None
        self._init_client()

    def _init_client(self):
        if self.api_key:
            try:
                from google import genai
                self.genai_client = genai.Client(api_key=self.api_key)
                logger.info(f"Initialized Google GenAI client with model {self.model_name}.")
            except Exception as e:
                logger.warning(f"Failed to initialize GenAI client ({e}). Using deterministic offline generator.")

    def generate_answer(
        self,
        question: str,
        evidence: Optional[List[Dict[str, Any]]] = None,
        evidence_list: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Returns:
        {
           "answer": "...",
           "claims": ["Claim 1", "Claim 2"]
        }
        """
        evidence_items = evidence if evidence is not None else (evidence_list or [])
        # Format evidence context
        evidence_str = "\n\n".join([
            f"--- EVIDENCE ITEM [{i+1}] ({item.get('source_type', 'KB')}) ---\n{item.get('evidence_text', '')}"
            for i, item in enumerate(evidence_items)
        ])

        if not evidence_str.strip():
            return {
                "answer": "I could not find sufficient verified information to answer this question. Please contact the Gram Panchayat office.",
                "claims": ["No evidence found in repository."]
            }

        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"USER QUESTION:\n{question}\n\n"
            f"SUPPLIED EVIDENCE CONTEXT:\n{evidence_str}\n\n"
            f"Generate response in JSON format:"
        )

        if self.genai_client is not None:
            try:
                response = self.genai_client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                )
                text = response.text.strip()
                # Parse JSON if output is markdown wrapped
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()

                parsed = json.loads(text)
                return {
                    "answer": parsed.get("answer", text),
                    "claims": parsed.get("claims", [])
                }
            except Exception as e:
                logger.error(f"GenAI LLM generation error ({e}). Falling back to evidence-synthesis engine.")

        # Offline Evidence-Bound Synthesis Engine (Strict RAG)
        return self._rule_based_evidence_synthesis(question, evidence)

    def _rule_based_evidence_synthesis(self, question: str, evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synthesizes factual answers directly from evidence text to ensure reliability offline."""
        q_lower = question.lower()
        
        # Check if complaint record exists in evidence
        complaint_evidences = [e for e in evidence if e.get("source_type") == "COMPLAINT_RECORD"]
        
        if complaint_evidences:
            comp_text = complaint_evidences[0]["evidence_text"]
            # Extract key details from text representation (robust to multiple schema formats)
            num_match = re_search(r'(?:ID:|RECORD|COMPLAINT)\s*([A-Z0-9-]+)', comp_text) or re_search(r'([A-Z]{2,4}-\d{4}-\d{4,6})', comp_text)
            status_match = re_search(r'Status:\s*([^\n.]+)', comp_text)
            dept_match = re_search(r'Department(?:\s*Handling)?:\s*([^\n.]+)', comp_text)
            category_match = re_search(r'Category:\s*([^\n.]+)', comp_text)
            
            c_num = num_match if num_match else "your complaint"
            c_status = status_match if status_match else "Under Review"
            c_dept = dept_match if dept_match else "Panchayat Office"
            
            answer = f"Your complaint {c_num} is currently '{c_status}' and is being handled by the {c_dept}."
            claims = [
                f"Complaint {c_num} status is {c_status}",
                f"Complaint {c_num} is handled by {c_dept}"
            ]
            return {"answer": answer, "claims": claims}

        # Otherwise synthesize from general knowledge base evidence
        kb_texts = [e["evidence_text"] for e in evidence if e.get("evidence_text")]
        if not kb_texts:
            return {
                "answer": "I could not find sufficient verified information to answer this question. Please contact the relevant village office.",
                "claims": []
            }

        # Select top relevant snippet
        main_snippet = kb_texts[0][:350]
        answer = f"Based on official village documents: {main_snippet}"
        claims = [f"Gram Panchayat documentation states: {main_snippet[:120]}..."]

        return {"answer": answer, "claims": claims}

def re_search(pattern, text):
    import re
    m = re.search(pattern, text)
    return m.group(1).strip() if m else None

llm_service = LLMService()
