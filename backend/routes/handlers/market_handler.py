from ...services import market_service


class MarketHandler:

    @staticmethod
    def get_ticker_data() -> list:
        return market_service.get_ticker_data()

    @staticmethod
    def get_movers() -> dict:
        return market_service.get_market_movers()

    @staticmethod
    def get_news() -> list:
        return market_service.get_market_news()

    @staticmethod
    def get_ipo_calendar() -> list:
        return market_service.get_ipo_calendar()
