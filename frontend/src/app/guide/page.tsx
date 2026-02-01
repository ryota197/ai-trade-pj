import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BookOpen } from "lucide-react";
import { getAllIndicatorGuides, type IndicatorGuide } from "@/lib/indicator-guide";

/**
 * 指標ガイドセクション
 */
function IndicatorSection({ guide }: { guide: IndicatorGuide }) {
  const signalVariant = {
    bullish: "default" as const,
    bearish: "destructive" as const,
    neutral: "secondary" as const,
  };

  return (
    <Card id={guide.id} className="scroll-mt-20">
      <CardHeader>
        <CardTitle className="text-xl">
          {guide.name}
          <span className="text-muted-foreground font-normal ml-2">
            ({guide.nameJa})
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* 概要 */}
        <div>
          <h4 className="text-sm font-semibold text-muted-foreground mb-2">概要</h4>
          <p className="text-sm leading-relaxed">{guide.description}</p>
        </div>

        {/* 計算ロジック */}
        <div>
          <h4 className="text-sm font-semibold text-muted-foreground mb-2">
            計算ロジック
          </h4>
          <pre className="text-sm bg-muted p-3 rounded-lg whitespace-pre-wrap font-mono">
            {guide.calculation}
          </pre>
        </div>

        {/* 閾値・見方 */}
        <div>
          <h4 className="text-sm font-semibold text-muted-foreground mb-2">
            閾値と見方
          </h4>
          <div className="border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted">
                <tr>
                  <th className="text-left px-4 py-2 font-medium">範囲</th>
                  <th className="text-left px-4 py-2 font-medium">判定</th>
                  <th className="text-left px-4 py-2 font-medium">シグナル</th>
                </tr>
              </thead>
              <tbody>
                {guide.thresholds.map((threshold, index) => (
                  <tr key={index} className="border-t">
                    <td className="px-4 py-2 font-mono">{threshold.range}</td>
                    <td className="px-4 py-2">{threshold.label}</td>
                    <td className="px-4 py-2">
                      <Badge variant={signalVariant[threshold.signal]}>
                        {threshold.signal === "bullish"
                          ? "強気"
                          : threshold.signal === "bearish"
                            ? "弱気"
                            : "中立"}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* 使い方 */}
        <div>
          <h4 className="text-sm font-semibold text-muted-foreground mb-2">
            使い方
          </h4>
          <p className="text-sm leading-relaxed">{guide.usage}</p>
        </div>

        {/* 注意事項 */}
        {guide.note && (
          <div className="p-3 bg-yellow-50 dark:bg-yellow-950/20 border border-yellow-200 dark:border-yellow-900 rounded-lg">
            <p className="text-sm text-yellow-800 dark:text-yellow-200">
              <strong>Note:</strong> {guide.note}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * ガイドページ
 *
 * マーケット指標の詳細な解説を表示
 */
export default function GuidePage() {
  const guides = getAllIndicatorGuides();

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="mx-auto max-w-4xl px-4 py-8">
        {/* ページヘッダー */}
        <div className="mb-8">
          <div className="flex items-center gap-3">
            <BookOpen className="h-6 w-6 text-primary" />
            <div>
              <h1 className="text-2xl font-bold text-foreground">
                指標ガイド
              </h1>
              <p className="text-sm text-muted-foreground mt-1">
                マーケット指標の見方と計算ロジック
              </p>
            </div>
          </div>
        </div>

        {/* 目次 */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="text-lg">目次</CardTitle>
          </CardHeader>
          <CardContent>
            <nav className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground mb-3">
                マーケット指標
              </p>
              <ul className="grid gap-2 md:grid-cols-2">
                {guides.map((guide) => (
                  <li key={guide.id}>
                    <a
                      href={`#${guide.id}`}
                      className="text-sm text-primary hover:underline"
                    >
                      {guide.name} ({guide.nameJa})
                    </a>
                  </li>
                ))}
              </ul>
            </nav>
          </CardContent>
        </Card>

        {/* マーケット指標セクション */}
        <section>
          <h2 className="text-lg font-semibold mb-4">マーケット指標</h2>
          <div className="space-y-6">
            {guides.map((guide) => (
              <IndicatorSection key={guide.id} guide={guide} />
            ))}
          </div>
        </section>

        {/* Market Condition判定 */}
        <section className="mt-12">
          <h2 className="text-lg font-semibold mb-4">Market Condition判定</h2>
          <Card>
            <CardHeader>
              <CardTitle className="text-xl">
                総合判定ロジック
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h4 className="text-sm font-semibold text-muted-foreground mb-2">
                  概要
                </h4>
                <p className="text-sm leading-relaxed">
                  本アプリでは、複数の指標を組み合わせてマーケット全体の状態を
                  「Risk On」「Neutral」「Risk Off」の3段階で判定します。
                  スコアは -5 から +5 の範囲で表示され、プラスが強気、マイナスが弱気を示します。
                </p>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-muted-foreground mb-2">
                  判定ロジック
                </h4>
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-muted">
                      <tr>
                        <th className="text-left px-4 py-2 font-medium">指標</th>
                        <th className="text-left px-4 py-2 font-medium">強気条件</th>
                        <th className="text-left px-4 py-2 font-medium">弱気条件</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-t">
                        <td className="px-4 py-2 font-medium">VIX</td>
                        <td className="px-4 py-2">&lt; 20</td>
                        <td className="px-4 py-2">&gt; 25</td>
                      </tr>
                      <tr className="border-t">
                        <td className="px-4 py-2 font-medium">RSI</td>
                        <td className="px-4 py-2">30 - 70</td>
                        <td className="px-4 py-2">&lt; 30 or &gt; 70</td>
                      </tr>
                      <tr className="border-t">
                        <td className="px-4 py-2 font-medium">200MA</td>
                        <td className="px-4 py-2">価格 &gt; 200MA</td>
                        <td className="px-4 py-2">価格 &lt; 200MA</td>
                      </tr>
                      <tr className="border-t">
                        <td className="px-4 py-2 font-medium">Put/Call</td>
                        <td className="px-4 py-2">&lt; 1.0</td>
                        <td className="px-4 py-2">&gt; 1.0</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-muted-foreground mb-2">
                  総合判定
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-3">
                    <Badge>Risk On</Badge>
                    <span>スコア +2 以上: 積極的に買いを検討可能</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant="secondary">Neutral</Badge>
                    <span>スコア -1 〜 +1: 様子見、慎重に</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant="destructive">Risk Off</Badge>
                    <span>スコア -2 以下: 新規買いを控える</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* 参考情報 */}
        <section className="mt-12">
          <h2 className="text-lg font-semibold mb-4">参考情報</h2>
          <Card>
            <CardContent className="pt-6">
              <ul className="space-y-2 text-sm">
                <li>
                  <strong>CAN-SLIM手法:</strong>{" "}
                  ウィリアム・オニールが開発した成長株投資手法。
                  Market Direction（M）は7つの基準の1つ。
                </li>
                <li>
                  <strong>データソース:</strong>{" "}
                  VIX、S&P500、RSIはyfinance経由で取得。
                  Put/Call Ratioは現在固定値を使用。
                </li>
                <li>
                  <strong>更新タイミング:</strong>{" "}
                  管理画面から手動更新、またはスケジュール実行（予定）。
                </li>
              </ul>
            </CardContent>
          </Card>
        </section>
      </main>
    </div>
  );
}
