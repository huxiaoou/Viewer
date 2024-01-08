import pandas as pd
from tqsdk import TqApi, TqAuth
from husfort.qutility import SFG, SFR
from husfort.qinstruments import CInstrumentInfoTable


class CContract(object):
    def __init__(self, contract: str, instru_info_tab: CInstrumentInfoTable):
        self.__contract: str = contract
        self.__instrument: str = instru_info_tab.parse_instrument_from_contract(contract)
        self.__exchange: str = instru_info_tab.get_exchangeId(self.__instrument)
        self.__contract_multiplier: int = instru_info_tab.get_multiplier(self.__instrument)

    @property
    def contract(self) -> str:
        return self.__contract

    @property
    def multiplier(self) -> int:
        return self.__contract_multiplier

    @property
    def tq_id(self) -> str:
        return f"{self.__exchange}.{self.__contract}"


class CPosition(object):
    def __init__(self, contract: CContract, direction: int, qty: int, cost_price: float, base_price: float):
        self._contract = contract
        self._direction = direction
        self._qty = qty
        self._cost_price: float = cost_price
        self._base_price: float = base_price
        self._last_mkt_prc: float | None = None

    @property
    def contract(self) -> CContract:
        return self._contract

    @property
    def direction(self) -> int:
        return self._direction

    @property
    def qty(self) -> int:
        return self._qty

    @property
    def cost_price(self) -> float:
        return self._cost_price

    @property
    def base_price(self) -> float:
        return self._base_price

    @property
    def last_mkt_prc(self) -> float:
        return self._last_mkt_prc

    @last_mkt_prc.setter
    def last_mkt_prc(self, prc: float):
        self._last_mkt_prc = prc

    @property
    def cost_val(self) -> float:
        return self._cost_price * self._qty * self._contract.multiplier * self._direction

    @property
    def base_val(self) -> float:
        return self._base_price * self._qty * self._contract.multiplier * self._direction

    @property
    def mkt_val(self) -> float:
        return self._last_mkt_prc * self._qty * self._contract.multiplier * self._direction

    @property
    def float_pnl(self) -> float:
        return self.mkt_val - self.cost_val

    @property
    def float_pnl_increment(self) -> float:
        return self.mkt_val - self.base_val


class CManagerViewer(object):
    def __init__(self, position_file_path: str, instru_info_tab: CInstrumentInfoTable):
        print(f"... loading data from {position_file_path}")
        position_df = pd.read_csv(position_file_path)
        self.positions: list[CPosition] = []
        for _, r in position_df.iterrows():
            contract = CContract(contract=getattr(r, "contract"), instru_info_tab=instru_info_tab)
            self.positions.append(CPosition(
                contract=contract,
                direction=getattr(r, "direction"),
                qty=getattr(r, "qty"),
                cost_price=getattr(r, "aver_cost_price"),
                base_price=getattr(r, "last_market_price"),
            ))

    @property
    def positions_size(self) -> int:
        return len(self.positions)

    @staticmethod
    def color_msg(msg: str, val: float):
        return SFR(msg) if val >= 0 else SFG(msg)

    def print_positions(self):
        sep_b = "=" * 102
        sep_s = "-" * 102

        print(sep_b)
        head = (f"{'CONTRACT':>8s}"
                f"{'DIR':>4s}"
                f"{'QTY':>4s}"
                f"{'COST':>10s}"
                f"{'BASE':>10s}"
                f"{'MKT':>10s}"
                f"{'COST-VAL':>12s}"
                f"{'BASE-VAL':>12s}"
                f"{'MKT-VAL':>12s}"
                f"{'FLOAT':>10s}"
                f"{'INCREMENT':>10s}")
        print(head)
        print(sep_s)

        qty, cost_val, base_val, mkt_val, float_pnl, increment = 0, 0.0, 0.0, 0.0, 0.0, 0.0
        for pos in self.positions:
            qty += pos.qty
            cost_val += pos.cost_val
            base_val += pos.base_val
            mkt_val += pos.mkt_val
            float_pnl += pos.float_pnl
            increment += pos.float_pnl_increment
            msg = (f"{pos.contract.contract:>8s}"
                   f"{pos.direction:>4d}"
                   f"{pos.qty:>4d}"
                   f"{pos.cost_price:>10.2f}"
                   f"{pos.base_price:>10.2f}"
                   f"{pos.last_mkt_prc:>10.2f}"
                   f"{pos.cost_val:>12.2f}"
                   f"{pos.base_val:>12.2f}"
                   f"{pos.mkt_val:>12.2f}"
                   f"{pos.float_pnl:>10.2f}"
                   f"{pos.float_pnl_increment:>10.2f}")
            print(self.color_msg(msg, pos.float_pnl_increment))

        print(sep_s)
        msg = (f"{'SUM':>8s}{qty:>8d}"
               f"{cost_val:>42.2f}{base_val:>12.2f}{mkt_val:>12.2f}"
               f"{float_pnl:>10.2f}{increment:>10.2f}")
        print(self.color_msg(msg, increment))
        print(sep_b)
        print("\033[A" * (self.positions_size + 6), end="\r")

    def main(self, tq_account: str, tq_password: str):
        contracts = [pos.contract.tq_id for pos in self.positions]
        api = TqApi(auth=TqAuth(user_name=tq_account, password=tq_password))
        quotes = [api.get_quote(contract) for contract in contracts]
        while True:
            api.wait_update()
            for pos, quote in zip(self.positions, quotes):
                pos.last_mkt_prc = quote.last_price
            self.print_positions()