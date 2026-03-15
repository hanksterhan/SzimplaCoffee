# SC-41 Execution Plan: Error Boundaries

## Execution
1. Add `errorComponent` to TanStack Router route definitions
2. Create reusable ErrorFallback component with coffee-themed error message + retry button
3. Add 404 `notFoundComponent` to router config
4. Add global error handler to API client (catch network errors, show user-friendly messages)
