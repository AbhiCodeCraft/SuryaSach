import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Surya Sach | Independent Rooftop Solar Performance Verification",
  description: "Know what your solar system produced — and what it reasonably should have.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
