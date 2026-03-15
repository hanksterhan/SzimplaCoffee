# SC-36 Execution Plan: Purchase History Viewer

## Overview
Browse, edit, delete purchases. Summary stats at top.

## Execution
1. **API:** PUT /api/v1/purchases/{id}, DELETE /api/v1/purchases/{id}
2. **List page:** Route /purchases — table with date, merchant, product, price, feedback status
3. **Detail view:** Route /purchases/{id} — full info + feedback display
4. **Edit/Delete:** Edit form (same as create, pre-filled), delete with confirmation dialog
5. **Summary stats:** Total purchases, total spent, bags this month, most-purchased merchant
