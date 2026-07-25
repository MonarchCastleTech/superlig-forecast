import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { AppLoader } from "./app-loader";
import "../app/globals.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <AppLoader />
  </StrictMode>,
);
