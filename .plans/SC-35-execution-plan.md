# SC-35 Execution Plan: Brew Feedback Form

## Overview
Feedback form linked to purchases for rating coffees and recording espresso outcomes.

## Execution
1. **API:** POST /api/v1/purchases/{id}/feedback, GET /api/v1/purchases/{id}/feedback
2. **Form:** Route /purchases/{id}/feedback — rating slider (1-10), shot_style dropdown, would_reorder toggle, flavor_notes textarea, dial_in_difficulty (1-5)
3. **Integration:** Link from purchase list "Add Feedback" action. Display existing feedback on purchase detail.
4. **Verify:** Submit feedback, check _preference_profile() picks up high-rated merchants.
