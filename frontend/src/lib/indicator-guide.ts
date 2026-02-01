/**
 * 指標ガイドデータ
 *
 * 各指標の概要、見方、計算ロジック、閾値を定義
 */

export type IndicatorId = "vix" | "rsi" | "ma200" | "put_call_ratio";

export interface IndicatorThreshold {
  range: string;
  label: string;
  signal: "bullish" | "bearish" | "neutral";
}

export interface IndicatorGuide {
  id: IndicatorId;
  name: string;
  nameJa: string;
  summary: string;
  description: string;
  calculation: string;
  thresholds: IndicatorThreshold[];
  usage: string;
  note?: string;
}

export const INDICATOR_GUIDES: Record<IndicatorId, IndicatorGuide> = {
  vix: {
    id: "vix",
    name: "VIX",
    nameJa: "恐怖指数",
    summary: "S&P500オプション価格から算出される市場の不安度を示す指標",
    description:
      "VIX（Volatility Index）は、シカゴ・オプション取引所（CBOE）が算出する「恐怖指数」です。S&P500のオプション価格から今後30日間の予想変動率（インプライド・ボラティリティ）を算出します。市場参加者の不安が高まるとVIXは上昇し、楽観的になると低下します。",
    calculation:
      "S&P500オプション（複数の行使価格・満期）のインプライド・ボラティリティを加重平均して算出。詳細な計算式はCBOEが公開しています。",
    thresholds: [
      { range: "< 15", label: "低い（楽観）", signal: "bearish" },
      { range: "15 - 20", label: "通常", signal: "neutral" },
      { range: "20 - 30", label: "やや高い（警戒）", signal: "neutral" },
      { range: "> 30", label: "高い（パニック）", signal: "bullish" },
    ],
    usage:
      "逆張り指標として使われることが多い。VIXが極端に低い時は市場が油断しており天井に注意。逆に極端に高い時はパニック売りの後で買い場となることも。",
    note: "VIXが低い = 安全ではなく、むしろ警戒が必要な場合があります。",
  },

  rsi: {
    id: "rsi",
    name: "RSI",
    nameJa: "相対力指数",
    summary: "直近の値動きから買われすぎ・売られすぎを判断する指標",
    description:
      "RSI（Relative Strength Index）は、一定期間の値上がり幅と値下がり幅の比率から、相場の過熱感を測る指標です。0〜100の範囲で表示され、一般的に70以上で「買われすぎ」、30以下で「売られすぎ」と判断します。",
    calculation:
      "RSI = 100 - (100 / (1 + RS))\nRS = 期間内の平均上昇幅 / 期間内の平均下落幅\n\n本アプリでは14日RSIを使用しています。",
    thresholds: [
      { range: "> 70", label: "買われすぎ", signal: "bearish" },
      { range: "50 - 70", label: "やや強い", signal: "neutral" },
      { range: "30 - 50", label: "やや弱い", signal: "neutral" },
      { range: "< 30", label: "売られすぎ", signal: "bullish" },
    ],
    usage:
      "トレンド相場では70-80でも上昇が続くことがあるため、RSI単体での判断は避け、他の指標と組み合わせて使用します。",
    note: "強い上昇トレンド中はRSIが70以上で張り付くこともあります。",
  },

  ma200: {
    id: "ma200",
    name: "200-Day Moving Average",
    nameJa: "200日移動平均線",
    summary: "過去200営業日の終値平均。長期トレンドの判断に使用",
    description:
      "200日移動平均線は、過去200営業日（約10ヶ月）の終値を平均した値です。長期的なトレンドの方向性を示し、機関投資家も重視する重要な指標です。価格が200MAより上にあれば上昇トレンド、下にあれば下降トレンドと判断します。",
    calculation:
      "200MA = 過去200日間の終値の合計 / 200\n\n本アプリではS&P500の200日移動平均を表示しています。",
    thresholds: [
      { range: "価格 > 200MA", label: "上昇トレンド", signal: "bullish" },
      { range: "価格 < 200MA", label: "下降トレンド", signal: "bearish" },
    ],
    usage:
      "CAN-SLIM手法では、S&P500が200MAを上回っている時のみ積極的に買いを検討します。200MAを下回っている場合は、新規の買いを控え、既存ポジションの利確・損切りを検討します。",
    note: "200MAのゴールデンクロス（価格が下から上に抜ける）は買いシグナル、デッドクロス（上から下に抜ける）は売りシグナルとされます。",
  },

  put_call_ratio: {
    id: "put_call_ratio",
    name: "Put/Call Ratio",
    nameJa: "プット・コール・レシオ",
    summary: "プットオプションとコールオプションの出来高比率",
    description:
      "Put/Call Ratioは、プットオプション（売る権利）とコールオプション（買う権利）の出来高または建玉の比率です。市場参加者がどの程度弱気か強気かを示す指標として使われます。",
    calculation:
      "Put/Call Ratio = プットオプション出来高 / コールオプション出来高\n\n1.0を超えるとプットの方が多い（弱気優勢）、1.0未満だとコールの方が多い（強気優勢）を意味します。",
    thresholds: [
      { range: "> 1.0", label: "弱気優勢", signal: "bullish" },
      { range: "0.7 - 1.0", label: "通常", signal: "neutral" },
      { range: "< 0.7", label: "強気優勢", signal: "bearish" },
    ],
    usage:
      "逆張り指標として使われることが多い。極端に高い値（弱気が多い）は買い場、極端に低い値（強気が多い）は天井のサインとなることがあります。",
    note: "本アプリでは現在固定値（0.85）を使用しています。将来的にはCBOEからリアルタイムデータを取得予定です。",
  },
};

/**
 * 指標IDからガイドを取得
 */
export function getIndicatorGuide(id: IndicatorId): IndicatorGuide {
  return INDICATOR_GUIDES[id];
}

/**
 * 全指標ガイドを取得
 */
export function getAllIndicatorGuides(): IndicatorGuide[] {
  return Object.values(INDICATOR_GUIDES);
}
