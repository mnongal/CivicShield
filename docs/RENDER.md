# Deploy CivicShield on Render Free

The service runs the frontend and FastAPI together. No separate static site, paid disk, AI account or managed database is required.

1. Put the contents of this project folder at the root of your GitHub repository. Do not upload `.env`, `.venv`, local databases or logs.
2. In Render, choose New > Blueprint and connect that repository. Render reads `render.yaml`. Review the single **Free** web service before deployment.
3. Alternatively choose New > Web Service: Python 3, Free instance, build `pip install -r requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, health path `/api/health`. Set `PYTHON_VERSION=3.12.10` and `DATABASE_URL=sqlite:////tmp/civicshield.db`.
4. If you upload the surrounding workspace rather than this folder, set Root Directory to the actual folder containing `requirements.txt` and `app/`.
5. After deployment, check `/api/health`, run the fictional homepage demo, open the Fair Fares PDF, test optional AI intake suggestions if configured and download a plan and calendar reminder. Test the HTTPS URL on an actual phone and add it to the home screen.

Render's automatically supplied `RENDER_EXTERNAL_HOSTNAME` is allowed by the backend. For a custom domain, add its exact hostname to `ALLOWED_HOSTS` (comma-separated, no scheme).

## Free-plan behavior

The service sleeps after 15 minutes without traffic; waking takes about a minute. Render allows 750 free instance hours per workspace per month. Bandwidth and build limits also apply; review billing settings and spend limits if a payment method is attached.

Local files disappear when the service restarts, redeploys or sleeps. This app safely recreates its public catalog from `data/programs.json`; user plans remain in the browser and must be downloaded before leaving. Do not add persistent user records to SQLite on this plan. No free Postgres service is configured because it expires after 30 days.

For optional AI intake, set GROQ_API_KEY privately in Render Environment and GROQ_MODEL=openai/gpt-oss-120b. Notice processing and translation are removed. Free hosting is suitable for this portfolio demo, not a guarantee of availability for time-critical benefits support.

Official references: https://render.com/docs/deploy-fastapi and https://render.com/docs/free
