# Product Processing App

A Next.js application with Python API functions for processing product images and descriptions using Google Gemini AI.

## Features

- Upload product images with drag & drop
- AI-powered description rewriting using Google Gemini
- EXIF metadata injection (iPhone-style GPS and camera data)
- ZIP file generation with processed images and descriptions
- Team member authentication
- Modern, responsive UI

## Setup

1. **Copy environment file:**
   ```bash
   cp env_example.txt .env
   ```

2. **Add your API key:**
   Edit `.env` and add your `GEMINI_API_KEY` from [Google AI Studio](https://makersuite.google.com/app/apikey)

3. **Install dependencies:**
   ```bash
   npm install
   ```

## Local Development

### Option 1: Run Both Servers (Recommended)

```bash
npm run dev:full
```

This starts:
- Next.js dev server on http://localhost:3000
- Python API server on http://localhost:5001

### Option 2: Run Separately

**Terminal 1 - Next.js:**
```bash
npm run dev
```

**Terminal 2 - Python API:**
```bash
npm run dev:api
```

### Option 3: Use Vercel CLI (Matches Production)

```bash
# Install Vercel CLI
npm i -g vercel

# Run in dev mode (simulates serverless functions)
vercel dev
```

## Deployment to Vercel

1. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Deploy:**
   ```bash
   vercel --prod
   ```

3. **Set environment variables in Vercel dashboard:**
   - `GEMINI_API_KEY` - Your Google Gemini API key

## Project Structure

```
├── api/                    # Vercel serverless functions
│   ├── process_product.py  # Main product processing
│   ├── health.py          # Health check endpoint
│   ├── login_tracking.py  # Login tracking
│   └── server.py          # Local dev server (not used on Vercel)
├── src/                    # Next.js application
│   ├── app/               # App router pages
│   ├── components/        # React components
│   └── lib/               # Utility libraries
├── public/                # Static assets
└── vercel.json           # Vercel configuration
```

## API Endpoints

- `POST /api/process_product` - Process product images and text
- `GET /api/health` - Health check
- `POST /api/login_tracking` - Track user logins

## Technology Stack

- **Frontend:** Next.js 14, React, TypeScript, Tailwind CSS
- **Backend:** Python serverless functions (Vercel)
- **AI:** Google Gemini 2.0 Flash
- **Image Processing:** PIL/Pillow, piexif

## Notes

- **Local Development:** Uses `api/server.py` to run Python functions locally
- **Vercel Production:** Serverless functions run directly (no server.py needed)
- **Configuration:** `next.config.js` automatically detects environment and routes accordingly

## License

Private project
