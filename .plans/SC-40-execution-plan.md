# SC-40 Execution Plan: Responsive Mobile Layout

## Execution
1. Sidebar: Use shadcn Sheet component for mobile nav, triggered by hamburger button. Hide sidebar at `md:` breakpoint.
2. Dashboard: Change grid to `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`
3. Recommendations: Stack form above results on mobile (remove side-by-side grid)
4. Merchants: Card layout on mobile, table on desktop using responsive utility
5. Test all pages at 375px, 768px, 1024px widths
