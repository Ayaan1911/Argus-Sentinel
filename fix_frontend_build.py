import os
import json

# 1. Update package.json
package_json_path = "frontend/package.json"
if os.path.exists(package_json_path):
    with open(package_json_path, 'r') as f:
        pkg = json.load(f)
else:
    pkg = {
        "name": "argus-sentinel-frontend",
        "private": True,
        "version": "1.0.0",
        "type": "module",
        "scripts": {
            "dev": "vite",
            "build": "vite build",
            "lint": "eslint . --ext js,jsx --report-unused-disable-directives --max-warnings 0",
            "preview": "vite preview"
        }
    }

pkg["dependencies"] = {
    "axios": "^1.6.0",
    "lucide-react": "^0.383.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "react-router-dom": "^6.0.0"
}
pkg["devDependencies"] = {
    "@vitejs/plugin-react": "^4.0.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "vite": "^5.0.0"
}

with open(package_json_path, 'w') as f:
    json.dump(pkg, f, indent=2)

# 2. Create postcss.config.js
postcss_content = """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
"""
with open("frontend/postcss.config.js", "w") as f:
    f.write(postcss_content)

# 3. Create tailwind.config.js
# We merge user's requested colors with our previously used ones to avoid breaking UI.
tailwind_content = """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'argus-bg': '#0a0f1a',
        'argus-surface': '#111827',
        'argus-card': '#1a2235',
        'argus-border': '#1e2d40',
        'argus-accent': '#00d4ff',
        'argus-danger': '#ff4444',
        'argus-warning': '#ffaa00',
        'argus-success': '#00ff88',
        background: "#0a0f1a",
        surface: "#111827",
        card: "#1a2235",
        bordercolor: "#1e2d40",
        accent: "#00d4ff",
        danger: "#ff4444",
        warning: "#ffaa00",
        success: "#00ff88",
        textpri: "#e2e8f0",
        textmut: "#64748b",
      }
    },
  },
  plugins: [],
}
"""
with open("frontend/tailwind.config.js", "w") as f:
    f.write(tailwind_content)

# 4. Fix vite.config.js
vite_content = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
  },
})
"""
with open("frontend/vite.config.js", "w") as f:
    f.write(vite_content)

# 5. Fix index.css (just making sure it has the right directives)
index_css_path = "frontend/src/index.css"
if os.path.exists(index_css_path):
    with open(index_css_path, "r") as f:
        css = f.read()
    if "@tailwind base;" not in css:
        css = "@tailwind base;\\n@tailwind components;\\n@tailwind utilities;\\n" + css
        with open(index_css_path, "w") as f:
            f.write(css)

# 6. Fix Dockerfile
dockerfile_content = """FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"]
"""
with open("frontend/Dockerfile", "w") as f:
    f.write(dockerfile_content)

print("Frontend configuration fixed.")
