# Tiny CRM

![Tiny CRM](https://img.shields.io/badge/Vue.js-3.0-4FC08D?style=flat-square&logo=vue.js)
![Vite](https://img.shields.io/badge/Vite-5.0-646CFF?style=flat-square&logo=vite)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=flat-square&logo=typescript)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC?style=flat-square&logo=tailwind-css)
![Pinia](https://img.shields.io/badge/Pinia-2.1-FFDE59?style=flat-square)

Tiny CRM is a lightweight, frontend-first Customer Relationship Management application designed for simplicity, speed, and intelligence. Built with Vue 3, Vite, and Tailwind CSS, it offers a modern and responsive user interface to manage your sales pipeline effectively. 

A standout feature of Tiny CRM is its **AI-powered Insights** integration, leveraging the Google Gemini API to analyze sales data and provide actionable suggestions, risk assessments, and coaching.

## ✨ Features

- **📊 Comprehensive Dashboard:** Get a bird's-eye view of your business with metrics like Total Revenue, Active Leads, Contacts, and Conversion Rates. Includes Revenue Charts and Pipeline Overviews.
- **🤝 Contact & Lead Management:** Keep track of your contacts and active leads with detailed views and easy sorting.
- **💼 Deal Tracking:** Manage your deals across different stages (Discovery, Proposal, Negotiation, Closed Won, Closed Lost) and track potential revenue.
- **👥 Seller Performance:** Monitor seller performance and conversion rates.
- **🤖 Dedicated AI Panel (Gemini API):** Get live, context-aware artificial intelligence insights on your entities. Generate actionable risk analysis, sales coaching, and confidence-scored suggestions directly from your data.
- **⚡ Blazing Fast:** Powered by Vite and Vue 3 Composition API for an incredibly snappy user experience.
- **🎨 Modern UI:** A clean, responsive, and beautiful interface styled with Tailwind CSS.

## 🚀 Tech Stack

- **Framework:** [Vue 3](https://vuejs.org/) (Composition API & `<script setup>`)
- **Build Tool:** [Vite](https://vitejs.dev/)
- **Language:** [TypeScript](https://www.typescriptlang.org/)
- **Styling:** [Tailwind CSS](https://tailwindcss.com/)
- **State Management:** [Pinia](https://pinia.vuejs.org/)
- **Routing:** [Vue Router](https://router.vuejs.org/)
- **AI Integration:** [Google Gemini API](https://ai.google.dev/)

## 📦 Getting Started

### Prerequisites

Ensure you have [Node.js](https://nodejs.org/) (version 18+ recommended) and `npm` (or `yarn`/`pnpm`) installed.

### Installation

1. Clone the repository (if applicable) or download the source code:
   ```bash
   git clone <repository-url>
   cd tinycrm-main
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Set up your AI API Key:
   To use the live AI integration, ensure you have a valid Google Gemini API key and configure it within the app's AI panel or environment variables as required. (The app also includes simulated mock AI responses for testing).

### Development

Start the Vite development server with Hot Module Replacement (HMR):

```bash
npm run dev
```

The application will be available at `http://localhost:5173`.

### Building for Production

To create an optimized production build:

```bash
npm run build
```

You can then preview the production build locally:

```bash
npm run preview
```

## 📂 Project Structure

```text
src/
├── components/       # Reusable UI components (ai, dashboard, layout, etc.)
├── composables/      # Vue composables for shared logic
├── data/             # Mock data for demonstration purposes
├── router/           # Vue Router configuration
├── services/         # API and external service integrations (e.g., ai.ts for Gemini API)
├── stores/           # Pinia state management stores (contacts, deals, leads, sellers)
├── types/            # TypeScript type definitions
├── views/            # Route-level components (DashboardView, ContactsView, etc.)
├── App.vue           # Root application component
└── main.ts           # Application entry point
```

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page if you want to contribute.

## 📝 License

This project is open-source and available under the [MIT License](LICENSE).
