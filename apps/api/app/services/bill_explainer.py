import json
import uuid
from anthropic import Anthropic
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.models.bill import Bill
from app.models.bill_line_item import BillLineItem

# Initialize the anthropic client
anthropic_client = Anthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None

EXPLANATION_PROMPT_TEMPLATE = """
You are a helpful healthcare billing assistant. A user has a line item on their medical bill.
Description: "{description}"
Amount: ${amount}

Please provide:
1. "explanation": A plain-language explanation of what this charge likely represents.
2. "flagged": A boolean (true/false) indicating whether this looks like a potential overcharge or a highly unusual fee. (Be lenient, only flag if it's typically known as a junk fee or way out of line for standard services).
3. "reasoning": A brief note explaining your reasoning for the flag status.

Respond ONLY with valid JSON in this exact format, with no markdown formatting or other text:
{{"explanation": "...", "flagged": false, "reasoning": "..."}}
"""

def explain_line_item(description: str, amount: float) -> dict:
    """
    Calls Anthropic API to explain a bill line item.
    Returns a dictionary with explanation, flagged, and reasoning.
    """
    if not anthropic_client:
        return {
            "explanation": "AI explanations are disabled (no API key).",
            "flagged": False,
            "reasoning": "Configuration missing."
        }

    prompt = EXPLANATION_PROMPT_TEMPLATE.format(description=description, amount=amount)

    try:
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            temperature=0.0,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        content = response.content[0].text.strip()
        
        # In case the model wrapped it in markdown code blocks, strip them
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
        data = json.loads(content.strip())
        
        return {
            "explanation": data.get("explanation", "No explanation provided."),
            "flagged": bool(data.get("flagged", False)),
            "reasoning": data.get("reasoning", "")
        }
    except Exception as e:
        print(f"Error calling Anthropic API: {e}")
        return {
            "explanation": "Failed to generate explanation due to an error.",
            "flagged": False,
            "reasoning": "Error communicating with AI service or parsing response."
        }

def explain_bill(bill_id: uuid.UUID, db: Session) -> dict:
    """
    Fetches a bill and its line items, explains each, updates DB, and returns summary.
    """
    bill = db.get(Bill, bill_id)
    if not bill:
        raise ValueError("Bill not found")

    stmt = select(BillLineItem).where(BillLineItem.bill_id == bill.id)
    line_items = db.execute(stmt).scalars().all()
    
    total_flagged = 0
    
    for item in line_items:
        result = explain_line_item(item.description, float(item.amount))
        
        item.explanation = result["explanation"]
        item.flagged_overcharge = result["flagged"]
        
        if item.flagged_overcharge:
            total_flagged += 1
            
    db.commit()
    
    # Refresh to get updated data
    db.refresh(bill)
    
    return {
        "bill_id": str(bill.id),
        "total_items": len(line_items),
        "flagged_items": total_flagged,
        "status": "explanations_generated"
    }
