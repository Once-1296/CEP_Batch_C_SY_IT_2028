## Plan: ABDM HIU Webhook Flow

TL;DR: Add a dedicated ABDM service layer that owns token caching and Gateway calls, a new router for consent initiation and webhook callbacks, and a small Supabase tracking table so the asynchronous consent/data flow can be correlated safely. Keep decryption as a placeholder helper for now, and update patient rows by `abha_id` once the decrypted FHIR bundle is parsed.

**Steps**
1. Add ABDM configuration and session management. Create a dedicated config/service module for the sandbox base URL, production base URL, client ID/secret, ngrok callback base URL, and a cached bearer token with expiry. Reuse `httpx.AsyncClient` and an `asyncio.Lock` so multiple callback requests do not stampede the session endpoint.
2. Define ABDM Pydantic models in `backend/app/controllers/schema.py`. Add input models for the consent-init route and both webhook payloads; allow extra fields on webhook models so sandbox-only additions do not break validation, while still enforcing the fields the flow depends on, such as `abha_id`, `consent_artifact_id`, consent status, and the encrypted payload envelope.
3. Add a persistence layer for asynchronous correlation. Create or reuse a Supabase table to store the ABHA ID, consent request ID, consent artifact ID, health-data request ID, status, timestamps, and raw payload snapshots. This durable state is what lets the later webhooks find the correct patient row.
4. Implement `/api/abdm/request-consent` and register the router in `main.py`. Validate the incoming `abha_id`, confirm the patient exists, store the tracking row, then call `/v0.5/consent-requests/init` with callback URLs pointing at ngrok. If this route should only be usable by a logged-in pharmacist, extend `app/middleware/auth.py` so `/api/abdm/request-consent` is treated like the existing protected routes.
5. Implement `/api/callbacks/consent-status`. Validate the webhook payload, extract the `consent_artifact_id` and consent status, update the tracking record, and when approval is received, call `/v0.5/health-information/cm/request` using the cached gateway token. Persist the returned request identifier so the next webhook can be correlated.
6. Implement `/api/callbacks/health-data`. Validate the encrypted HIP payload, run it through a placeholder decrypt helper, and keep that helper isolated so ABDM key handling can be added later without changing the route contract.
7. Parse the decrypted FHIR bundle and update Supabase by `abha_id`. Convert the bundle into `medical_history` and `medicines_to_avoid`, then write the update through `supabase_admin` so RLS does not block the webhook path. Keep the mapping logic in a small helper so it can be unit-tested independently.
8. Wire the new module into the app startup path. Add the router include in `main.py`, ensure startup/shutdown handling covers the shared HTTP client if you choose an app-scoped client, and document the sandbox-to-production switches in the config module comments or README.

**Relevant files**
- [backend/main.py] — include the ABDM router and any startup/shutdown hooks.
- [backend/app/controllers/schema.py] — add ABDM request and webhook models.
- [backend/app/config/settings.py] — add ABDM env vars if you keep config centralized here.
- [backend/app/config/supabase.py] — reuse existing client accessors for tracking writes and patient updates.
- [backend/app/middleware/auth.py] — optionally protect the consent-init route.
- [backend/app/middleware/error_handler.py] and [backend/app/middleware/logging.py] — reuse error and request-id behavior for the webhook flow.
- [backend/app/routes/patients.py] and [backend/app/controllers/patient_controller.py] — reference patterns for route/controller separation and Supabase updates.
- [backend/app/routes/safety.py] and [backend/app/controllers/safety_controller.py] — reference the current thin-route style.

**Verification**
1. Run the sandbox end-to-end through ngrok and confirm the three legs work in sequence: consent init, consent-approved callback, and health-data callback.
2. Send malformed callback payloads and confirm validation fails cleanly without touching Supabase.
3. Confirm token caching by observing that repeated Gateway calls reuse the same bearer token until expiry.
4. Verify the Supabase row updates by `abha_id` and that a missing `abha_id` returns a deterministic 400 or 404.
5. Start the app and ensure the existing routes still behave exactly as before after the ABDM router is added.

**Decisions**
- The ABDM code should stay separate from the existing patient and safety logic; that keeps the integration testable and avoids widening the current controllers.
- The webhook chain needs durable correlation state; relying on process memory would be unsafe for ABDM’s asynchronous callbacks.
- The current codebase’s patient-table assumptions do not match the ABHA-centric flow, so the ABDM update path should be keyed by `abha_id` and not by the integer patient IDs used elsewhere.