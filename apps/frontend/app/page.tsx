import { RateBoard } from "@/components/RateBoard";
import { TrendChart } from "@/components/TrendChart";

export default function HomePage() {
  return (
    <div className="space-y-8">
      <RateBoard />
      <TrendChart />
    </div>
  );
}
