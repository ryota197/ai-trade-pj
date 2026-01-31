"""RS Rating計算サービス"""

from decimal import Decimal


class RSRatingCalculator:
    """RS Rating計算サービス

    全銘柄の相対強度からパーセンタイル順位（RS Rating 1-99）を計算する。
    """

    def calculate_ratings(
        self,
        relative_strengths: dict[str, Decimal],
    ) -> dict[str, int]:
        """全銘柄のRS Ratingを計算

        Args:
            relative_strengths: 銘柄ごとの相対強度 {symbol: relative_strength}

        Returns:
            銘柄ごとのRS Rating {symbol: rs_rating} (1-99パーセンタイル)
        """
        if not relative_strengths:
            return {}

        # 相対強度でソート
        sorted_symbols = sorted(
            relative_strengths.keys(),
            key=lambda s: relative_strengths[s],
        )

        total = len(sorted_symbols)
        ratings: dict[str, int] = {}

        for rank, symbol in enumerate(sorted_symbols, start=1):
            # パーセンタイル計算（1-99）
            percentile = int((rank / total) * 98) + 1
            ratings[symbol] = percentile

        return ratings
