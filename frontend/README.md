# CloudWise AI - Cloud Cost Optimization Platform

CloudWise AI is a premium enterprise-grade SaaS application designed for Cloud Cost Optimization. It integrates state-of-the-art technologies including React Three Fiber (R3F) for interactive 3D elements, glassmorphism UI, and a powerful FinOps analytics dashboard.

## 🌟 Features

- **Premium Homepage**: Custom liquid-glass styling, full-screen background animations, and an interactive 3D Cloud Infrastructure scene.
- **Lightweight Internal 3D**: Optimized procedural 3D geometries (Data Cubes, Network Graphs, HoloSpheres) embedded in internal pages to maintain the premium aesthetic without performance overhead.
- **Analytics Dashboard**: Extensive cost tracking, resource management, and AI insights utilizing Recharts.
- **Lazy Loaded Routes**: Complete code-splitting architecture using `React.lazy` and `Suspense` for blazing fast load times.

## 🛠 Tech Stack

### Frontend
- **React 19**
- **TypeScript**
- **Vite**
- **Tailwind CSS v4**
- **React Three Fiber / Drei / Three.js**
- **Zustand** (State Management)
- **Framer Motion** (Animations)
- **Recharts** (Data Visualization)
- **React Router v7**

### Backend
- **FastAPI** (Python)
- **SQLAlchemy**
- **Celery**
- **PyTorch & Transformers** (AI/ML)
- **Redis**

## 🚀 Getting Started

### Prerequisites
- Node.js (v18 or higher)
- npm or yarn
- Python 3.9+ (for Backend)
- Docker & Docker Compose (Optional, but recommended)

### Local Development Setup

#### 1. Frontend
```bash
cd frontend
npm install
npm run dev
```
The application will be available at `http://localhost:5173`.

#### 2. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## 🏗 Building for Production

To create an optimized production build of the frontend:
```bash
cd frontend
npm run build
```
This generates static files in the `dist/` directory, utilizing aggressive chunk splitting.

## 🎨 Design System & Aesthetics
- **Typography**: Google Inter font used globally for precision.
- **Glassmorphism**: A reusable `.liquid-glass` CSS class providing a frosted glass effect with a subtle border.
- **Performance**: Heavy 3D assets (`GlobalCanvas.tsx`) are strictly isolated to the Landing page. Internal dashboards use primitive geometries to ensure 60FPS scrolling and interaction.
