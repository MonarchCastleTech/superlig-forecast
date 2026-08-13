import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { MethodologyLoader } from "@/components/methodology-page";
import "../app/globals.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode><MethodologyLoader /></StrictMode>,
);
