# HomzDoctor web interface

React + TypeScript patient and clinician interface for the local HomzDoctor API.

## Run locally

Start the API from the repository root first, then:

```powershell
pnpm install --frozen-lockfile
pnpm dev
```

Open `http://localhost:3000`. Vite proxies `/api` requests to `http://localhost:8000`.

With npm, the equivalent commands are `npm ci` and `npm run dev`.

## Verify a production build

```powershell
pnpm run build
```

The UI presents AI results as clinician-reviewed decision support. It does not make autonomous diagnoses or treatment decisions.
