"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  TrendingUp,
  Calendar,
  Target,
  BarChart3,
  Award,
  Building2,
  CheckCircle,
  XCircle,
} from "lucide-react";
import type { CANSLIMScore, CANSLIMCriteria } from "@/types/stock";

interface CANSLIMScoreCardProps {
  score: CANSLIMScore | null;
  isLoading?: boolean;
}

interface CriteriaRowProps {
  criteria: CANSLIMCriteria;
  icon: React.ReactNode;
  label: string;
}

function getGradeColor(grade: string): string {
  switch (grade) {
    case "A":
      return "text-green-600";
    case "B":
      return "text-blue-600";
    case "C":
      return "text-yellow-600";
    case "D":
      return "text-orange-600";
    case "F":
      return "text-red-600";
    default:
      return "text-muted-foreground";
  }
}

function getGradeBadgeVariant(grade: string): "default" | "secondary" | "destructive" | "outline" {
  switch (grade) {
    case "A":
      return "default";
    case "B":
      return "secondary";
    case "C":
    case "D":
      return "outline";
    case "F":
      return "destructive";
    default:
      return "outline";
  }
}

function CriteriaRow({ criteria, icon, label }: CriteriaRowProps) {
  const isPassing = criteria.score >= 70;

  return (
    <div className="flex items-center justify-between py-3 border-b border-border last:border-0">
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-muted">
          {icon}
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-medium">{label}</span>
            {isPassing ? (
              <CheckCircle className="h-4 w-4 text-green-600" />
            ) : (
              <XCircle className="h-4 w-4 text-red-600" />
            )}
          </div>
          <p className="text-xs text-muted-foreground">{criteria.description}</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <div className="text-right">
          <div className="font-mono text-sm">
            {criteria.value !== null ? criteria.value.toFixed(1) : "-"}
          </div>
          <div className="text-xs text-muted-foreground">
            基準: {criteria.threshold}
          </div>
        </div>
        <Badge
          variant={getGradeBadgeVariant(criteria.grade)}
          className={`w-8 justify-center ${getGradeColor(criteria.grade)}`}
        >
          {criteria.grade}
        </Badge>
      </div>
    </div>
  );
}

/**
 * CAN-SLIMスコアカード
 *
 * CAN-SLIM基準ごとのスコアと総合評価を表示
 */
export function CANSLIMScoreCard({ score, isLoading = false }: CANSLIMScoreCardProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader className="border-b">
          <CardTitle>CAN-SLIMスコア</CardTitle>
        </CardHeader>
        <CardContent className="py-16">
          <div className="flex flex-col items-center justify-center text-muted-foreground">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-4" />
            <p>スコアを計算中...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!score) {
    return (
      <Card>
        <CardHeader className="border-b">
          <CardTitle>CAN-SLIMスコア</CardTitle>
        </CardHeader>
        <CardContent className="py-16">
          <div className="flex flex-col items-center justify-center text-muted-foreground">
            <Award className="h-12 w-12 mb-4 opacity-50" />
            <p className="text-lg font-medium">スコアデータがありません</p>
            <p className="text-sm mt-1">
              この銘柄のCAN-SLIMスコアは計算されていません
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="border-b">
        <div className="flex items-center justify-between">
          <CardTitle>CAN-SLIMスコア</CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline">{score.passing_count}/6 合格</Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-4">
        {/* 総合スコア */}
        <div className="flex items-center justify-center gap-6 mb-6 py-4 bg-muted/50 rounded-lg">
          <div className="text-center">
            <div className="text-5xl font-bold font-mono">{score.total_score}</div>
            <div className="text-sm text-muted-foreground">総合スコア</div>
          </div>
          <div className="text-center">
            <div
              className={`text-5xl font-bold ${getGradeColor(score.overall_grade)}`}
            >
              {score.overall_grade}
            </div>
            <div className="text-sm text-muted-foreground">総合グレード</div>
          </div>
        </div>

        {/* 各基準のスコア */}
        <div className="space-y-1">
          <CriteriaRow
            criteria={score.c_score}
            icon={<TrendingUp className="h-4 w-4" />}
            label="C - 四半期EPS成長率"
          />
          <CriteriaRow
            criteria={score.a_score}
            icon={<Calendar className="h-4 w-4" />}
            label="A - 年間EPS成長率"
          />
          <CriteriaRow
            criteria={score.n_score}
            icon={<Target className="h-4 w-4" />}
            label="N - 新高値"
          />
          <CriteriaRow
            criteria={score.s_score}
            icon={<BarChart3 className="h-4 w-4" />}
            label="S - 需給（出来高）"
          />
          <CriteriaRow
            criteria={score.l_score}
            icon={<Award className="h-4 w-4" />}
            label="L - リーダー銘柄"
          />
          <CriteriaRow
            criteria={score.i_score}
            icon={<Building2 className="h-4 w-4" />}
            label="I - 機関投資家"
          />
        </div>
      </CardContent>
    </Card>
  );
}
