import type { Metadata } from "next";
import CalculatorApp from "../CalculatorApp";

export const metadata: Metadata = {
  title: "Browser Calculator",
  description: "Run roadway superelevation calculations and CAD-ready exports privately in your browser.",
};

export default function CalculatorPage() {
  return <CalculatorApp />;
}
