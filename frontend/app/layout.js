import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Providers from "./providers";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "Forma3D | Photo to 3D Assets",
  description:
    "Upload photos and receive clean, design-ready 3D assets for architecture, interiors, and product visualization.",
  openGraph: {
    title: "Forma3D | Photo to 3D Assets",
    description:
      "GPU-accelerated pipeline that turns a handful of photos into downloadable OBJ/GLB/STL assets.",
    url: "https://forma3d.local",
    siteName: "Forma3D",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Forma3D | Photo to 3D Assets",
    description:
      "Fast photo-to-3D conversions for architects, designers, and CGI teams.",
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
