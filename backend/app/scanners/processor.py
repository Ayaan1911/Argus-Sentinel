from app.intelligence.loader import get_intelligence_loader
from app.engines import reasoning_engine, confidence_engine

class FindingProcessor:
    def __init__(self):
        self.loader = get_intelligence_loader()

    def process(self, raw_finding: dict, scan_id: str, audience: str) -> dict:
        f_type = raw_finding.get("type", "").lower()
        title = raw_finding.get("title", "")
        raw_data = raw_finding.get("raw_data", {})
        source = raw_finding.get("source", "unknown")

        kb_entry = None
        if f_type in ["port", "service"]:
            service_name = raw_data.get("service", "")
            kb_entry = self.loader.get_service(service_name)
        elif f_type == "technology":
            tech_name = raw_data.get("title", "") # fallback or actual detection
            kb_entry = self.loader.get_technology(tech_name)
        elif f_type == "vulnerability":
            vuln_name = raw_data.get("info", {}).get("name", "")
            kb_entry = self.loader.get_vulnerability(vuln_name)
        
        if kb_entry is None:
            kb_entry = {}

        reasoning_res = reasoning_engine.calculate_risk(f_type, raw_data, kb_entry)
        confidence_res = confidence_engine.calculate_confidence(source, raw_data, kb_entry)

        risk_level = reasoning_res.risk_level
        
        if risk_level in ["critical", "high"]:
            biz_impact = "Significant business risk"
        elif risk_level == "medium":
            biz_impact = "Moderate business risk"
        else:
            biz_impact = "Minimal business risk"

        audience_data = kb_entry.get("audience_guidance", {})
        guidance = {audience: audience_data.get(audience, "")} if audience_data else {}

        return {
            "scan_id": scan_id,
            "type": f_type,
            "title": title,
            "raw_data": raw_data,
            "severity": risk_level,
            "confidence": confidence_res.final_confidence,
            "risk_score": reasoning_res.total_score,
            "technical_impact": kb_entry.get("description", "Unknown"),
            "business_impact": biz_impact,
            "audience_guidance": guidance,
            "recommended_actions": kb_entry.get("recommended_actions", []),
            "learning_resources": kb_entry.get("learning_resources", []),
            "reasoning_breakdown": reasoning_res.reasoning_breakdown,
            "attack_patterns": kb_entry.get("attack_patterns", []),
            "related_findings": kb_entry.get("related_findings", []),
            "correlation_modifier": 0.0,
            "final_risk_score": reasoning_res.total_score
        }
