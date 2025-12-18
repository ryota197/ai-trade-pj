import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

type ModuleStatus = "active" | "coming-soon" | "disabled";

interface ModuleCardProps {
  title: string;
  description: string;
  status?: ModuleStatus;
  href?: string;
}

const statusLabels: Record<ModuleStatus, string> = {
  active: "Active",
  "coming-soon": "Coming Soon",
  disabled: "Disabled",
};

const statusVariants: Record<
  ModuleStatus,
  "default" | "secondary" | "outline"
> = {
  active: "default",
  "coming-soon": "secondary",
  disabled: "outline",
};

/**
 * モジュールカード
 *
 * アプリケーションの各モジュール（Market, Screener, Portfolio等）を表示
 */
export function ModuleCard({
  title,
  description,
  status = "coming-soon",
  href,
}: ModuleCardProps) {
  const Wrapper = href ? "a" : "div";
  const wrapperProps = href
    ? { href, className: "block transition-shadow hover:shadow-md" }
    : {};

  return (
    <Wrapper {...wrapperProps}>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent>
          <Badge variant={statusVariants[status]}>{statusLabels[status]}</Badge>
        </CardContent>
      </Card>
    </Wrapper>
  );
}
