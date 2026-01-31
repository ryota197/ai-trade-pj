import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Search, Eye, Briefcase } from "lucide-react";

const actions = [
  {
    title: "スクリーナー",
    description: "CAN-SLIM条件で銘柄を検索",
    href: "/screener",
    icon: Search,
  },
  {
    title: "ウォッチリスト",
    description: "注目銘柄を管理",
    href: "/portfolio?tab=watchlist",
    icon: Eye,
  },
  {
    title: "ポートフォリオ",
    description: "ペーパートレードを管理",
    href: "/portfolio",
    icon: Briefcase,
  },
];

/**
 * クイックアクションカード
 *
 * スクリーナー、ウォッチリスト、ポートフォリオへのナビゲーション
 */
export function QuickActions() {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {actions.map((action) => (
        <Link key={action.href} href={action.href}>
          <Card className="h-full hover:bg-muted/50 transition-colors cursor-pointer">
            <CardContent className="pt-6">
              <div className="flex items-start gap-4">
                <div className="p-2 rounded-lg bg-primary/10">
                  <action.icon className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold">{action.title}</h3>
                  <p className="text-sm text-muted-foreground mt-1">
                    {action.description}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}
