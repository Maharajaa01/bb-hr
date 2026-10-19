# BB HR — implementation checklist

Target site: `bbacademy-erp.dreamtechsolution.com` (Frappe 15.113.4, ERPNext 15.115.0, HRMS 15.63.3).
App: `bb_academy_hrms`. PWA served at `/bbhr`.

## Inspection findings (2026-10-16)
- Payroll Settings → `payroll_based_on = Attendance`: check-ins must produce submitted `Attendance`.
- 38 active employees; only `HR-EMP-00001` (test.staff@example.com) is linked to a User.
- No `reports_to` hierarchy yet; only Administrator holds HR roles.
- Shift Types are split sessions (several IN/OUT pairs per day); auto-attendance is off.
- 4 Holiday Lists (company default `BB Academy 2026`); 4 active employees have none (company default applies).
- 2 submitted Salary Slips (HR-EMP-00001, Jul + Aug 2026). wkhtmltopdf 0.12.6 present.
- Employee Checkin already has `latitude`/`longitude`/`geolocation`; HR Settings geolocation tracking off.
- Sibling app `kakachi_mobile` provides the house conventions reused here
  (www page with CSRF injection, root-scoped service worker, never-cache-/api rule).

## Progress
- [x] Project inspection
- [x] Vue foundation and design system
- [x] Authentication and permissions
- [x] Employee dashboard
- [x] Geo-fenced check-in/check-out
- [x] Attendance directory
- [x] Salary slips
- [x] Holiday calendar
- [x] Reporting Manager dashboard
- [x] HR administrator dashboard
- [x] PWA configuration
- [x] Tests and bug fixes
- [x] Deployment documentation

## Verification (2026-10-16)
- Backend: `bench execute bb_academy_hrms.tests.integration.run` → 15 passed, 0 failed (rolled back; DB verified clean).
- Frontend: `vue-tsc` clean; `vitest` 16/16; `vite build` OK; ruff check clean.
- Real browser (headless Chromium via nginx, live data, temporary sessions deleted afterwards): every screen at
  390 px and 1366 px, no console errors, no failed API calls, no horizontal overflow; full check-in flow with GPS +
  fake camera (punch intercepted, not saved); SW scope `/bbhr/`, cache contains only the 55 static build files.
- HTTP: guests get 403 on data endpoints; employee gets 403 on team/HR/others' salary; POST without CSRF → 400;
  payslip PDF 200 `application/pdf` with `Cache-Control: private, no-store`.

## Remaining manual setup (data, not code)
- Add Office Location(s) in BB HR Settings — check-in is refused until then.
- Link Users to the 37 unlinked active Employees; set Reports To; assign HR roles.
- Not tested: a real phone on the real campus (needs real coordinates + a linked staff login).
