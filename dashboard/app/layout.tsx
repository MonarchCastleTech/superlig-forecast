import type { Metadata } from "next";
import { headers } from "next/headers";
import { Geist, Geist_Mono } from "next/font/google";

import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const host = requestHeaders.get("host") ?? "localhost:3000";
  const protocol =
    requestHeaders.get("x-forwarded-proto") ??
    (host.startsWith("localhost") ? "http" : "https");
  const metadataBase = new URL(`${protocol}://${host}`);

  return {
    metadataBase,
    title: "Süper Lig Forecast Lab",
    description:
      "Explore a five-million-season Süper Lig simulation and its twenty-season walk-forward backtest.",
    icons: {
      icon: "/favicon.svg",
      shortcut: "/favicon.svg",
    },
    openGraph: {
      title: "Süper Lig Forecast Lab",
      description:
        "Interactive championship probabilities, fixture forecasts, and twenty-season model validation.",
      images: [{ url: "/og.png", width: 1536, height: 1024 }],
      type: "website",
    },
    twitter: {
      card: "summary_large_image",
      title: "Süper Lig Forecast Lab",
      description:
        "Five million season simulations. Twenty seasons of backtesting.",
      images: ["/og.png"],
    },
  };
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        {children}
      </body>
    </html>
  );
}

