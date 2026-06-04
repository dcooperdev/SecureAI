import os
import json
import time
import logging
from google import genai
from google.api_core import exceptions
from dotenv import load_dotenv
from galt.core.config import get_llm_model

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Bridge:
    def __init__(self, data_dir=None):
        load_dotenv()
        self.api_key = os.getenv("GOOGLE_API_KEY")
        # By default use vault/ or galt/data/
        self.data_dir = data_dir or os.path.join(os.getcwd(), "vault")
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        self.state_file = os.path.join(self.data_dir, "last_scan_state.json")
        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Error initializing Gemini Client: {e}")

    def _clean_for_comparison(self, data):
        """
        Cleans the data for comparison (Diff), removing timestamps
        and fields that change on each run without affecting security.
        """
        if isinstance(data, list):
            return [self._clean_for_comparison(item) for item in data]
        elif isinstance(data, dict):
            new_dict = {}
            for k, v in data.items():
                # Ignore time fields or ephemeral unique IDs
                if k in ["timestamp", "time", "date", "scan_id", "epoch", "ui_date_short", "ui_date_full", "pid"]:
                    continue
                new_dict[k] = self._clean_for_comparison(v)
            return new_dict
        else:
            return data

    def _load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading previous state: {e}")
        return None

    def _save_state(self, findings, score, narrative):
        try:
            state = {
                "findings": findings,
                "score": score,
                "narrative": narrative,
                "timestamp": time.time()
            }
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving state: {e}")

    def get_analysis(self, current_findings, current_score):
        """
        Main flow:
        1. Load previous state.
        2. Compare (Diff).
        3. Decide whether to call AI or use cache.
        4. Return result + state metadata.
        """
        last_state = self._load_state()
        
        # --- 1. Comparison Logic (Diff) ---
        has_changed = True
        improvement_msg = ""
        
        clean_current = self._clean_for_comparison(current_findings)
        
        if last_state:
            last_score = last_state.get("score", 0)
            clean_last = self._clean_for_comparison(last_state.get("findings", []))
            
            # Compare data exactness and score
            # Convert to sorted json string to compare complex structures
            current_str = json.dumps(clean_current, sort_keys=True)
            last_str = json.dumps(clean_last, sort_keys=True)
            
            if current_str == last_str and current_score == last_score:
                has_changed = False
            
            # Detect improvement
            if current_score > last_score:
                improvement_msg = f"The user improved their security (Score rose from {last_score} to {current_score}). Identify what changed, congratulate them, and explain the benefit."

        # --- 2. Decision Making ---
        
        # CASE A: Cache Hit
        if not has_changed and last_state and last_state.get("narrative"):
            logger.info("Smart Cache: No changes detected. Reusing narrative.")
            return {
                "json_report": last_state["narrative"], # Renamed from markdown to json_report
                "ai_status": "cached",
                "score": current_score,
                "used_cache": True
            }

        # CASE B: Changes or Cache Miss -> Call AI
        logger.info(f"Changes detected. Requesting analysis from Gemini...")
        
        prompt_context = "Analyze these security findings."
        if improvement_msg:
            prompt_context += f"\n\nCONTEXT NOTE: {improvement_msg}"

        try:
            if not self.client:
                raise ValueError("Gemini client not initialized (Missing API Key)")

            response_json_obj = self._call_gemini(clean_current, current_score, prompt_context)
            
            # Save new state (narrative is now a dict)
            self._save_state(current_findings, current_score, response_json_obj)
            
            return {
                "json_report": response_json_obj, # Return Dict
                "ai_status": "online",
                "score": current_score,
                "used_cache": False
            }

        except Exception as e:
            logger.error(f"AI call failed: {e}")
            # CASE C: Fallback / Error
            fallback_json = self._get_fallback_narrative(current_score, e)
            return {
                "json_report": fallback_json,
                "ai_status": "offline",
                "score": current_score,
                "error": str(e)
            }

    def _call_gemini(self, findings, score, context_msg):
        # Sistema de Prompting JSON STRICT
        system_prompt = f"""
        You are a Cybersecurity Engine. Analyze the scan data. 
        Return ONLY valid JSON adhering to this schema: 
        {{ 
            "summary": "Brief executive summary string", 
            "score_reasoning": "Why is the score {score}?", 
            "critical_risks": [{{"id": "port_445", "title": "SMB Exposure", "severity": "High", "fix": "Close port"}}], 
            "recommendations": ["Action 1", "Action 2"] 
        }} 
        Do not use Markdown formatting. Do not wrap in ```json code blocks.
        """
        
        content = f"DATOS TÉCNICOS:\n{json.dumps(findings, indent=2)}"
        
        response = self.client.models.generate_content(
            model=get_llm_model(),
            contents=system_prompt + "\n\n" + content
        )
        
        # Clean and Parse
        raw_text = response.text.replace('```json', '').replace('```', '').strip()
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            # Fallback for malformed JSON
            logger.error("JSON PARSE ERROR on AI Response. Returning RAW wrapper.")
            return {"error": "Invalid JSON from AI", "raw_output": raw_text}

    def _get_fallback_narrative(self, score, error=None):
        """
        Generates offline JSON.
        """
        logger.warning(f"Generating offline JSON. Reason: {error}")
        
        status = "Secure"
        if score < 60: status = "Critical"
        elif score < 90: status = "Warning"
        
        return {
            "summary": f"Offline Mode Active. System Status: {status}. Static analysis detected issues.",
            "score_reasoning": f"Score is {score}/100 based on local rules.",
            "critical_risks": [{"id": "offline_error", "title": "AI Offline", "severity": "Info", "fix": str(error)}],
            "recommendations": ["Check internet connection", "Verify API Key", "Review local firewall rules manually"]
        }

if __name__ == "__main__":
    # Quick test
    b = Bridge()
    print("Testing Bridge...")
    res = b.get_analysis([{"test": 1}], 80)
    print(res)
