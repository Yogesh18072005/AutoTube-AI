import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AutoTube AI",
  description: "Your bilingual AI YouTube production studio",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
