"use client";

import { CANSLIMScore, CANSLIMCriteria } from "@/types/stock";

interface CANSLIMScoreCardProps {
  score: CANSLIMScore;
}

function ScoreItem({ criteria, label }: { criteria: CANSLIMCriteria; label: string }) {
  const getScoreColor = (score: number) => {
    if (score >= 15) return "bg-green-500";
    if (score >= 10) return "bg-yellow-500";
    return "bg-red-500";
  };

  return (
    <div className="flex flex-col items-center p-3 bg-gray-50 rounded-lg">
      <span className="text-xs font-medium text-gray-500 mb-1">{label}</span>
      <div
        className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold ${getScoreColor(
          criteria.score
        )}`}
      >
        {criteria.score}
      </div>
      <span className="text-xs text-gray-600 mt-1">{criteria.grade}</span>
    </div>
  );
}

function formatValue(criteria: CANSLIMCriteria): string {
  if (criteria.value === null) return "N/A";

  // L - Leader (RS Rating) は整数表示
  if (criteria.name.includes("Leader")) {
    return criteria.value.toFixed(0);
  }
  // S - Supply and Demand (出来高倍率) は x 付き
  if (criteria.name.includes("Supply")) {
    return `${criteria.value.toFixed(2)}x`;
  }
  // それ以外は % 表示
  return `${criteria.value.toFixed(1)}%`;
}

function formatThreshold(criteria: CANSLIMCriteria): string {
  // L - Leader (RS Rating) は整数表示
  if (criteria.name.includes("Leader")) {
    return `${criteria.threshold.toFixed(0)}`;
  }
  // S - Supply and Demand (出来高倍率) は x 付き
  if (criteria.name.includes("Supply")) {
    return `${criteria.threshold.toFixed(1)}x`;
  }
  // それ以外は % 表示
  return `${criteria.threshold}%`;
}

function CriteriaDetail({ criteria }: { criteria: CANSLIMCriteria }) {
  const isPassing = criteria.score >= 10;

  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${
              isPassing ? "bg-green-500" : "bg-red-500"
            }`}
          />
          <span className="font-medium">{criteria.name}</span>
        </div>
        <p className="text-xs text-gray-500 ml-4">{criteria.description}</p>
      </div>
      <div className="text-right">
        <span className="font-semibold">{formatValue(criteria)}</span>
        <span className="text-xs text-gray-500 ml-1">
          (基準: {formatThreshold(criteria)})
        </span>
      </div>
    </div>
  );
}

export function CANSLIMScoreCard({ score }: CANSLIMScoreCardProps) {
  const getGradeColor = (grade: string) => {
    switch (grade) {
      case "A":
        return "text-green-600 bg-green-100";
      case "B":
        return "text-blue-600 bg-blue-100";
      case "C":
        return "text-yellow-600 bg-yellow-100";
      case "D":
        return "text-orange-600 bg-orange-100";
      default:
        return "text-red-600 bg-red-100";
    }
  };

  const criteria = [
    { key: "c_score", label: "C" },
    { key: "a_score", label: "A" },
    { key: "n_score", label: "N" },
    { key: "s_score", label: "S" },
    { key: "l_score", label: "L" },
    { key: "i_score", label: "I" },
  ] as const;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold mb-4">CAN-SLIM スコア</h2>

      {/* 総合スコア */}
      <div className="flex items-center gap-4 mb-6">
        <div className="text-5xl font-bold">{score.total_score}</div>
        <div>
          <span
            className={`inline-block px-3 py-1 rounded-full text-lg font-semibold ${getGradeColor(
              score.overall_grade
            )}`}
          >
            {score.overall_grade}
          </span>
          <p className="text-sm text-gray-500 mt-1">
            {score.passing_count}/6 項目クリア
          </p>
        </div>
      </div>

      {/* スコアサマリー */}
      <div className="grid grid-cols-6 gap-2 mb-6">
        {criteria.map(({ key, label }) => (
          <ScoreItem key={key} criteria={score[key]} label={label} />
        ))}
      </div>

      {/* 詳細 */}
      <div className="border-t border-gray-200 pt-4">
        <h3 className="text-sm font-medium text-gray-700 mb-3">各項目の詳細</h3>
        <div className="space-y-1">
          {criteria.map(({ key }) => (
            <CriteriaDetail key={key} criteria={score[key]} />
          ))}
        </div>
      </div>
    </div>
  );
}
