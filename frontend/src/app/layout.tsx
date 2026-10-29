import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "FieldWeaver | Swarm mission simulation",
    template: "%s | FieldWeaver",
  },
  description: "Compile, review, and evaluate seeded multi-robot source-localization simulations.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
