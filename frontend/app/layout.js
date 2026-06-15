import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata = {
  title: "ReviewBot",
  description: "AI-powered code review for GitHub pull requests",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={`${inter.variable} min-h-screen bg-slate-50 font-sans text-slate-900 antialiased`}>
        <nav className="sticky top-0 z-10 border-b border-slate-200 bg-white/80 backdrop-blur">
          <div className="mx-auto flex max-w-4xl items-center gap-6 px-8 py-4">
            <a href="/" className="flex items-center gap-2 text-lg font-bold text-slate-900">
              <span className="text-indigo-600">●</span> ReviewBot
            </a>
            <a href="/history" className="text-sm font-medium text-slate-500 hover:text-slate-900">
              History
            </a>
          </div>
        </nav>
        {children}
      </body>
    </html>
  );
}
