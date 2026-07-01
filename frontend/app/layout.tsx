import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VoiceShield B2B — Copilote anti-fraude vocale",
  description:
    "Détection de deepfake vocal et de fraude au virement en temps réel pour les PME.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
